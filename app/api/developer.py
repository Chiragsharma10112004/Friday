from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.code_intelligence.schemas import (
    WorkspaceMap,
    SymbolDefinition,
    TestRunReport,
    CodeEditProposal,
)
from app.core.code_intelligence.analyzer import CodeAnalyzer
from app.core.code_intelligence.test_runner import SafeTestRunner
from app.core.editor.agent import EditorAgent
from app.core.editor.editor import extract_function
from app.core.editor.diff import generate_diff
from app.core.code_intelligence.safety_guard import ExecutionGuard

router = APIRouter(prefix="/developer", tags=["Developer & Code Intelligence"])


class RunTestsRequest(BaseModel):
    target: str = Field("tests.run_all_phase_tests", description="Target test suite or module")
    timeout: int = Field(60, ge=5, le=300, description="Execution timeout in seconds")


class CodeEditRequest(BaseModel):
    function_name: str = Field(..., description="Target function name to edit")
    instruction: str = Field(..., description="Natural language editing instruction")
    preview: bool = Field(True, description="If true, returns diff preview without modifying file")


@router.get(
    "/workspace",
    response_model=WorkspaceMap,
    summary="Inspect workspace file tree, line counts, and AST symbol catalog"
)
def inspect_workspace(root: str = Query(".", description="Relative root directory")):
    if not ExecutionGuard.is_path_safe(root):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access outside workspace is restricted.")
    return CodeAnalyzer.analyze_workspace(root=root)


@router.get(
    "/symbols",
    response_model=List[SymbolDefinition],
    summary="Search for functions, classes, and symbols across the codebase"
)
def lookup_symbol(
    name: str = Query(..., description="Symbol name to search for"),
    root: str = Query(".", description="Relative root directory")
):
    if not ExecutionGuard.is_path_safe(root):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access outside workspace is restricted.")
    return CodeAnalyzer.lookup_symbol(symbol_name=name, root=root)


@router.post(
    "/run-tests",
    response_model=TestRunReport,
    summary="Safely execute test suites and return structured pass/fail diagnostics"
)
def run_tests(req: RunTestsRequest):
    return SafeTestRunner.run_tests(test_target=req.target, timeout=req.timeout)


@router.post(
    "/edit",
    summary="Propose and execute controlled AST function edits with unified diff preview"
)
def edit_code(req: CodeEditRequest):
    agent = EditorAgent()
    result = agent.edit(
        function_name=req.function_name,
        instruction=req.instruction,
        preview=req.preview,
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Edit failed"))
    return result
