/**
 * MongoDB Atlas Vector Search Initialization Script
 * 
 * Purpose: Configure vector search index for marking_evidence collection
 * 
 * Requirements:
 * - MongoDB Atlas with Vector Search enabled
 * - Collection: marking_evidence
 * - Embedding dimensions: 384 (sentence-transformers/all-MiniLM-L6-v2)
 * - Similarity metric: cosine
 * 
 * Usage:
 *   mongosh "mongodb://localhost:27017/zimprep" init_vector_store.js
 */

// Switch to zimprep database
db = db.getSiblingDB('zimprep');

print('=== ZimPrep Vector Store Initialization ===\n');

// Step 1: Create marking_evidence collection if it doesn't exist
print('Step 1: Creating marking_evidence collection...');
try {
    db.createCollection('marking_evidence', {
        validator: {
            $jsonSchema: {
                bsonType: 'object',
                required: [
                    'source_type',
                    'content',
                    'embedding',
                    'source_reference',
                    'subject',
                    'syllabus_version',
                    'paper_code',
                    'question_id'
                ],
                properties: {
                    source_type: {
                        bsonType: 'string',
                        enum: [
                            'marking_scheme',
                            'examiner_report',
                            'model_answer',
                            'syllabus_excerpt',
                            'student_answer'
                        ],
                        description: 'Type of evidence source'
                    },
                    content: {
                        bsonType: 'string',
                        description: 'Original text content from source document (verbatim)'
                    },
                    embedding: {
                        bsonType: 'array',
                        items: { bsonType: 'double' },
                        description: 'Vector embedding (384 dimensions)'
                    },
                    source_reference: {
                        bsonType: 'string',
                        description: 'Document ID or reference for audit trail'
                    },
                    subject: {
                        bsonType: 'string',
                        description: 'Subject name (e.g., Mathematics, Physics)'
                    },
                    syllabus_version: {
                        bsonType: 'string',
                        description: 'Syllabus version identifier'
                    },
                    paper_code: {
                        bsonType: 'string',
                        description: 'Paper code (e.g., ZIMSEC_O_LEVEL_MATH_4008)'
                    },
                    question_id: {
                        bsonType: 'string',
                        description: 'Question identifier'
                    },
                    syllabus_ref: {
                        bsonType: ['string', 'null'],
                        description: 'Syllabus reference if applicable'
                    },
                    mark_mapping: {
                        bsonType: ['int', 'null'],
                        minimum: 0,
                        description: 'Mark allocation if specified'
                    },
                    source_year: {
                        bsonType: ['int', 'null'],
                        description: 'Year of source document'
                    },
                    confidence_weight: {
                        bsonType: ['double', 'null'],
                        minimum: 0.0,
                        maximum: 1.0,
                        description: 'Evidence confidence weight (1.0 = official, 0.6 = student)'
                    },
                    metadata: {
                        bsonType: ['object', 'null'],
                        description: 'Additional metadata from source document'
                    },
                    created_at: {
                        bsonType: 'date',
                        description: 'Timestamp when evidence was ingested'
                    },
                    embedding_model: {
                        bsonType: 'string',
                        description: 'Model used to generate embedding'
                    },
                    embedding_version: {
                        bsonType: 'string',
                        description: 'Version of embedding for cache invalidation'
                    }
                }
            }
        }
    });
    print('✓ Collection created successfully\n');
} catch (e) {
    if (e.code === 48) {
        print('✓ Collection already exists\n');
    } else {
        print('✗ Error creating collection:', e.message);
        quit(1);
    }
}

// Step 2: Create indexes for metadata filtering
print('Step 2: Creating metadata indexes...');

const indexes = [
    {
        key: { source_type: 1 },
        name: 'idx_source_type',
        background: true
    },
    {
        key: { subject: 1, syllabus_version: 1, paper_code: 1 },
        name: 'idx_subject_syllabus_paper',
        background: true
    },
    {
        key: { question_id: 1 },
        name: 'idx_question_id',
        background: true
    },
    {
        key: { source_reference: 1 },
        name: 'idx_source_reference',
        unique: true,
        background: true
    },
    {
        key: { created_at: 1 },
        name: 'idx_created_at',
        background: true
    }
];

indexes.forEach(index => {
    try {
        db.marking_evidence.createIndex(index.key, {
            name: index.name,
            background: index.background,
            unique: index.unique || false
        });
        print(`✓ Created index: ${index.name}`);
    } catch (e) {
        if (e.code === 85 || e.code === 86) {
            print(`✓ Index already exists: ${index.name}`);
        } else {
            print(`✗ Error creating index ${index.name}:`, e.message);
        }
    }
});
print('');

// Step 3: Display Vector Search index creation instructions
print('Step 3: Vector Search Index Configuration\n');
print('IMPORTANT: MongoDB Atlas Vector Search indexes must be created via Atlas UI or API.\n');
print('Follow these steps:\n');
print('1. Go to MongoDB Atlas Console');
print('2. Navigate to your cluster → Collections → zimprep → marking_evidence');
print('3. Click "Search Indexes" tab');
print('4. Click "Create Search Index"');
print('5. Select "JSON Editor"');
print('6. Use the following configuration:\n');

const vectorIndexConfig = {
    "name": "evidence_vector_index",
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 384,
                "similarity": "cosine"
            },
            {
                "type": "filter",
                "path": "source_type"
            },
            {
                "type": "filter",
                "path": "subject"
            },
            {
                "type": "filter",
                "path": "syllabus_version"
            },
            {
                "type": "filter",
                "path": "paper_code"
            },
            {
                "type": "filter",
                "path": "question_id"
            }
        ]
    }
};

print(JSON.stringify(vectorIndexConfig, null, 2));
print('\n');

print('Alternative: Create via Atlas CLI:');
print('atlas clusters search indexes create \\');
print('  --clusterName <your-cluster> \\');
print('  --file vector_index_config.json\n');

// Step 4: Display collection statistics
print('Step 4: Collection Statistics\n');
const stats = db.marking_evidence.stats();
print(`✓ Collection: ${stats.ns}`);
print(`✓ Document count: ${stats.count}`);
print(`✓ Storage size: ${(stats.storageSize / 1024).toFixed(2)} KB`);
print(`✓ Indexes: ${stats.nindexes}`);
print('');

// Step 5: Sample document structure
print('Step 5: Sample Document Structure\n');
print('When inserting evidence, use this schema:');

const sampleDocument = {
    "source_type": "marking_scheme",
    "content": "Award 1 mark for identifying the formula. Award 1 mark for correct substitution. Award 1 mark for final answer with units.",
    "embedding": new Array(384).fill(0.123),  // 384-dimensional vector
    "source_reference": "MS_2024_4008_Q3a",
    "subject": "Mathematics",
    "syllabus_version": "ZIMSEC_2024",
    "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
    "question_id": "Q3a",
    "syllabus_ref": "3.2.1 Algebra",
    "mark_mapping": 3,
    "source_year": 2024,
    "confidence_weight": 1.0,
    "metadata": {
        "page_number": 5,
        "section": "Section A"
    },
    "created_at": new Date(),
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_version": "1.0.0"
};

print(JSON.stringify(sampleDocument, null, 2));
print('\n');

print('=== Vector Store Initialization Complete ===\n');
print('Next steps:');
print('1. Create vector search index in Atlas (see Step 3)');
print('2. Run: python scripts/seed_sample_evidence.py');
print('3. Verify: db.marking_evidence.countDocuments()');
print('');
