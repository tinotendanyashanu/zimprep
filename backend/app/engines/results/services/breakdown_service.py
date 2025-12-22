"""Breakdown service for the Results Engine.

Generates topic-level and paper-level performance breakdowns.
Pure aggregation and calculation only - no interpretation or recommendations.
"""

import logging
from typing import List, Dict
from collections import defaultdict

from app.engines.results.schemas.input import PaperInput, SectionBreakdown
from app.engines.results.schemas.output import TopicBreakdown, PaperResult
from app.engines.results.services.aggregation_service import AggregationService

logger = logging.getLogger(__name__)


class BreakdownService:
    """Service for generating performance breakdowns.
    
    Provides topic-level aggregation and paper contribution analysis.
    No interpretation or advice - pure data aggregation only.
    """
    
    @classmethod
    def build_topic_breakdown(
        cls,
        papers: List[PaperInput]
    ) -> List[TopicBreakdown]:
        """Aggregate marks by topic across all papers.
        
        A topic may appear in multiple papers (e.g., "Algebra" in both
        Paper 1 and Paper 2). This method aggregates all occurrences.
        
        Args:
            papers: List of paper inputs with section breakdowns
            
        Returns:
            List of topic breakdowns sorted by topic_code
        """
        # Aggregate topics across papers
        topic_data: Dict[str, Dict] = defaultdict(lambda: {
            "topic_name": "",
            "total_max_marks": 0.0,
            "total_awarded_marks": 0.0,
            "papers_covered": set()
        })
        
        for paper in papers:
            for section in paper.section_breakdown:
                topic_code = section.topic_code
                
                # Update aggregated data
                topic_data[topic_code]["topic_name"] = section.topic_name
                topic_data[topic_code]["total_max_marks"] += section.max_marks
                topic_data[topic_code]["total_awarded_marks"] += section.awarded_marks
                topic_data[topic_code]["papers_covered"].add(paper.paper_code)
        
        # Build TopicBreakdown objects
        breakdowns = []
        for topic_code, data in topic_data.items():
            percentage = AggregationService.calculate_percentage(
                awarded_marks=data["total_awarded_marks"],
                max_marks=data["total_max_marks"]
            )
            
            breakdowns.append(TopicBreakdown(
                topic_code=topic_code,
                topic_name=data["topic_name"],
                total_max_marks=data["total_max_marks"],
                total_awarded_marks=data["total_awarded_marks"],
                percentage=percentage,
                papers_covered=sorted(data["papers_covered"])
            ))
        
        # Sort by topic code for consistency
        breakdowns.sort(key=lambda b: b.topic_code)
        
        logger.info("Built topic breakdown for %d topics", len(breakdowns))
        
        return breakdowns
    
    @classmethod
    def build_paper_breakdown(
        cls,
        papers: List[PaperInput]
    ) -> List[PaperResult]:
        """Summarize each paper's performance and contribution.
        
        Args:
            papers: List of paper inputs
            
        Returns:
            List of paper results sorted by paper_code
        """
        results = []
        
        for paper in papers:
            # Calculate percentage for this paper
            percentage = AggregationService.calculate_percentage(
                awarded_marks=paper.awarded_marks,
                max_marks=paper.max_marks
            )
            
            # Calculate weighted contribution
            weighted_contribution = AggregationService.apply_paper_weighting(
                awarded_marks=paper.awarded_marks,
                max_marks=paper.max_marks,
                weighting=paper.weighting
            )
            
            results.append(PaperResult(
                paper_code=paper.paper_code,
                paper_name=paper.paper_name,
                max_marks=paper.max_marks,
                awarded_marks=paper.awarded_marks,
                percentage=percentage,
                weighting=paper.weighting,
                weighted_contribution=weighted_contribution
            ))
        
        # Sort by paper code for consistency
        results.sort(key=lambda r: r.paper_code)
        
        logger.info("Built paper breakdown for %d papers", len(results))
        
        return results
    
    @classmethod
    def build_complete_breakdown(
        cls,
        papers: List[PaperInput]
    ) -> tuple[List[PaperResult], List[TopicBreakdown]]:
        """Build both paper and topic breakdowns.
        
        Args:
            papers: List of paper inputs
            
        Returns:
            Tuple of (paper_results, topic_breakdowns)
        """
        paper_results = cls.build_paper_breakdown(papers)
        topic_breakdowns = cls.build_topic_breakdown(papers)
        
        logger.info(
            "Built complete breakdown: %d papers, %d topics",
            len(paper_results),
            len(topic_breakdowns)
        )
        
        return paper_results, topic_breakdowns
