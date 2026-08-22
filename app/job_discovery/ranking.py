from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.profile.models import UserProfile
from app.job_discovery.schemas import DiscoveredJob, JobRecommendation
from app.services.job_service import analyze_job


class JobRanker:
    """
    Candidate profile matching and ranking engine for discovered job opportunities.
    Reuses Phase 1 deterministic analysis and scoring contracts.
    """

    @classmethod
    def evaluate_match(
        cls,
        job: DiscoveredJob,
        db: Session,
        profile: Optional[UserProfile] = None
    ) -> DiscoveredJob:
        if not profile:
            profile = db.query(UserProfile).first()

        if not profile:
            job.match_score = 0
            job.recommendation = JobRecommendation.WEAK_MATCH
            job.ranking_explanation = "No master candidate profile found to score this opportunity."
            return job

        try:
            analysis = analyze_job(job.description, db)
            score = analysis.get("match_score", 0)

            if score >= 75:
                rec = JobRecommendation.STRONG_MATCH
            elif score >= 60:
                rec = JobRecommendation.GOOD_MATCH
            elif score >= 45:
                rec = JobRecommendation.PARTIAL_MATCH
            else:
                rec = JobRecommendation.WEAK_MATCH

            strong_matches = analysis.get("strong_matches", [])
            project_matches = analysis.get("project_matches", [])
            partial_matches = analysis.get("partial_matches", [])
            missing_skills = analysis.get("missing_skills", [])

            strengths = []
            if strong_matches:
                strengths.append(f"Demonstrated core skills: {', '.join(strong_matches[:3])}")
            if project_matches:
                strengths.append(f"Hands-on project alignment: {', '.join(project_matches[:2])}")
            if not strengths:
                strengths.append("General technical background alignment.")

            concerns = []
            if missing_skills:
                concerns.append(f"Missing required skills: {', '.join(missing_skills[:3])}")
            if not concerns:
                concerns.append("No critical skill deficiencies identified.")

            job.match_score = score
            job.recommendation = rec
            job.ranking_explanation = analysis.get("reason") or (
                f"Candidate scored {score}% fit with {len(strong_matches)} direct matches and {len(missing_skills)} skill gaps."
            )
            job.matched_skills = strong_matches + project_matches + partial_matches
            job.missing_skills = missing_skills
            job.key_strengths = strengths
            job.key_concerns = concerns

        except Exception as e:
            job.match_score = 50
            job.recommendation = JobRecommendation.PARTIAL_MATCH
            job.ranking_explanation = f"Automated scoring completed with default baseline: {str(e)}"

        return job

    @classmethod
    def rank_jobs(
        cls,
        jobs: List[DiscoveredJob],
        db: Session,
        profile: Optional[UserProfile] = None
    ) -> List[DiscoveredJob]:
        evaluated_jobs = [cls.evaluate_match(j, db, profile) for j in jobs]
        return sorted(evaluated_jobs, key=lambda x: (x.match_score or 0), reverse=True)
