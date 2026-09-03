import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.profile.models import UserProfile
from app.applications.models import JobApplication
from app.services.job_service import analyze_job, build_candidate_profile
from app.core.brain.manager import process_message

from app.application_assets.schemas import (
    AssetType,
    CoverLetterStyle,
    MessageChannel,
    MessageTone,
    ClaimEvidenceType,
    EvidenceMetadata,
    TailoredProjectAsset,
    TailoredResumeAsset,
    CoverLetterAsset,
    RecruiterMessageAsset,
    PriorityGap,
    SkillGapAnalysis,
    ApplicationSummaryAsset,
    GeneratedAssetsBundle,
    ApplicationAssetRequest,
    ApplicationAssetResponse,
)
from app.application_assets.prompts import (
    SYSTEM_PROMPT,
    build_asset_generation_prompt,
)
from app.application_assets.validators import (
    extract_json_from_llm_output,
    audit_candidate_grounding,
)

logger = logging.getLogger("friday.application_assets")


class AssetGenerationService:
    """
    Coordinates profile retrieval, job analysis reuse, AI asset synthesis,
    and anti-hallucination fact grounding.
    """

    @staticmethod
    def _resolve_job_inputs(
        request: ApplicationAssetRequest,
        db: Session
    ) -> tuple[str, str, str, Optional[int], Optional[dict]]:
        """
        Resolve job_description, company, role, application_id, and analysis_context
        from raw input, normalized posting, or database record.
        """
        job_desc = request.job_description
        company = request.company
        role = request.role
        app_id = request.application_id
        analysis_context = None

        # 1. From database JobApplication
        if app_id:
            db_app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
            if not db_app:
                raise ValueError(f"Job application with ID {app_id} not found in database.")
            job_desc = job_desc or db_app.job_description
            company = company or db_app.company
            role = role or db_app.role

        # 2. From Phase 2 NormalizedJobPosting
        elif request.normalized_job:
            job_desc = job_desc or request.normalized_job.job_description
            company = company or request.normalized_job.company
            role = role or request.normalized_job.role

        if not job_desc or len(job_desc.strip()) < 30:
            raise ValueError("A valid job description of at least 30 characters is required.")

        company = (company or "Target Company").strip()
        role = (role or "Target Role").strip()

        return job_desc, company, role, app_id, analysis_context

    @classmethod
    def generate_assets(
        cls,
        request: ApplicationAssetRequest,
        db: Session
    ) -> ApplicationAssetResponse:
        """
        Main orchestration pipeline for generating tailored application assets.
        """
        # 1. Resolve inputs
        job_desc, company, role, app_id, _ = cls._resolve_job_inputs(request, db)

        # 2. Retrieve Candidate Master Profile
        profile = db.query(UserProfile).first()
        if not profile:
            raise ValueError("Master candidate profile not found. Create a profile before generating application assets.")

        candidate_profile_text = build_candidate_profile(profile)

        # 3. Reuse existing deterministic job analysis
        analysis = analyze_job(job_desc, db)
        match_score = analysis.get("match_score", 0)
        recommendation = analysis.get("recommendation", "APPLY")

        # 4. Build prompt
        prompt = build_asset_generation_prompt(
            candidate_profile_text=candidate_profile_text,
            job_description_text=job_desc,
            company=company,
            role=role,
            requested_assets=request.assets,
            cover_letter_style=request.cover_letter_style,
            message_channel=request.message_style,
            message_tone=request.message_tone,
            analysis_context=analysis,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        # 5. Execute generation through centralized AI Gateway
        raw_output = process_message(messages, task="asset_generation")
        parsed_data = extract_json_from_llm_output(raw_output)

        # 6. Audit & Ground Claims
        cleaned_data, evidence_list, warnings = audit_candidate_grounding(
            assets_data=parsed_data,
            profile_text=candidate_profile_text,
            target_company=company,
            target_role=role,
        )

        # 7. Construct Assets Bundle
        bundle = cls._build_bundle(
            parsed_data=cleaned_data,
            requested_assets=request.assets,
            analysis=analysis,
            profile=profile,
            company=company,
            role=role,
            cover_letter_style=request.cover_letter_style,
            message_channel=request.message_style,
            message_tone=request.message_tone,
        )

        return ApplicationAssetResponse(
            success=True,
            company=company,
            role=role,
            match_score=match_score,
            recommendation=recommendation,
            assets=bundle,
            evidence_metadata=evidence_list,
            warnings=warnings,
            errors=[]
        )

    @classmethod
    def _build_bundle(
        cls,
        parsed_data: Dict[str, Any],
        requested_assets: List[AssetType],
        analysis: Dict[str, Any],
        profile: UserProfile,
        company: str,
        role: str,
        cover_letter_style: CoverLetterStyle,
        message_channel: MessageChannel,
        message_tone: MessageTone,
    ) -> GeneratedAssetsBundle:
        """
        Assemble the final GeneratedAssetsBundle with fallback defaults if AI output omitted fields.
        """
        bundle = GeneratedAssetsBundle()

        # A. Resume Asset
        if AssetType.RESUME in requested_assets:
            res_data = parsed_data.get("resume") or {}
            projects = []
            for p in res_data.get("relevant_projects", []):
                if isinstance(p, dict):
                    projects.append(TailoredProjectAsset(**p))

            if not projects and profile.projects:
                projects.append(
                    TailoredProjectAsset(
                        name="Featured Portfolio Project",
                        description=str(profile.projects)[:200],
                        bullet_points=["Applied core backend and data engineering principles."],
                        matched_skills=analysis.get("strong_matches", [])[:3]
                    )
                )

            summary = res_data.get("professional_summary") or profile.summary or f"Qualified candidate seeking {role} position at {company}."
            bundle.resume = TailoredResumeAsset(
                professional_summary=summary,
                relevant_skills=res_data.get("relevant_skills") or analysis.get("strong_matches", []),
                relevant_projects=projects,
                experience_bullets=res_data.get("experience_bullets", []),
                achievement_bullets=res_data.get("achievement_bullets", []),
                keywords_matched=res_data.get("keywords_matched") or analysis.get("strong_matches", []),
                keywords_missing=res_data.get("keywords_missing") or analysis.get("missing_skills", []),
                sections_to_prioritize=res_data.get("sections_to_prioritize", ["Technical Skills", "Key Projects"])
            )

        # B. Cover Letter Asset
        if AssetType.COVER_LETTER in requested_assets:
            cl_data = parsed_data.get("cover_letter") or {}
            letter_text = cl_data.get("letter_text") or (
                f"Dear Hiring Team at {company},\n\n"
                f"I am writing to express my enthusiastic interest in the {role} position. "
                f"With demonstrated expertise in {', '.join(analysis.get('strong_matches', ['software engineering'])[:3])}, "
                f"I am confident in my ability to deliver immediate value to your team.\n\n"
                f"Sincerely,\n{profile.first_name or 'Candidate'} {profile.last_name or ''}"
            )
            bundle.cover_letter = CoverLetterAsset(
                letter_text=letter_text,
                style=cover_letter_style,
                key_highlights=cl_data.get("key_highlights") or analysis.get("strong_matches", [])[:3],
                evidence_used=cl_data.get("evidence_used", ["Candidate Profile Summary"])
            )

        # C. Recruiter Message Asset
        if AssetType.RECRUITER_MESSAGE in requested_assets:
            rm_data = parsed_data.get("recruiter_message") or {}
            msg_text = rm_data.get("message_text") or (
                f"Hi! I noticed {company} is hiring for a {role}. "
                f"With my background in {', '.join(analysis.get('strong_matches', ['relevant tech'])[:2])}, "
                f"I would love to connect and share how my experience aligns with your team's goals."
            )
            bundle.recruiter_message = RecruiterMessageAsset(
                message_text=msg_text,
                channel=message_channel,
                tone=message_tone,
                character_count=len(msg_text)
            )

        # D. Skill Gap Analysis Asset
        if AssetType.SKILL_GAP in requested_assets:
            sg_data = parsed_data.get("skill_gap") or {}
            priority_gaps = []
            for g in sg_data.get("priority_gaps", []):
                if isinstance(g, dict):
                    priority_gaps.append(PriorityGap(**g))

            if not priority_gaps and analysis.get("missing_skills"):
                for m_skill in analysis["missing_skills"][:3]:
                    priority_gaps.append(
                        PriorityGap(
                            skill=m_skill,
                            priority="HIGH",
                            reason=f"Identified as a required skill in {role} posting.",
                            evidence_from_jd=f"Referenced in job description for {role}.",
                            suggested_action=f"Review foundational documentation and complete a sample implementation for {m_skill}."
                        )
                    )

            bundle.skill_gap = SkillGapAnalysis(
                matched_skills=sg_data.get("matched_skills") or analysis.get("strong_matches", []),
                partially_matched_skills=sg_data.get("partially_matched_skills") or analysis.get("partial_matches", []),
                missing_skills=sg_data.get("missing_skills") or analysis.get("missing_skills", []),
                transferable_skills=sg_data.get("transferable_skills", []),
                priority_gaps=priority_gaps,
                recommended_learning_actions=sg_data.get("recommended_learning_actions") or analysis.get("learnable_skills", [])
            )

        # E. Application Summary Asset
        if AssetType.APPLICATION_SUMMARY in requested_assets:
            as_data = parsed_data.get("application_summary") or {}
            bundle.application_summary = ApplicationSummaryAsset(
                overall_fit=as_data.get("overall_fit") or ("STRONG_MATCH" if analysis.get("match_score", 0) >= 80 else "MODERATE_MATCH"),
                strongest_selling_points=as_data.get("strongest_selling_points") or [f"Strong alignment in {s}" for s in analysis.get("strong_matches", [])[:2]],
                biggest_concerns=as_data.get("biggest_concerns") or ([f"Missing demonstrated experience in {s}" for s in analysis.get("missing_skills", [])[:2]] if analysis.get("missing_skills") else ["No major skill deficiencies identified."]),
                missing_requirements=as_data.get("missing_requirements") or analysis.get("missing_skills", []),
                recommended_assets=as_data.get("recommended_assets") or ["Tailored Resume", "Personalized Cover Letter"],
                apply_recommendation=analysis.get("recommendation", "APPLY")
            )

        return bundle


# Default singleton instance
default_asset_service = AssetGenerationService()

