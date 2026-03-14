"""
Student routes — profile and dashboard data.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
def get_my_profile():
    """Return the authenticated student's profile."""
    # TODO Week 2: extract user from auth header, fetch from student table
    return {"message": "not implemented"}


@router.get("/me/dashboard")
def get_dashboard():
    """
    Return aggregated dashboard data for the authenticated student:
    recent sessions, weak topics, syllabus coverage summary.
    """
    # TODO Week 2: build dashboard query
    return {"message": "not implemented"}
