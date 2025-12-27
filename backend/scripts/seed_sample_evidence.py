"""
Sample Evidence Seeding Script for ZimPrep Vector Store

Purpose: Seed marking_evidence collection with authoritative ZIMSEC sample data
         to enable real REG (Retrieve-Evidence-Generate) marking.

Usage:
    python scripts/seed_sample_evidence.py

Requirements:
    - MongoDB running on localhost:27017
    - sentence-transformers installed
    - Vector store initialized (run init_vector_store.js first)
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Import embedding service
from app.engines.ai.embedding.services.embedding_service import EmbeddingService

# MongoDB configuration
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "zimprep"
COLLECTION_NAME = "marking_evidence"

# Embedding configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_VERSION = "1.0.0"


def create_sample_evidence() -> List[Dict[str, Any]]:
    """Create sample ZIMSEC evidence data across 3 subjects.
    
    Returns:
        List of evidence documents ready for embedding
    """
    evidence = []
    
    # ========== MATHEMATICS O-LEVEL (Paper 4008) ==========
    
    # Question 1: Algebra - Quadratic Equations
    evidence.extend([
        {
            "source_type": "marking_scheme",
            "content": "Award 1 mark for correctly rearranging the equation to standard form ax² + bx + c = 0. Award 1 mark for identifying a=1, b=5, c=-14. Award 1 mark for substituting into the quadratic formula. Award 1 mark for each correct root (x=-7 or x=2).",
            "source_reference": "MS_2024_MATH_4008_Q1a",
            "subject": "Mathematics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
            "question_id": "Q1a",
            "syllabus_ref": "3.2.1 Quadratic Equations",
            "mark_mapping": 4,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Algebra",
                "difficulty": "Medium",
                "max_marks": 4
            }
        },
        {
            "source_type": "examiner_report",
            "content": "Most candidates correctly identified the quadratic formula but made errors in substitution. Common mistakes: incorrect signs when substituting b=-5, arithmetic errors in the discriminant calculation. Strong candidates showed all working clearly.",
            "source_reference": "ER_2024_MATH_4008_Q1a",
            "subject": "Mathematics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
            "question_id": "Q1a",
            "syllabus_ref": "3.2.1 Quadratic Equations",
            "mark_mapping": None,
            "source_year": 2024,
            "confidence_weight": 0.9,
            "metadata": {
                "topic": "Algebra",
                "common_errors": ["sign errors", "discriminant calculation"]
            }
        },
        {
            "source_type": "model_answer",
            "content": "x² + 5x - 14 = 0. Using quadratic formula: x = (-b ± √(b²-4ac)) / 2a. a=1, b=5, c=-14. x = (-5 ± √(25+56)) / 2 = (-5 ± √81) / 2 = (-5 ± 9) / 2. Therefore x = 2 or x = -7.",
            "source_reference": "MA_2024_MATH_4008_Q1a",
            "subject": "Mathematics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
            "question_id": "Q1a",
            "syllabus_ref": "3.2.1 Quadratic Equations",
            "mark_mapping": 4,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Algebra",
                "solution_method": "quadratic_formula"
            }
        }
    ])
    
    # Question 2: Geometry - Circle Theorems
    evidence.extend([
        {
            "source_type": "marking_scheme",
            "content": "Award 1 mark for identifying the angle subtended at the center is twice the angle at the circumference. Award 1 mark for correct calculation: angle AOB = 2 × 35° = 70°. Award 1 mark for stating the reason (circle theorem).",
            "source_reference": "MS_2024_MATH_4008_Q2b",
            "subject": "Mathematics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
            "question_id": "Q2b",
            "syllabus_ref": "4.1.3 Circle Theorems",
            "mark_mapping": 3,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Geometry",
                "difficulty": "Easy",
                "max_marks": 3
            }
        },
        {
            "source_type": "examiner_report",
            "content": "This question was well attempted. Most candidates correctly applied the circle theorem. A small number incorrectly divided by 2 instead of multiplying. Candidates must state the theorem used to receive full marks.",
            "source_reference": "ER_2024_MATH_4008_Q2b",
            "subject": "Mathematics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
            "question_id": "Q2b",
            "syllabus_ref": "4.1.3 Circle Theorems",
            "mark_mapping": None,
            "source_year": 2024,
            "confidence_weight": 0.9,
            "metadata": {
                "topic": "Geometry",
                "common_errors": ["division instead of multiplication", "no theorem stated"]
            }
        }
    ])
    
    # Question 3: Trigonometry
    evidence.extend([
        {
            "source_type": "marking_scheme",
            "content": "Award 1 mark for identifying the correct trigonometric ratio (sin θ = opposite/hypotenuse). Award 1 mark for correct substitution: sin 30° = h/12. Award 1 mark for rearrangement: h = 12 × sin 30°. Award 1 mark for correct answer: h = 6 m.",
            "source_reference": "MS_2024_MATH_4008_Q3c",
            "subject": "Mathematics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
            "question_id": "Q3c",
            "syllabus_ref": "5.2.1 Trigonometric Ratios",
            "mark_mapping": 4,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Trigonometry",
                "difficulty": "Medium",
                "max_marks": 4
            }
        },
        {
            "source_type": "syllabus_excerpt",
            "content": "Candidates should be able to: calculate unknown sides and angles in right-angled triangles using sine, cosine, and tangent ratios; solve practical problems involving heights and distances using trigonometry.",
            "source_reference": "SYL_2024_MATH_4008_5.2",
            "subject": "Mathematics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
            "question_id": "Q3c",
            "syllabus_ref": "5.2.1 Trigonometric Ratios",
            "mark_mapping": None,
            "source_year": 2024,
            "confidence_weight": 0.8,
            "metadata": {
                "topic": "Trigonometry",
                "assessment_objective": "AO2 - Application"
            }
        }
    ])
    
    # ========== PHYSICS O-LEVEL (Paper 5054) ==========
    
    # Question 1: Forces and Motion
    evidence.extend([
        {
            "source_type": "marking_scheme",
            "content": "Award 1 mark for stating Newton's Second Law (F = ma). Award 1 mark for correct substitution: F = 5 kg × 2 m/s². Award 1 mark for correct answer with units: F = 10 N.",
            "source_reference": "MS_2024_PHYS_5054_Q1a",
            "subject": "Physics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_PHYS_5054",
            "question_id": "Q1a",
            "syllabus_ref": "2.1.2 Newton's Laws",
            "mark_mapping": 3,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Forces and Motion",
                "difficulty": "Easy",
                "max_marks": 3
            }
        },
        {
            "source_type": "examiner_report",
            "content": "This was a straightforward recall and application question. Most candidates knew F=ma but many forgot to include units in their final answer, losing the unit mark. Some candidates confused mass and weight.",
            "source_reference": "ER_2024_PHYS_5054_Q1a",
            "subject": "Physics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_PHYS_5054",
            "question_id": "Q1a",
            "syllabus_ref": "2.1.2 Newton's Laws",
            "mark_mapping": None,
            "source_year": 2024,
            "confidence_weight": 0.9,
            "metadata": {
                "topic": "Forces and Motion",
                "common_errors": ["missing units", "mass/weight confusion"]
            }
        },
        {
            "source_type": "model_answer",
            "content": "Using Newton's Second Law: F = ma. Given: mass m = 5 kg, acceleration a = 2 m/s². Substituting: F = 5 × 2 = 10 N. Therefore the force is 10 N.",
            "source_reference": "MA_2024_PHYS_5054_Q1a",
            "subject": "Physics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_PHYS_5054",
            "question_id": "Q1a",
            "syllabus_ref": "2.1.2 Newton's Laws",
            "mark_mapping": 3,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Forces and Motion",
                "concept": "Newton's Second Law"
            }
        }
    ])
    
    # Question 2: Electricity - Ohm's Law
    evidence.extend([
        {
            "source_type": "marking_scheme",
            "content": "Award 1 mark for stating Ohm's Law (V = IR). Award 1 mark for rearranging to find current: I = V/R. Award 1 mark for correct substitution: I = 12V / 4Ω. Award 1 mark for correct answer: I = 3 A.",
            "source_reference": "MS_2024_PHYS_5054_Q2c",
            "subject": "Physics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_PHYS_5054",
            "question_id": "Q2c",
            "syllabus_ref": "3.2.1 Ohm's Law",
            "mark_mapping": 4,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Electricity",
                "difficulty": "Medium",
                "max_marks": 4
            }
        },
        {
            "source_type": "examiner_report",
            "content": "Generally well answered. Candidates who showed clear rearrangement steps scored full marks. Common error: using incorrect formula variations (e.g., I = R/V). Always show formula, substitution, and final answer with units.",
            "source_reference": "ER_2024_PHYS_5054_Q2c",
            "subject": "Physics",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_PHYS_5054",
            "question_id": "Q2c",
            "syllabus_ref": "3.2.1 Ohm's Law",
            "mark_mapping": None,
            "source_year": 2024,
            "confidence_weight": 0.9,
            "metadata": {
                "topic": "Electricity",
                "common_errors": ["incorrect formula", "no working shown"]
            }
        }
    ])
    
    # ========== ENGLISH O-LEVEL (Paper 1184) ==========
    
    # Question 1: Comprehension
    evidence.extend([
        {
            "source_type": "marking_scheme",
            "content": "Award up to 3 marks for interpretation of the phrase 'turning point'. 3 marks: Clear explanation showing the moment changed the character's perspective permanently. 2 marks: Adequate explanation of change but lacking detail. 1 mark: Basic identification that something changed. 0 marks: No understanding demonstrated.",
            "source_reference": "MS_2024_ENG_1184_Q1b",
            "subject": "English Language",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_ENG_1184",
            "question_id": "Q1b",
            "syllabus_ref": "1.2 Reading Comprehension",
            "mark_mapping": 3,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Comprehension",
                "difficulty": "Medium",
                "max_marks": 3,
                "skill": "interpretation"
            }
        },
        {
            "source_type": "examiner_report",
            "content": "This question required candidates to infer meaning from context. Successful candidates quoted the relevant section and explained its significance. Weaker candidates simply copied phrases without explanation. Use of own words demonstrates understanding.",
            "source_reference": "ER_2024_ENG_1184_Q1b",
            "subject": "English Language",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_ENG_1184",
            "question_id": "Q1b",
            "syllabus_ref": "1.2 Reading Comprehension",
            "mark_mapping": None,
            "source_year": 2024,
            "confidence_weight": 0.9,
            "metadata": {
                "topic": "Comprehension",
                "common_errors": ["copying without explanation", "lack of inference"]
            }
        }
    ])
    
    # Question 2: Summary Writing
    evidence.extend([
        {
            "source_type": "marking_scheme",
            "content": "Content (5 marks): Award 1 mark for each key point identified (maximum 5 points). Language/Style (5 marks): 5 marks for fluent, accurate summary in own words; 4 marks for clear summary with minor errors; 3 marks for adequate summary with several errors; 2 marks for basic summary with many errors; 1 mark for poor attempt; 0 marks for no understanding.",
            "source_reference": "MS_2024_ENG_1184_Q2",
            "subject": "English Language",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_ENG_1184",
            "question_id": "Q2",
            "syllabus_ref": "2.1 Summary Writing",
            "mark_mapping": 10,
            "source_year": 2024,
            "confidence_weight": 1.0,
            "metadata": {
                "topic": "Summary Writing",
                "difficulty": "Hard",
                "max_marks": 10,
                "skill": "synthesis"
            }
        },
        {
            "source_type": "examiner_report",
            "content": "Summary writing continues to challenge candidates. Best responses identified key points systematically and expressed them concisely. Avoid copying large chunks verbatim. Use connecting words to create a coherent paragraph. Respect word limits.",
            "source_reference": "ER_2024_ENG_1184_Q2",
            "subject": "English Language",
            "syllabus_version": "ZIMSEC_2024",
            "paper_code": "ZIMSEC_O_LEVEL_ENG_1184",
            "question_id": "Q2",
            "syllabus_ref": "2.1 Summary Writing",
            "mark_mapping": None,
            "source_year": 2024,
            "confidence_weight": 0.9,
            "metadata": {
                "topic": "Summary Writing",
                "common_errors": ["verbatim copying", "exceeding word limit", "lack of coherence"]
            }
        }
    ])
    
    return evidence


def generate_embedding(content: str, trace_id: str = "SEEDING") -> List[float]:
    """Generate embedding vector for content.
    
    Args:
        content: Text content to embed
        trace_id: Trace ID for logging
        
    Returns:
        384-dimensional embedding vector
    """
    try:
        embedding = EmbeddingService.generate_embedding(content, trace_id)
        return embedding
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
        raise


def calculate_embedding_hash(embedding: List[float]) -> str:
    """Calculate SHA256 hash of embedding for audit trail.
    
    Args:
        embedding: Embedding vector
        
    Returns:
        Hex digest of SHA256 hash
    """
    embedding_bytes = str(embedding).encode('utf-8')
    return hashlib.sha256(embedding_bytes).hexdigest()


def seed_evidence(client: MongoClient) -> None:
    """Seed marking_evidence collection with sample data.
    
    Args:
        client: MongoDB client instance
    """
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== ZimPrep Evidence Seeding ===\\n")
    
    # Get sample evidence
    print("Step 1: Generating sample evidence...")
    sample_evidence = create_sample_evidence()
    print(f"✓ Created {len(sample_evidence)} evidence documents\\n")
    
    # Generate embeddings and insert
    print("Step 2: Generating embeddings and inserting documents...")
    inserted_count = 0
    skipped_count = 0
    error_count = 0
    
    for idx, evidence_doc in enumerate(sample_evidence, 1):
        try:
            # Generate embedding
            embedding = generate_embedding(
                content=evidence_doc["content"],
                trace_id=f"SEED_{idx}"
            )
            
            # Add embedding and metadata to document
            evidence_doc["embedding"] = embedding
            evidence_doc["created_at"] = datetime.utcnow()
            evidence_doc["embedding_model"] = EMBEDDING_MODEL
            evidence_doc["embedding_version"] = EMBEDDING_VERSION
            
            # Insert document
            collection.insert_one(evidence_doc)
            inserted_count += 1
            
            print(f"✓ [{idx}/{len(sample_evidence)}] Inserted: {evidence_doc['source_reference']}")
            
        except DuplicateKeyError:
            skipped_count += 1
            print(f"⊘ [{idx}/{len(sample_evidence)}] Skipped (duplicate): {evidence_doc['source_reference']}")
            
        except Exception as e:
            error_count += 1
            print(f"✗ [{idx}/{len(sample_evidence)}] Error: {evidence_doc['source_reference']} - {e}")
    
    print(f"\\n=== Seeding Complete ===")
    print(f"✓ Inserted: {inserted_count}")
    print(f"⊘ Skipped (duplicates): {skipped_count}")
    print(f"✗ Errors: {error_count}")
    print(f"\\nTotal documents in collection: {collection.count_documents({})}")
    
    # Display statistics by source type
    print("\\n=== Evidence Statistics ===")
    pipeline = [
        {"$group": {
            "_id": "$source_type",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    for stat in collection.aggregate(pipeline):
        print(f"{stat['_id']}: {stat['count']}")
    
    # Display statistics by subject
    print("\\n=== Subject Distribution ===")
    pipeline = [
        {"$group": {
            "_id": "$subject",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    for stat in collection.aggregate(pipeline):
        print(f"{stat['_id']}: {stat['count']}")


def main():
    """Main execution function."""
    print("Connecting to MongoDB...")
    
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB at {MONGO_URI}\\n")
        
        # Seed evidence
        seed_evidence(client)
        
        print("\\n✓ Evidence seeding complete!")
        print("\\nNext steps:")
        print("1. Verify: db.marking_evidence.countDocuments()")
        print("2. Create vector search index in Atlas (see init_vector_store.js)")
        print("3. Test retrieval: python tests/test_retrieval_with_evidence.py")
        
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        sys.exit(1)
    
    finally:
        client.close()


if __name__ == "__main__":
    main()
