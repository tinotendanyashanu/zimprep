"""
Reporting & Analytics Engine - Report Builder Service

Assembles role-specific reports from raw data.
"""

from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime

from app.engines.reporting_analytics.schemas.input import UserRole
from app.engines.reporting_analytics.schemas.student_report import (
    StudentReportData,
    ExamSummary,
    QuestionBreakdown,
    TopicPerformance,
    HistoricalDataPoint,
)
from app.engines.reporting_analytics.schemas.parent_report import (
    ParentReportData,
    ParentExamSummary,
    SimplifiedTopicPerformance,
    ProgressIndicator,
)
from app.engines.reporting_analytics.schemas.school_report import (
    SchoolReportData,
    CohortStatistics,
    StudentPerformanceSummary,
    TopicAnalysis,
    ClassTrend,
)
from app.engines.reporting_analytics.rules.aggregation_rules import AggregationRules
from app.engines.reporting_analytics.errors.exceptions import ReportGenerationError


class ReportBuilderService:
    """
    Service for building role-specific reports.
    
    Responsibilities:
    - Assemble student reports with full detail
    - Assemble parent reports with simplified view
    - Assemble school reports with cohort statistics
    - Apply role-appropriate formatting
    """
    
    def __init__(self, trace_id: UUID):
        """
        Initialize the report builder.
        
        Args:
            trace_id: Trace ID for audit logging
        """
        self.trace_id = trace_id
        self.aggregation_rules = AggregationRules(trace_id=trace_id)
    
    def build_student_report(
        self,
        results_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]] | None = None,
    ) -> StudentReportData:
        """
        Build a detailed student report.
        
        Args:
            results_data: Complete results from Results Engine
            historical_data: Optional historical performance data
            
        Returns:
            StudentReportData with full details
            
        Raises:
            ReportGenerationError: If report assembly fails
        """
        try:
            # Extract exam summary
            exam_summary = ExamSummary(
                exam_title=results_data.get("exam_title", "Unknown Exam"),
                subject_name=results_data.get("subject_name", "Unknown Subject"),
                completion_date=results_data.get("completion_date", datetime.now()),
                total_marks=results_data.get("total_marks", 0.0),
                total_available=results_data.get("total_available", 0.0),
                percentage=results_data.get("percentage", 0.0),
                grade=results_data.get("grade", "U"),
            )
            
            # Build question breakdown
            question_breakdown = [
                QuestionBreakdown(
                    question_number=q.get("question_number", 0),
                    question_text=q.get("question_text", "")[:100],  # Truncate
                    marks_awarded=q.get("marks_awarded", 0.0),
                    marks_available=q.get("marks_available", 0.0),
                    percentage=(
                        (q.get("marks_awarded", 0.0) / q.get("marks_available", 1.0)) * 100
                        if q.get("marks_available", 0.0) > 0
                        else 0.0
                    ),
                    topic=q.get("topic", "Unknown"),
                    feedback_summary=q.get("feedback_summary"),
                )
                for q in results_data.get("questions", [])
            ]
            
            # Aggregate topic performance
            topic_data = self.aggregation_rules.aggregate_topic_performance(
                results_data.get("questions", [])
            )
            topic_performance = [
                TopicPerformance(
                    topic_name=t["topic_name"],
                    questions_attempted=t["questions_attempted"],
                    marks_earned=t["marks_earned"],
                    marks_available=t["marks_available"],
                    percentage=t["percentage"],
                    trend=None,  # Will be filled from historical data
                )
                for t in topic_data
            ]
            
            # Process historical data
            historical_performance = []
            if historical_data:
                historical_performance = [
                    HistoricalDataPoint(
                        exam_session_id=h.get("exam_session_id"),
                        exam_date=h.get("exam_date"),
                        percentage=h.get("percentage", 0.0),
                        grade=h.get("grade", "U"),
                    )
                    for h in historical_data
                ]
            
            # Identify strengths and weaknesses
            strengths, weaknesses = self.aggregation_rules.identify_strengths_and_weaknesses(
                topic_data
            )
            
            return StudentReportData(
                exam_summary=exam_summary,
                question_breakdown=question_breakdown,
                topic_performance=topic_performance,
                historical_performance=historical_performance,
                strengths=strengths,
                areas_for_improvement=weaknesses,
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "trace_id": str(self.trace_id),
                },
            )
        
        except Exception as e:
            raise ReportGenerationError(
                message=f"Failed to build student report: {str(e)}",
                trace_id=self.trace_id,
                context={"error": str(e)},
            )
    
    def build_parent_report(
        self,
        results_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]] | None = None,
    ) -> ParentReportData:
        """
        Build a simplified parent/guardian report.
        
        Args:
            results_data: Complete results from Results Engine
            historical_data: Optional historical performance data
            
        Returns:
            ParentReportData with simplified view
            
        Raises:
            ReportGenerationError: If report assembly fails
        """
        try:
            # Simplified exam summary (no raw marks)
            exam_summary = ParentExamSummary(
                exam_title=results_data.get("exam_title", "Unknown Exam"),
                subject_name=results_data.get("subject_name", "Unknown Subject"),
                completion_date=results_data.get("completion_date", datetime.now()),
                percentage=results_data.get("percentage", 0.0),
                grade=results_data.get("grade", "U"),
                performance_summary=self._generate_performance_summary(
                    results_data.get("percentage", 0.0)
                ),
            )
            
            # Simplified topic performance
            topic_data = self.aggregation_rules.aggregate_topic_performance(
                results_data.get("questions", [])
            )
            topic_performance = [
                SimplifiedTopicPerformance(
                    topic_name=t["topic_name"],
                    performance_level=self.aggregation_rules.categorize_performance(
                        t["percentage"]
                    ),
                    percentage=t["percentage"],
                    trend=None,  # Will be filled from historical data
                )
                for t in topic_data
            ]
            
            # Progress indicators
            progress_indicators = []
            if historical_data:
                trend_data = self.aggregation_rules.calculate_historical_trends(
                    historical_data
                )
                progress_indicators.append(
                    ProgressIndicator(
                        period="Overall",
                        trend=trend_data["trend"],
                        average_score=trend_data["average_score"],
                    )
                )
            
            # Identify strengths and weaknesses
            strengths, weaknesses = self.aggregation_rules.identify_strengths_and_weaknesses(
                topic_data
            )
            
            return ParentReportData(
                exam_summary=exam_summary,
                topic_performance=topic_performance,
                progress_indicators=progress_indicators,
                strengths=strengths,
                areas_for_improvement=weaknesses,
                guardian_notes="This report provides a high-level overview of your child's performance. "
                              "For detailed feedback, please consult with the student's teacher.",
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "trace_id": str(self.trace_id),
                },
            )
        
        except Exception as e:
            raise ReportGenerationError(
                message=f"Failed to build parent report: {str(e)}",
                trace_id=self.trace_id,
                context={"error": str(e)},
            )
    
    def build_school_report(
        self,
        cohort_results: List[Dict[str, Any]],
        historical_trends: List[Dict[str, Any]] | None = None,
    ) -> SchoolReportData:
        """
        Build an institutional report with cohort statistics.
        
        Args:
            cohort_results: Results for all students in the cohort
            historical_trends: Optional historical trend data
            
        Returns:
            SchoolReportData with cohort insights
            
        Raises:
            ReportGenerationError: If report assembly fails
        """
        try:
            if not cohort_results:
                raise ReportGenerationError(
                    message="Cannot generate school report: no cohort results provided",
                    trace_id=self.trace_id,
                    context={"cohort_size": 0},
                )
            
            # Use first result for exam metadata
            first_result = cohort_results[0]
            exam_title = first_result.get("exam_title", "Unknown Exam")
            subject_name = first_result.get("subject_name", "Unknown Subject")
            
            # Compute cohort statistics
            stats_data = self.aggregation_rules.compute_cohort_statistics(cohort_results)
            cohort_statistics = CohortStatistics(
                total_students=stats_data["total_students"],
                average_score=stats_data["average_score"],
                median_score=stats_data["median_score"],
                std_deviation=stats_data["std_deviation"],
                highest_score=stats_data["highest_score"],
                lowest_score=stats_data["lowest_score"],
                grade_distribution=stats_data["grade_distribution"],
            )
            
            # Student summaries
            student_summaries = [
                StudentPerformanceSummary(
                    student_id=r.get("student_id"),
                    student_name=r.get("student_name"),
                    percentage=r.get("percentage", 0.0),
                    grade=r.get("grade", "U"),
                    topics_strong=r.get("topics_strong", []),
                    topics_weak=r.get("topics_weak", []),
                )
                for r in cohort_results
            ]
            
            # Topic analysis (aggregate across cohort)
            # NOTE: This would require question-level data for each student
            topic_analysis = []
            
            # Class trends
            class_trends = []
            if historical_trends:
                class_trends = [
                    ClassTrend(
                        period=t.get("period", "Unknown"),
                        average_score=t.get("average_score", 0.0),
                        trend_direction=t.get("trend_direction", "stable"),
                        student_count=t.get("student_count", 0),
                    )
                    for t in historical_trends
                ]
            
            # Generate recommendations
            recommendations = self._generate_school_recommendations(
                cohort_statistics, topic_analysis
            )
            
            return SchoolReportData(
                exam_title=exam_title,
                subject_name=subject_name,
                cohort_statistics=cohort_statistics,
                student_summaries=student_summaries,
                topic_analysis=topic_analysis,
                class_trends=class_trends,
                recommendations=recommendations,
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "trace_id": str(self.trace_id),
                },
            )
        
        except Exception as e:
            raise ReportGenerationError(
                message=f"Failed to build school report: {str(e)}",
                trace_id=self.trace_id,
                context={"error": str(e)},
            )
    
    def _generate_performance_summary(self, percentage: float) -> str:
        """Generate a human-readable performance summary."""
        if percentage >= 75:
            return "Strong performance overall"
        elif percentage >= 60:
            return "Good performance with room for improvement"
        elif percentage >= 50:
            return "Satisfactory performance with targeted improvement needed"
        else:
            return "Additional support recommended"
    
    def _generate_school_recommendations(
        self,
        cohort_stats: CohortStatistics,
        topic_analysis: List[TopicAnalysis],
    ) -> List[str]:
        """Generate data-driven recommendations for schools."""
        recommendations = []
        
        # Based on average performance
        if cohort_stats.average_score < 50:
            recommendations.append(
                "Consider additional teaching resources for this subject"
            )
        
        # Based on standard deviation
        if cohort_stats.std_deviation > 20:
            recommendations.append(
                "High variance in scores suggests differentiated instruction may be beneficial"
            )
        
        # Based on topic analysis
        for topic in topic_analysis:
            if topic.difficulty_level == "challenging":
                recommendations.append(
                    f"Topic '{topic.topic_name}' may require additional instruction time"
                )
        
        return recommendations
