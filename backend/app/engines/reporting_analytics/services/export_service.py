"""
Reporting & Analytics Engine - Export Service

Handles export of reports to multiple formats (JSON, CSV, PDF).
"""

from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
import json
import csv
import io

from app.engines.reporting_analytics.schemas.output import ExportLink
from app.engines.reporting_analytics.errors.exceptions import ExportFailureError


class ExportService:
    """
    Service for exporting reports in various formats.
    
    Responsibilities:
    - Export to JSON (structured data)
    - Export to CSV (tabular data)
    - Generate download links
    - Track export metadata
    """
    
    # Link expiration time
    EXPORT_LINK_EXPIRY_HOURS = 24
    
    def __init__(self, trace_id: UUID, base_url: str = "https://zimprep.example.com"):
        """
        Initialize the export service.
        
        Args:
            trace_id: Trace ID for audit logging
            base_url: Base URL for generating download links
        """
        self.trace_id = trace_id
        self.base_url = base_url
    
    def export_to_json(
        self,
        report_data: Dict[str, Any],
    ) -> str:
        """
        Export report data to JSON format.
        
        Args:
            report_data: The complete report data
            
        Returns:
            JSON string
            
        Raises:
            ExportFailureError: If export fails
        """
        try:
            return json.dumps(
                report_data,
                indent=2,
                default=str,  # Handle non-serializable types
                sort_keys=True,  # Deterministic ordering
            )
        except Exception as e:
            raise ExportFailureError(
                message=f"Failed to export to JSON: {str(e)}",
                trace_id=self.trace_id,
                context={"error": str(e)},
            )
    
    def export_to_csv(
        self,
        report_data: Dict[str, Any],
        report_type: str,
    ) -> str:
        """
        Export report data to CSV format.
        
        Args:
            report_data: The complete report data
            report_type: Type of report (determines CSV structure)
            
        Returns:
            CSV string
            
        Raises:
            ExportFailureError: If export fails
        """
        try:
            output = io.StringIO()
            
            if report_type == "student":
                self._export_student_csv(report_data, output)
            elif report_type == "parent":
                self._export_parent_csv(report_data, output)
            elif report_type == "school":
                self._export_school_csv(report_data, output)
            else:
                raise ExportFailureError(
                    message=f"Unknown report type: {report_type}",
                    trace_id=self.trace_id,
                    context={"report_type": report_type},
                )
            
            return output.getvalue()
        
        except Exception as e:
            raise ExportFailureError(
                message=f"Failed to export to CSV: {str(e)}",
                trace_id=self.trace_id,
                context={"error": str(e)},
            )
    
    def generate_export_links(
        self,
        report_id: UUID,
        formats: List[str],
        file_sizes: Dict[str, int],
    ) -> Dict[str, ExportLink]:
        """
        Generate download links for exported reports.
        
        Args:
            report_id: ID of the report
            formats: List of export formats (e.g., ['pdf', 'csv'])
            file_sizes: Dictionary mapping format to file size in bytes
            
        Returns:
            Dictionary mapping format to ExportLink
        """
        links = {}
        expires_at = datetime.now() + timedelta(hours=self.EXPORT_LINK_EXPIRY_HOURS)
        
        for format in formats:
            url = f"{self.base_url}/exports/{report_id}.{format}"
            file_size = file_sizes.get(format, 0)
            
            links[format] = ExportLink(
                format=format,
                url=url,
                expires_at=expires_at,
                file_size_bytes=file_size,
            )
        
        return links
    
    def _export_student_csv(
        self,
        report_data: Dict[str, Any],
        output: io.StringIO,
    ) -> None:
        """Export student report to CSV."""
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ZimPrep Student Report"])
        writer.writerow([])
        
        # Exam summary
        exam_summary = report_data.get("exam_summary", {})
        writer.writerow(["Exam Summary"])
        writer.writerow(["Exam", exam_summary.get("exam_title", "")])
        writer.writerow(["Subject", exam_summary.get("subject_name", "")])
        writer.writerow(["Grade", exam_summary.get("grade", "")])
        writer.writerow(["Percentage", f"{exam_summary.get('percentage', 0.0):.2f}%"])
        writer.writerow([])
        
        # Question breakdown
        writer.writerow(["Question Breakdown"])
        writer.writerow([
            "Question #",
            "Topic",
            "Marks Awarded",
            "Marks Available",
            "Percentage"
        ])
        
        for question in report_data.get("question_breakdown", []):
            writer.writerow([
                question.get("question_number", ""),
                question.get("topic", ""),
                question.get("marks_awarded", 0.0),
                question.get("marks_available", 0.0),
                f"{question.get('percentage', 0.0):.2f}%",
            ])
        writer.writerow([])
        
        # Topic performance
        writer.writerow(["Topic Performance"])
        writer.writerow(["Topic", "Questions", "Marks Earned", "Marks Available", "Percentage"])
        
        for topic in report_data.get("topic_performance", []):
            writer.writerow([
                topic.get("topic_name", ""),
                topic.get("questions_attempted", 0),
                topic.get("marks_earned", 0.0),
                topic.get("marks_available", 0.0),
                f"{topic.get('percentage', 0.0):.2f}%",
            ])
    
    def _export_parent_csv(
        self,
        report_data: Dict[str, Any],
        output: io.StringIO,
    ) -> None:
        """Export parent report to CSV."""
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ZimPrep Parent/Guardian Report"])
        writer.writerow([])
        
        # Exam summary
        exam_summary = report_data.get("exam_summary", {})
        writer.writerow(["Exam Summary"])
        writer.writerow(["Exam", exam_summary.get("exam_title", "")])
        writer.writerow(["Subject", exam_summary.get("subject_name", "")])
        writer.writerow(["Grade", exam_summary.get("grade", "")])
        writer.writerow(["Percentage", f"{exam_summary.get('percentage', 0.0):.2f}%"])
        writer.writerow([])
        
        # Topic performance (simplified)
        writer.writerow(["Topic Performance"])
        writer.writerow(["Topic", "Performance Level", "Percentage"])
        
        for topic in report_data.get("topic_performance", []):
            writer.writerow([
                topic.get("topic_name", ""),
                topic.get("performance_level", ""),
                f"{topic.get('percentage', 0.0):.2f}%",
            ])
    
    def _export_school_csv(
        self,
        report_data: Dict[str, Any],
        output: io.StringIO,
    ) -> None:
        """Export school report to CSV."""
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ZimPrep School/Institution Report"])
        writer.writerow([])
        
        # Cohort statistics
        cohort_stats = report_data.get("cohort_statistics", {})
        writer.writerow(["Cohort Statistics"])
        writer.writerow(["Total Students", cohort_stats.get("total_students", 0)])
        writer.writerow(["Average Score", f"{cohort_stats.get('average_score', 0.0):.2f}%"])
        writer.writerow(["Median Score", f"{cohort_stats.get('median_score', 0.0):.2f}%"])
        writer.writerow(["Std Deviation", f"{cohort_stats.get('std_deviation', 0.0):.2f}"])
        writer.writerow([])
        
        # Student summaries
        writer.writerow(["Student Performance"])
        writer.writerow(["Student ID", "Student Name", "Percentage", "Grade"])
        
        for student in report_data.get("student_summaries", []):
            writer.writerow([
                student.get("student_id", ""),
                student.get("student_name", ""),
                f"{student.get('percentage', 0.0):.2f}%",
                student.get("grade", ""),
            ])
