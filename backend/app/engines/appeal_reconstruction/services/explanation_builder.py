"""Explanation Builder Service.

This service transforms stored audit traces into human-readable explanations.
It explains HISTORY, it does NOT judge or re-evaluate.

CRITICAL:
- No AI calls
- No inference
- No score recalculation
- Pure transformation of stored data
"""

import logging
from typing import Any
from datetime import datetime

from app.engines.appeal_reconstruction.schemas.output import (
    AppealReconstructionOutput,
    QuestionReconstruction,
    MarkingPointExplanation,
)
from app.engines.appeal_reconstruction.services.audit_loader import ReconstructionContext


logger = logging.getLogger(__name__)


class ExplanationBuilderService:
    """Service for building human-readable explanations from audit data.
    
    RESPONSIBILITIES:
    - Convert stored traces to human-readable explanations
    - Map student answers to marking points
    - Map evidence to awarded marks
    - Explain missing points with reasons
    - Preserve engine names, versions, and confidence scores
    
    CRITICAL CONSTRAINT:
    This service EXPLAINS history, it does NOT judge.
    """
    
    def build(
        self,
        reconstruction_context: ReconstructionContext,
        scope: str = "full",
        question_id: str | None = None
    ) -> AppealReconstructionOutput:
        """Build complete reconstruction from audit context.
        
        Args:
            reconstruction_context: Rehydrated audit data
            scope: "full" for entire paper, "question" for single question
            question_id: Question ID if scope is "question"
            
        Returns:
            AppealReconstructionOutput with human-readable explanations
        """
        logger.info(
            f"Building reconstruction for trace_id: {reconstruction_context.trace_id}",
            extra={
                "trace_id": reconstruction_context.trace_id,
                "scope": scope,
                "question_id": question_id
            }
        )
        
        # Build question reconstructions
        questions = self._build_question_reconstructions(
            reconstruction_context,
            scope,
            question_id
        )
        
        # Extract candidate info from audit record
        candidate_number = self._extract_candidate_number(
            reconstruction_context.audit_record
        )
        subject = self._extract_subject(reconstruction_context.audit_record)
        paper_code = self._extract_paper_code(reconstruction_context.audit_record)
        
        # Build final output
        output = AppealReconstructionOutput(
            trace_id=reconstruction_context.trace_id,
            candidate_number=candidate_number,
            subject=subject,
            paper_code=paper_code,
            final_score=reconstruction_context.final_score,
            grade=reconstruction_context.final_grade,
            reconstruction_timestamp=datetime.utcnow(),
            ai_used=reconstruction_context.was_ai_used(),
            re_executed=False,  # ALWAYS FALSE - this is legally critical
            audit_reference=reconstruction_context.audit_record_id,
            questions=questions
        )
        
        logger.info(
            f"Reconstruction complete for trace_id: {reconstruction_context.trace_id}",
            extra={
                "trace_id": reconstruction_context.trace_id,
                "questions_reconstructed": len(questions),
                "final_score": output.final_score,
                "grade": output.grade
            }
        )
        
        return output
    
    def _build_question_reconstructions(
        self,
        context: ReconstructionContext,
        scope: str,
        question_id: str | None
    ) -> list[QuestionReconstruction]:
        """Build reconstructions for questions based on scope.
        
        Args:
            context: Reconstruction context with audit data
            scope: "full" or "question"
            question_id: Specific question ID if scope is "question"
            
        Returns:
            List of QuestionReconstruction objects
        """
        reconstructions = []
        
        # Get marking decisions
        marking_decisions = context.marking_decisions
        
        # Get raw answers indexed by question_id
        answers_by_question = {
            answer.get("question_id"): answer
            for answer in context.raw_answers
        }
        
        for decision in marking_decisions:
            q_id = decision.get("question_id")
            
            # Filter by question_id if scope is "question"
            if scope == "question" and question_id and q_id != question_id:
                continue
            
            if not q_id:
                continue
            
            # Get raw answer
            answer_data = answers_by_question.get(q_id, {})
            student_answer = answer_data.get("answer_text", "[Answer not available in audit record]")
            
            # Build marking points
            marking_points = self._build_marking_points(decision, context.ai_evidence)
            
            # Create reconstruction
            reconstruction = QuestionReconstruction(
                question_id=q_id,
                student_answer=student_answer,
                marking_points=marking_points,
                marks_awarded=decision.get("marks_awarded", 0),
                marks_available=decision.get("marks_available", 0),
                decided_by_engine=decision.get("engine_name", "reasoning_marking"),
                engine_version=decision.get("engine_version", "unknown"),
                confidence=decision.get("confidence", 0.0)
            )
            
            reconstructions.append(reconstruction)
        
        # If no marking decisions found but we have raw answers,
        # create placeholder reconstructions
        if not reconstructions and context.raw_answers:
            for answer in context.raw_answers:
                q_id = answer.get("question_id")
                if scope == "question" and question_id and q_id != question_id:
                    continue
                
                reconstruction = QuestionReconstruction(
                    question_id=q_id,
                    student_answer=answer.get("answer_text", ""),
                    marking_points=[],
                    marks_awarded=0,
                    marks_available=0,
                    decided_by_engine="unknown",
                    engine_version="unknown",
                    confidence=0.0
                )
                reconstructions.append(reconstruction)
        
        return reconstructions
    
    def _build_marking_points(
        self,
        decision: dict[str, Any],
        ai_evidence: list[dict[str, Any]]
    ) -> list[MarkingPointExplanation]:
        """Build marking point explanations from decision and evidence.
        
        Args:
            decision: Marking decision dictionary
            ai_evidence: All AI evidence records
            
        Returns:
            List of MarkingPointExplanation objects
        """
        marking_points = []
        
        # Extract reasoning trace if available
        reasoning_trace = decision.get("reasoning_trace", {})
        evidence_chunks = decision.get("evidence_chunks", [])
        
        # If we have structured reasoning trace, use it
        if isinstance(reasoning_trace, dict):
            points_awarded = reasoning_trace.get("points_awarded", [])
            points_not_awarded = reasoning_trace.get("points_not_awarded", [])
            
            for point in points_awarded:
                marking_points.append(
                    MarkingPointExplanation(
                        point=point.get("description", "Marking criterion"),
                        evidence_source=point.get("evidence_source", "Marking Scheme"),
                        awarded=True,
                        reason=point.get("reason", "Matched expected criteria")
                    )
                )
            
            for point in points_not_awarded:
                marking_points.append(
                    MarkingPointExplanation(
                        point=point.get("description", "Marking criterion"),
                        evidence_source=point.get("evidence_source", "Marking Scheme"),
                        awarded=False,
                        reason=point.get("reason", "Did not match expected criteria")
                    )
                )
        
        # If we have evidence chunks, create points from those
        elif evidence_chunks:
            for chunk in evidence_chunks:
                marking_points.append(
                    MarkingPointExplanation(
                        point=chunk.get("criterion", "Evidence-based marking"),
                        evidence_source=chunk.get("source", "Retrieved Evidence"),
                        awarded=chunk.get("matched", True),
                        reason=chunk.get("explanation", None)
                    )
                )
        
        # If no structured data, create a single summary point
        if not marking_points:
            marks_awarded = decision.get("marks_awarded", 0)
            marks_available = decision.get("marks_available", 0)
            
            marking_points.append(
                MarkingPointExplanation(
                    point=f"Overall assessment: {marks_awarded}/{marks_available} marks",
                    evidence_source="Audit Record",
                    awarded=marks_awarded > 0,
                    reason="Detailed marking point breakdown not available in audit record"
                )
            )
        
        return marking_points
    
    def _extract_candidate_number(self, audit_record: dict[str, Any]) -> str:
        """Extract candidate number from audit record."""
        # Try multiple possible field names
        candidate_fields = [
            "candidate_number",
            "student_id",
            "student_candidate_number"
        ]
        
        for field in candidate_fields:
            value = audit_record.get(field)
            if value:
                return str(value)
        
        return "Unknown"
    
    def _extract_subject(self, audit_record: dict[str, Any]) -> str:
        """Extract subject from audit record."""
        # Try to get from exam metadata or request metadata
        exam_id = audit_record.get("exam_id", "")
        request_metadata = audit_record.get("request_metadata", {})
        
        # Check request metadata first
        if isinstance(request_metadata, dict):
            subject = request_metadata.get("subject")
            if subject:
                return str(subject)
        
        # Parse from exam_id if possible (common format: SUBJ_YEAR_PAPER)
        if exam_id and "_" in exam_id:
            parts = exam_id.split("_")
            if parts:
                return parts[0]
        
        return "Unknown Subject"
    
    def _extract_paper_code(self, audit_record: dict[str, Any]) -> str:
        """Extract paper code from audit record."""
        request_metadata = audit_record.get("request_metadata", {})
        
        if isinstance(request_metadata, dict):
            paper_code = request_metadata.get("paper_code")
            if paper_code:
                return str(paper_code)
        
        # Try exam_id
        exam_id = audit_record.get("exam_id", "")
        if exam_id and "_" in exam_id:
            parts = exam_id.split("_")
            if len(parts) >= 2:
                return parts[-1]
        
        return "Unknown"
