"""Reporting & Analytics Engine - Schema Definitions"""

from app.engines.reporting_analytics.schemas.input import ReportingInput
from app.engines.reporting_analytics.schemas.output import ReportingOutput
from app.engines.reporting_analytics.schemas.student_report import StudentReportData
from app.engines.reporting_analytics.schemas.parent_report import ParentReportData
from app.engines.reporting_analytics.schemas.school_report import SchoolReportData

__all__ = [
    "ReportingInput",
    "ReportingOutput",
    "StudentReportData",
    "ParentReportData",
    "SchoolReportData",
]
