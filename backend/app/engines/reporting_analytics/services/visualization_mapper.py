"""
Reporting & Analytics Engine - Visualization Mapper Service

Maps report data to visualization-ready formats for frontend consumption.
"""

from typing import Dict, Any, List
from uuid import UUID

from app.engines.reporting_analytics.schemas.output import VisualSection


class VisualizationMapperService:
    """
    Service for mapping data to visualization formats.
    
    Responsibilities:
    - Transform data into chart-ready formats
    - Generate visualization metadata
    - Structure data for frontend rendering
    - Support multiple chart types (bar, line, pie, radar)
    """
    
    def __init__(self, trace_id: UUID):
        """
        Initialize the visualization mapper.
        
        Args:
            trace_id: Trace ID for audit logging
        """
        self.trace_id = trace_id
    
    def map_to_chart_data(
        self,
        data: List[Dict[str, Any]],
        chart_type: str,
        x_field: str,
        y_field: str,
    ) -> Dict[str, Any]:
        """
        Map data to a specific chart format.
        
        Args:
            data: List of data points
            chart_type: Type of chart (bar, line, pie, radar)
            x_field: Field to use for x-axis
            y_field: Field to use for y-axis
            
        Returns:
            Chart-ready data structure
        """
        chart_data = {
            "type": chart_type,
            "labels": [d.get(x_field, "") for d in data],
            "datasets": [
                {
                    "label": y_field,
                    "data": [d.get(y_field, 0) for d in data],
                }
            ],
        }
        
        return chart_data
    
    def generate_visual_sections(
        self,
        report_data: Dict[str, Any],
        role: str,
    ) -> List[VisualSection]:
        """
        Generate visualization sections for a report.
        
        Args:
            report_data: The complete report data
            role: User role (student, parent, school_admin)
            
        Returns:
            List of VisualSection objects
        """
        sections = []
        
        # Topic performance bar chart
        if "topic_performance" in report_data:
            topic_data = report_data["topic_performance"]
            sections.append(
                VisualSection(
                    section_id="topic_performance_chart",
                    section_title="Performance by Topic",
                    visualization_type="bar_chart",
                    data=self.map_to_chart_data(
                        data=topic_data,
                        chart_type="bar",
                        x_field="topic_name",
                        y_field="percentage",
                    ),
                    metadata={"color_scheme": "performance"},
                )
            )
        
        # Historical trend line chart
        if "historical_performance" in report_data:
            historical_data = report_data["historical_performance"]
            if historical_data:
                sections.append(
                    VisualSection(
                        section_id="historical_trend_chart",
                        section_title="Performance Over Time",
                        visualization_type="line_chart",
                        data=self._format_historical_chart(historical_data),
                        metadata={"show_trend_line": True},
                    )
                )
        
        # Grade distribution (for school reports)
        if role == "school_admin" and "cohort_statistics" in report_data:
            cohort_stats = report_data["cohort_statistics"]
            if "grade_distribution" in cohort_stats:
                sections.append(
                    VisualSection(
                        section_id="grade_distribution_chart",
                        section_title="Grade Distribution",
                        visualization_type="pie_chart",
                        data=self._format_grade_distribution(
                            cohort_stats["grade_distribution"]
                        ),
                        metadata={"show_percentages": True},
                    )
                )
        
        return sections
    
    def format_for_frontend(
        self,
        report_data: Dict[str, Any],
        visual_sections: List[VisualSection],
    ) -> Dict[str, Any]:
        """
        Structure report data for optimal frontend consumption.
        
        Args:
            report_data: The complete report data
            visual_sections: List of visualization sections
            
        Returns:
            Frontend-optimized data structure
        """
        return {
            "summary": self._extract_summary(report_data),
            "details": report_data,
            "visualizations": [
                {
                    "id": section.section_id,
                    "title": section.section_title,
                    "type": section.visualization_type,
                    "data": section.data,
                    "metadata": section.metadata,
                }
                for section in visual_sections
            ],
        }
    
    def _format_historical_chart(
        self,
        historical_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Format historical data for line chart."""
        return {
            "type": "line",
            "labels": [
                d.get("exam_date", "").strftime("%Y-%m-%d")
                if hasattr(d.get("exam_date", ""), "strftime")
                else str(d.get("exam_date", ""))
                for d in historical_data
            ],
            "datasets": [
                {
                    "label": "Percentage Score",
                    "data": [d.get("percentage", 0) for d in historical_data],
                    "borderColor": "rgb(59, 130, 246)",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                }
            ],
        }
    
    def _format_grade_distribution(
        self,
        grade_distribution: Dict[str, int],
    ) -> Dict[str, Any]:
        """Format grade distribution for pie chart."""
        return {
            "type": "pie",
            "labels": list(grade_distribution.keys()),
            "datasets": [
                {
                    "label": "Students",
                    "data": list(grade_distribution.values()),
                    "backgroundColor": [
                        "rgb(34, 197, 94)",   # A - green
                        "rgb(59, 130, 246)",  # B - blue
                        "rgb(251, 191, 36)",  # C - yellow
                        "rgb(249, 115, 22)",  # D - orange
                        "rgb(239, 68, 68)",   # F/U - red
                    ],
                }
            ],
        }
    
    def _extract_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key summary metrics from report data."""
        summary = {}
        
        # Exam summary
        if "exam_summary" in report_data:
            exam_summary = report_data["exam_summary"]
            summary["exam_title"] = exam_summary.get("exam_title", "")
            summary["subject_name"] = exam_summary.get("subject_name", "")
            summary["grade"] = exam_summary.get("grade", "")
            summary["percentage"] = exam_summary.get("percentage", 0.0)
        
        # Topic count
        if "topic_performance" in report_data:
            summary["topic_count"] = len(report_data["topic_performance"])
        
        # Strengths and weaknesses count
        if "strengths" in report_data:
            summary["strengths_count"] = len(report_data["strengths"])
        if "areas_for_improvement" in report_data:
            summary["weaknesses_count"] = len(report_data["areas_for_improvement"])
        
        return summary
