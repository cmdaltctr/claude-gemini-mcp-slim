#!/usr/bin/env python3
"""
Agentic Collaboration Protocol (ACP) Models

This module defines Pydantic models for structured responses from LLMs,
implementing the Agentic Collaboration Protocol as outlined in CLAUDE.md.

These models enable the evolution from plain text responses to structured
data exchange, supporting the intelligent orchestration capabilities of
the claude-gemini-mcp system.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator


class PatchType(str, Enum):
    """Types of code patches that can be generated."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    REFACTOR = "refactor"
    FIX = "fix"
    ENHANCE = "enhance"


class Confidence(str, Enum):
    """Confidence levels for AI-generated content."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class CodePatchStep(BaseModel):
    """
    Represents a single atomic code modification step.

    This model captures the granular details of each code change,
    enabling precise tracking and validation of modifications.
    """

    description: str = Field(
        description="Clear description of what this step accomplishes"
    )

    patch_type: PatchType = Field(
        description="The type of modification being performed"
    )

    diff: str = Field(
        description="Unified diff format showing the exact changes"
    )

    line_range: Optional[tuple] = Field(
        default=None,
        description="Tuple of (start_line, end_line) for the affected range"
    )

    confidence: Confidence = Field(
        default=Confidence.MEDIUM,
        description="AI confidence level in this specific change"
    )

    reasoning: Optional[str] = Field(
        default=None,
        description="Detailed reasoning behind this modification"
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="List of other steps this one depends on"
    )

    @validator('diff')
    def validate_diff_format(cls, v):
        """Ensure diff follows unified diff format conventions."""
        if not v.strip():
            raise ValueError("Diff cannot be empty")
        return v


class TestStrategy(BaseModel):
    """
    Defines testing approach for code changes.

    This model ensures that generated code includes proper testing
    considerations, maintaining code quality standards.
    """

    test_type: str = Field(
        description="Type of testing required (unit, integration, e2e, etc.)"
    )

    test_files: List[str] = Field(
        default_factory=list,
        description="List of test files that should be created or modified"
    )

    test_commands: List[str] = Field(
        default_factory=list,
        description="Commands to run for testing the changes"
    )

    assertions: List[str] = Field(
        default_factory=list,
        description="Key assertions that tests should verify"
    )


class SecurityConsideration(BaseModel):
    """
    Security aspects of code changes.

    This model ensures security implications are explicitly considered
    in all code modifications, following defensive coding practices.
    """

    risk_level: str = Field(
        description="Security risk level (low, medium, high, critical)"
    )

    considerations: List[str] = Field(
        description="List of security considerations addressed"
    )

    mitigations: List[str] = Field(
        default_factory=list,
        description="Security mitigations implemented"
    )


class AgenticCodePatch(BaseModel):
    """
    Comprehensive model for AI-generated code patches.

    This is the primary model for structured code generation responses,
    implementing the Agentic Collaboration Protocol. It provides detailed,
    validated structure for code modifications with full traceability.

    Usage:
        This model should be used as the response_model parameter when
        calling instructor-enhanced LLM clients for code generation tasks.
    """

    # Core patch information
    filename: str = Field(
        description="Relative path to the file being modified"
    )

    patch_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this patch"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this patch was generated"
    )

    # Patch content
    steps: List[CodePatchStep] = Field(
        description="Ordered list of atomic modification steps"
    )

    summary: str = Field(
        description="High-level summary of all changes in this patch"
    )

    # Context and reasoning
    motivation: str = Field(
        description="Why these changes are necessary"
    )

    approach: str = Field(
        description="High-level approach taken for implementation"
    )

    # Quality assurance
    test_strategy: Optional[TestStrategy] = Field(
        default=None,
        description="Testing approach for these changes"
    )

    security: Optional[SecurityConsideration] = Field(
        default=None,
        description="Security implications and mitigations"
    )

    # Metadata
    confidence: Confidence = Field(
        default=Confidence.MEDIUM,
        description="Overall confidence in this patch"
    )

    estimated_effort: Optional[str] = Field(
        default=None,
        description="Estimated implementation time/effort"
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="External dependencies or prerequisites"
    )

    rollback_plan: Optional[str] = Field(
        default=None,
        description="How to rollback these changes if needed"
    )

    @validator('steps')
    def validate_steps_not_empty(cls, v):
        """Ensure at least one step is provided."""
        if not v:
            raise ValueError("At least one patch step is required")
        return v

    @validator('filename')
    def validate_filename_format(cls, v):
        """Ensure filename is properly formatted."""
        if not v.strip():
            raise ValueError("Filename cannot be empty")
        # Could add more validation (no absolute paths, valid extensions, etc.)
        return v.strip()


class CodeAnalysisResult(BaseModel):
    """
    Structured result from code analysis operations.

    This model provides comprehensive feedback on code quality,
    issues, and recommendations for improvement.
    """

    filename: str = Field(
        description="File that was analyzed"
    )

    analysis_type: str = Field(
        description="Type of analysis performed (security, performance, etc.)"
    )

    issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of issues found during analysis"
    )

    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended improvements"
    )

    metrics: Dict[str, Union[int, float, str]] = Field(
        default_factory=dict,
        description="Quantitative metrics from analysis"
    )

    overall_score: Optional[float] = Field(
        default=None,
        description="Overall quality score (0-100)"
    )


class AgenticResponse(BaseModel):
    """
    Generic structured response wrapper for agentic operations.

    This model provides a consistent structure for all AI responses,
    enabling proper error handling and result processing.
    """

    success: bool = Field(
        description="Whether the operation completed successfully"
    )

    result: Optional[Union[AgenticCodePatch, CodeAnalysisResult, Dict[str, Any]]] = Field(
        default=None,
        description="The main result of the operation"
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error message if operation failed"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings during operation"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the operation"
    )

    processing_time: Optional[float] = Field(
        default=None,
        description="Time taken to process the request (seconds)"
    )
