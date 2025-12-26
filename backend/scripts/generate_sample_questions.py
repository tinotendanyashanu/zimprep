"""Generate sample questions for ZimPrep question bank.

Creates 1000 realistic sample questions across subjects:
- Mathematics: 500 questions
- Science: 300 questions  
- English: 200 questions

Difficulty distribution: 40% easy, 40% medium, 20% hard

Run with: python -m scripts.generate_sample_questions
"""

import asyncio
from datetime import datetime
from motor import motor_asyncio
import os

# Question templates by subject and difficulty
MATH_QUESTIONS = {
    "easy": [
        ("Solve for x: 2x + 3 = 7", "Algebra", "calculation", 2, 3),
        ("What is 15% of 200?", "Percentages", "calculation", 2, 2),
        ("Calculate: 5 × 8", "Arithmetic", "calculation", 1, 1),
        ("Find the area of a rectangle with length 5cm and width 3cm", "Geometry", "calculation", 2, 3),
        ("Simplify: 2x + 3x", "Algebra", "calculation", 1, 2),
    ],
    "medium": [
        ("Solve the quadratic equation: x² + 5x + 6 = 0", "Quadratic Equations", "calculation", 5, 8),
        ("Factorize: x² - 9", "Factorization", "calculation", 3, 5),
        ("Find the derivative of f(x) = x³ + 2x²", "Calculus", "calculation", 5, 7),
        ("Calculate the area of a circle with radius 7cm (use π = 22/7)", "Geometry", "calculation", 3, 4),
        ("Solve the simultaneous equations: 2x + y = 5, x - y = 1", "Linear Equations", "calculation", 4, 6),
    ],
    "hard": [
        ("Prove that √2 is irrational", "Number Theory", "essay", 10, 15),
        ("Integrate: ∫(x² + 3x + 2)dx", "Calculus", "calculation", 8, 12),
        ("Find the general solution to the differential equation: dy/dx = xy", "Differential Equations", "calculation", 10, 15),
        ("Prove the Pythagorean theorem using similar triangles", "Geometry", "essay", 10, 20),
        ("Derive the quadratic formula from ax² + bx + c = 0", "Algebra", "essay", 8, 15),
    ]
}

SCIENCE_QUESTIONS = {
    "easy": [
        ("What is the chemical symbol for water?", "Chemistry", "multiple_choice", 1, 1),
        ("Name the three states of matter", "Physics", "multiple_choice", 2, 2),
        ("What is photosynthesis?", "Biology", "multiple_choice", 2, 3),
        ("What force pulls objects towards Earth?", "Physics", "multiple_choice", 1, 1),
        ("Name one renewable energy source", "Environmental Science", "multiple_choice", 1, 2),
    ],
    "medium": [
        ("Explain Newton's Second Law of Motion", "Physics", "structured", 5, 7),
        ("What is the difference between an atom and a molecule?", "Chemistry", "structured", 4, 6),
        ("Describe the process of cellular respiration", "Biology", "structured", 5, 8),
        ("Calculate the velocity of an object that travels 100m in 5 seconds", "Physics", "calculation", 3, 4),
        ("Balance the chemical equation: H₂ + O₂ → H₂O", "Chemistry", "calculation", 3, 5),
    ],
    "hard": [
        ("Explain the theory of evolution by natural selection", "Biology", "essay", 10, 15),
        ("Derive the equation E = mc² conceptually", "Physics", "essay", 10, 20),
        ("Explain the periodic table trends in atomic radius", "Chemistry", "essay", 8, 12),
        ("Describe the carbon cycle and its importance to ecosystems", "Environmental Science", "essay", 10, 15),
        ("Explain how DNA replication works", "Biology", "essay", 8, 15),
    ]
}

ENGLISH_QUESTIONS = {
    "easy": [
        ("Identify the noun in this sentence: 'The cat sat on the mat'", "Grammar", "multiple_choice", 1, 2),
        ("What is a synonym for 'happy'?", "Vocabulary", "multiple_choice", 1, 1),
        ("Identify the verb: 'She runs every morning'", "Grammar", "multiple_choice", 1, 1),
        ("What is the opposite of 'day'?", "Vocabulary", "multiple_choice", 1, 1),
        ("How many syllables are in 'elephant'?", "Phonics", "multiple_choice", 1, 2),
    ],
    "medium": [
        ("Explain the difference between 'there', 'their', and 'they're'", "Grammar", "structured", 4, 6),
        ("What is the main theme of this passage? [passage provided]", "Comprehension", "structured", 5, 8),
        ("Identify the literary device used: 'Time flies like an arrow'", "Literary Analysis", "structured", 3, 5),
        ("Write a topic sentence for a paragraph about climate change", "Writing", "structured", 3, 5),
        ("Correct the grammar: 'Me and him went to the store'", "Grammar", "calculation", 2, 3),
    ],
    "hard": [
        ("Analyze the use of symbolism in Shakespeare's Macbeth", "Literary Analysis", "essay", 10, 20),
        ("Compare and contrast romantic and modernist poetry", "Literary Analysis", "essay", 10, 20),
        ("Write a persuasive essay on the importance of reading", "Writing", "essay", 10, 25),
        ("Explain the concept of irony with examples from literature", "Literary Analysis", "essay", 8, 15),
        ("Analyze the narrative structure of a novel of your choice", "Literary Analysis", "essay", 10, 20),
    ]
}


