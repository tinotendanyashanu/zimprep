"""Feedback Generator Service.

Generates examiner-style feedback following ZIMSEC tone and standards.
"""

from typing import List
import logging

from app.engines.ai.reasoning_marking.schemas import (
    AwardedPoint,
    MissingPoint,
    AnswerType,
)

logger = logging.getLogger(__name__)


class FeedbackGenerator:
    """Service for generating professional, examiner-style feedback.
    
    Feedback must be:
    - Professional and constructive
    - Aligned to ZIMSEC tone
    - Reference syllabus expectations
    - Directly tied to rubric points
    - No speculation or guessing
    """
    
    @staticmethod
    def generate_feedback(
        awarded_points: List[AwardedPoint],
        missing_points: List[MissingPoint],
        awarded_marks: float,
        max_marks: int,
        answer_type: AnswerType,
        subject: str,
        trace_id: str
    ) -> str:
        """Generate comprehensive feedback.
        
        Args:
            awarded_points: Points successfully awarded
            missing_points: Points not awarded
            awarded_marks: Total marks awarded
            max_marks: Maximum marks
            answer_type: Type of answer
            subject: Subject name
            trace_id: Trace ID
            
        Returns:
            Examiner-style feedback text
        """
        feedback_sections = []
        
        # 1. Overall performance summary
        feedback_sections.append(
            FeedbackGenerator._generate_summary(
                awarded_marks,
                max_marks
            )
        )
        
        # 2. Strengths (awarded points)
        if awarded_points:
            feedback_sections.append(
                FeedbackGenerator._generate_strengths_section(
                    awarded_points
                )
            )
        
        # 3. Areas for improvement (missing points)
        if missing_points:
            feedback_sections.append(
                FeedbackGenerator._generate_improvements_section(
                    missing_points,
                    subject,
                    answer_type
                )
            )
        
        # 4. Next steps
        feedback_sections.append(
            FeedbackGenerator._generate_next_steps(
                missing_points,
                awarded_marks,
                max_marks
            )
        )
        
        feedback = "\n\n".join(feedback_sections)
        
        logger.info(
            "Feedback generated",
            extra={
                "trace_id": trace_id,
                "feedback_length": len(feedback),
                "sections": len(feedback_sections)
            }
        )
        
        return feedback
    
    @staticmethod
    def _generate_summary(awarded_marks: float, max_marks: int) -> str:
        """Generate overall performance summary."""
        percentage = (awarded_marks / max_marks * 100) if max_marks > 0 else 0
        
        return (
            f"You scored {awarded_marks:.1f} out of {max_marks} marks ({percentage:.0f}%)."
        )
    
    @staticmethod
    def _generate_strengths_section(awarded_points: List[AwardedPoint]) -> str:
        """Generate section highlighting what was done well."""
        lines = ["**Demonstrated Understanding:**"]
        
        for point in awarded_points:
            lines.append(f"- {point.description} ({point.marks} marks)")
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_improvements_section(
        missing_points: List[MissingPoint],
        subject: str,
        answer_type: AnswerType
    ) -> str:
        """Generate section on areas for improvement."""
        lines = ["**Areas for Development:**"]
        
        if not missing_points:
            lines.append("None - all rubric criteria met.")
            return "\n".join(lines)
        
        for point in missing_points:
            reason_text = f" ({point.reason})" if point.reason else ""
            lines.append(
                f"- {point.description}{reason_text} "
                f"({point.marks} marks available)"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_next_steps(
        missing_points: List[MissingPoint],
        awarded_marks: float,
        max_marks: int
    ) -> str:
        """Generate actionable next steps."""
        if not missing_points:
            return (
                "**Next Steps:** Continue practicing similar questions to maintain "
                "this level of understanding. Consider more challenging questions "
                "to deepen your mastery."
            )
        
        percentage = (awarded_marks / max_marks * 100) if max_marks > 0 else 0
        
        if percentage < 40:
            return (
                "**Next Steps:** Review the fundamental concepts for this topic. "
                "Focus on understanding key definitions and principles before "
                "attempting practice questions."
            )
        elif percentage < 70:
            return (
                "**Next Steps:** You have a solid foundation. Review the marking "
                "scheme for this question type and practice similar questions, "
                "paying particular attention to the areas identified above."
            )
        else:
            return (
                "**Next Steps:** Strong performance overall. Focus on the specific "
                "points identified above to achieve full marks on similar questions."
            )
    
    @staticmethod
    def generate_appeal_support_text(
        awarded_points: List[AwardedPoint],
        trace_id: str
    ) -> str:
        """Generate text explaining evidence basis for appeals.
        
        This is used if a student wants to understand WHY they got specific marks.
        
        Args:
            awarded_points: Points awarded with evidence citations
            trace_id: Trace ID
            
        Returns:
            Detailed evidence citations
        """
        if not awarded_points:
            return "No marks were awarded for this question."
        
        lines = ["**Evidence Basis for Awarded Marks:**\n"]
        
        for point in awarded_points:
            lines.append(f"**{point.description}** ({point.marks} marks)")
            lines.append(f"- Evidence ID: {point.evidence_id}")
            if point.evidence_excerpt:
                lines.append(f"- Supporting excerpt: \"{point.evidence_excerpt}\"")
            lines.append("")
        
        return "\n".join(lines)
