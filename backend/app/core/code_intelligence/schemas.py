from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SymbolDefinition(BaseModel):
    name: str
    symbol_type: str  # function, class, import
    file: str
    line: int
    docstring: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)


class FileInspection(BaseModel):
    path: str
    name: str
    size_bytes: int
    lines_count: int
    symbols_count: int
    functions: List[str] = Field(default_factory=list)
    classes: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)


class WorkspaceMap(BaseModel):
    root_path: str
    total_files: int
    total_lines: int
    files: List[FileInspection] = Field(default_factory=list)
    symbol_index: Dict[str, List[str]] = Field(default_factory=dict)


class TestCaseResult(BaseModel):
    name: str
    status: str  # PASSED, FAILED, ERROR, SKIPPED
    duration_sec: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


class TestRunReport(BaseModel):
    total_run: int
    passed: int
    failed: int
    errors: int
    duration_sec: float
    success: bool
    test_cases: List[TestCaseResult] = Field(default_factory=list)
    raw_output: str = ""


class CodeEditProposal(BaseModel):
    target_file: str
    target_symbol: Optional[str] = None
    instruction: str
    original_code: str
    updated_code: str
    diff: str
    valid_ast: bool = True
    requires_approval: bool = True