async def generate_questions():
    """Generate and insert sample questions into MongoDB."""
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client.zimprep
    collection = db.questions
    
    print("🚀 Generating sample questions...")
    print(f"   Connected to MongoDB: {mongo_uri}")
    
    questions = []
    question_counter = 1
    
    # Generate Mathematics questions (500)
    print("\n📐 Generating Mathematics questions (500)...")
    for _ in range(2):  # Repeat to get to 500
        for difficulty, templates in MATH_QUESTIONS.items():
            count = 80 if difficulty in ["easy", "medium"] else 40  # 40% easy, 40% medium, 20% hard
            for i in range(count // len(templates)):
                for template in templates:
                    text, topic, q_type, marks, minutes = template
                    
                    question = {
                        "question_id": f"q_math_{question_counter:04d}",
                        "question_text": text,
                        "question_type": q_type,
                        "topic_id": f"topic_{topic.lower().replace(' ', '_')}",
                        "topic_name": topic,
                        "subject": "Mathematics",
                        "syllabus_version": "2025_v1",
                        "difficulty": difficulty,
                        "max_marks": marks,
                        "estimated_minutes": minutes,
                        "answer_key": {"correct_answer": "Sample answer"},
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    questions.append(question)
                    question_counter += 1
                    
                    if len([q for q in questions if q["subject"] == "Mathematics"]) >= 500:
                        break
                if len([q for q in questions if q["subject"] == "Mathematics"]) >= 500:
                    break
            if len([q for q in questions if q["subject"] == "Mathematics"]) >= 500:
                break
        if len([q for q in questions if q["subject"] == "Mathematics"]) >= 500:
            break
    
    # Generate Science questions (300)
    print("🔬 Generating Science questions (300)...")
    science_counter = 1
    for _ in range(2):  # Repeat to get to 300
        for difficulty, templates in SCIENCE_QUESTIONS.items():
            count = 48 if difficulty in ["easy", "medium"] else 24  # 40% easy, 40% medium, 20% hard
            for i in range(count // len(templates)):
                for template in templates:
                    text, topic, q_type, marks, minutes = template
                    
                    question = {
                        "question_id": f"q_science_{science_counter:04d}",
                        "question_text": text,
                        "question_type": q_type,
                        "topic_id": f"topic_{topic.lower().replace(' ', '_')}",
                        "topic_name": topic,
                        "subject": "Science",
                        "syllabus_version": "2025_v1",
                        "difficulty": difficulty,
                        "max_marks": marks,
                        "estimated_minutes": minutes,
                        "answer_key": {"correct_answer": "Sample answer"},
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    questions.append(question)
                    science_counter += 1
                    
                    if len([q for q in questions if q["subject"] == "Science"]) >= 300:
                        break
                if len([q for q in questions if q["subject"] == "Science"]) >= 300:
                    break
            if len([q for q in questions if q["subject"] == "Science"]) >= 300:
                break
        if len([q for q in questions if q["subject"] == "Science"]) >= 300:
            break
    
    # Generate English questions (200)
    print("📚 Generating English questions (200)...")
    english_counter = 1
    for _ in range(2):  # Repeat to get to 200
        for difficulty, templates in ENGLISH_QUESTIONS.items():
            count = 32 if difficulty in ["easy", "medium"] else 16  # 40% easy, 40% medium, 20% hard
            for i in range(count // len(templates)):
                for template in templates:
                    text, topic, q_type, marks, minutes = template
                    
                    question = {
                        "question_id": f"q_english_{english_counter:04d}",
                        "question_text": text,
                        "question_type": q_type,
                        "topic_id": f"topic_{topic.lower().replace(' ', '_')}",
                        "topic_name": topic,
                        "subject": "English",
                        "syllabus_version": "2025_v1",
                        "difficulty": difficulty,
                        "max_marks": marks,
                        "estimated_minutes": minutes,
                        "answer_key": {"correct_answer": "Sample answer"},
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    questions.append(question)
                    english_counter += 1
                    
                    if len([q for q in questions if q["subject"] == "English"]) >= 200:
                        break
                if len([q for q in questions if q["subject"] == "English"]) >= 200:
                    break
            if len([q for q in questions if q["subject"] == "English"]) >= 200:
                break
        if len([q for q in questions if q["subject"] == "English"]) >= 200:
            break
    
    # Insert into MongoDB
    print(f"\n💾 Inserting {len(questions)} questions into MongoDB...")
    
    if questions:
        result = await collection.insert_many(questions)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} questions!")
        
        # Print statistics
        math_count = len([q for q in questions if q["subject"] == "Mathematics"])
        science_count = len([q for q in questions if q["subject"] == "Science"])
        english_count = len([q for q in questions if q["subject"] == "English"])
        
        easy_count = len([q for q in questions if q["difficulty"] == "easy"])
        medium_count = len([q for q in questions if q["difficulty"] == "medium"])
        hard_count = len([q for q in questions if q["difficulty"] == "hard"])
        
        print(f"\n📊 Question Statistics:")
        print(f"   Mathematics: {math_count}")
        print(f"   Science: {science_count}")
        print(f"   English: {english_count}")
        print(f"   Total: {len(questions)}")
        print(f"\n   Easy: {easy_count} ({easy_count/len(questions)*100:.1f}%)")
        print(f"   Medium: {medium_count} ({medium_count/len(questions)*100:.1f}%)")
        print(f"   Hard: {hard_count} ({hard_count/len(questions)*100:.1f}%)")
    
    client.close()
    print("\n🎉 Sample question generation complete!")


if __name__ == "__main__":
    asyncio.run(generate_questions())
