# StudyUIC RAG (Retrieval-Augmented Generation) System

## Architecture Overview

The RAG system enables semantic search and context-aware answers to questions about UIC academic information.

```
User Question
  ↓
[Query Embedding] ← OpenRouter text-embedding-3-small
  ↓
[Vector Similarity Search] ← pgvector on PostgreSQL
  ↓
[Metadata Filtering] (department, course_level, etc.)
  ↓
[Retrieve Documents + Context]
  ↓
[Build RAG Context] (preserve source information)
  ↓
[OpenRouter LLM Generation] ← Future phase
```

## Components

### 1. Document Construction (`rag_documents.py`)

**Deterministic, repeatable process** that converts course records into embedding documents:

- Input: CourseRecord (from Supabase)
- Output: RagDocument with structured text, metadata, and content hash
- Key property: Same course record → same document_text and content_hash

**Example document:**

```
Course: CS 251
Title: Data Structures
Department: Computer Science
Credits: 3
Course Level: 200
Prerequisites: CS 150 or equivalent
Description: Study of data structures including arrays, lists, stacks, queues, trees, and graphs.
Analysis of algorithms for searching and sorting.
```

**Metadata preserved:**

```json
{
  "department": "CS",
  "course_code": "CS 251",
  "course_level": 200,
  "credits": 3,
  "course_title": "Data Structures"
}
```

### 2. Embedding Generation (`embeddings.py`)

**Separate from LLM generation model.**

- Model: `text-embedding-3-small` (default, configurable)
- Dimensions: 1536
- Provider: OpenRouter (OpenAI-compatible API)
- Configuration via environment variables:
  - `EMBEDDING_MODEL`: Default `text-embedding-3-small`
  - `EMBEDDING_DIMENSIONS`: Default `1536`
  - Uses existing `OPENROUTER_API_KEY`

**Features:**

- Single embedding via `embed(text: str) → list[float]`
- Batch embeddings via `embed_batch(texts: list[str]) → list[list[float]]`
- Dimension validation before storage
- Graceful degradation when API is unavailable

### 3. Vector Storage (`rag_documents` table in Supabase)

**Schema:**

```sql
rag_documents (
  id uuid primary key,
  source_type text check (...in 'course', 'program', 'policy', 'resource'),
  source_id uuid,
  source_table text,
  document_text text,
  metadata jsonb,
  embedding vector(1536),
  embedding_model text,
  embedding_version text,
  content_hash text,
  created_at timestamptz,
  updated_at timestamptz
)
```

**Indexes:**

- `rag_documents_embedding_idx`: IVFFLAT vector index for similarity search
- `rag_documents_source_idx`: (source_type, source_id) for deduplication
- `rag_documents_hash_idx`: content_hash for change detection

**RPC for retrieval:**

```sql
retrieve_similar_documents(
  p_query_embedding vector(1536),
  p_limit integer,
  p_department text,
  p_course_level integer
) → table of (id, source_type, source_id, document_text, metadata, similarity, embedding_model, embedding_version)
```

### 4. Ingestion Pipeline (`rag_ingestion.py`)

**Deterministic, idempotent backfill process:**

1. Fetch all active courses from Supabase
2. Construct deterministic documents (via `rag_documents.py`)
3. Compute content_hash for each
4. Check if content changed (vs. database)
5. Generate embeddings only if needed
6. Upsert documents with embeddings

**Error handling:**

- Logs all failures without stopping pipeline
- Returns statistics: total, inserted, skipped, errors
- Can be safely rerun (idempotent via content_hash)

**Usage:**

```python
pipeline = RagIngestionPipeline()
stats = await pipeline.ingest_all_courses(batch_size=10)
# {
#   "total_courses": 150,
#   "documents_inserted": 150,
#   "documents_skipped": 0,
#   "errors": []
# }
```

### 5. Query-Time Retrieval (`rag_retrieval.py`)

**Retrieve relevant documents for user questions:**

Input:

```python
RetrievalQuery(
  question="What courses can I take after CS 251?",
  top_k=5,
  department_filter=None,
  course_level_filter=None
)
```

Process:

1. Embed the user question using same embedding model
2. Call `retrieve_similar_documents` RPC with query embedding
3. Apply optional metadata filters (department, course_level)
4. Return ranked results with similarity scores and source metadata

Output:

```python
[
  RetrievalResult(
    document_id="...",
    source_type="course",
    source_id="...",
    document_text="Course: CS 361 ...",
    metadata={"department": "CS", "course_level": 300, ...},
    similarity_score=0.87,
    embedding_model="text-embedding-3-small",
    embedding_version="1"
  ),
  ...
]
```

## Environment Configuration

### Required for Ingestion & Retrieval

```bash
OPENROUTER_API_KEY="your-key"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
EMBEDDING_MODEL="text-embedding-3-small"
EMBEDDING_DIMENSIONS="1536"
EMBEDDING_TIMEOUT_SECONDS="30"
```

### Backend Access

```bash
SUPABASE_URL="your-supabase-url"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

## Testing

### Unit Tests

```bash
pytest app/backend/tests/test_rag_documents.py -v
```

Tests for:

- Document construction from course records
- Determinism (same input → same output)
- Content hash changes on data modification
- Metadata extraction
- Field preference (long_description vs description)

### Document Construction Tests

```python
def test_construct_course_document_determinism():
    # Identical courses produce identical documents
    course1 = CourseRecord(...)
    course2 = CourseRecord(...)
    
    doc1 = construct_course_document(course1)
    doc2 = construct_course_document(course2)
    
    assert doc1.document_text == doc2.document_text
    assert doc1.content_hash == doc2.content_hash
```

### Integration Tests (Future)

- [ ] Ingestion pipeline with mock Supabase
- [ ] Retrieval accuracy with known courses
- [ ] Metadata filtering correctness
- [ ] Embedding dimension validation
- [ ] Error handling (API failures, malformed data)

## Evaluation Dataset

RAG evaluation should measure:

### 1. Factual Lookup

- Question: "What is the prerequisite for CS 251?"
- Expected: Document for CS 251 with prerequisite field
- Category: Exact recall

### 2. Semantic Search

- Question: "What courses are related to artificial intelligence?"
- Expected: CS courses with AI-related keywords in description
- Category: Recall@K

### 3. Multi-Document Questions

- Question: "What courses should I take for machine learning?"
- Expected: Multiple courses (CS 401, CS 412, CS 461, etc.)
- Category: Recall@K for multiple sources

### 4. Metadata/Filter Questions

- Question: "What 400-level CS courses have AI-related content?"
- Expected: CS courses with course_level=400 and AI keywords
- Category: Metadata filtering accuracy

### 5. No-Answer Questions

- Question: "What is the average salary for a CS graduate?"
- Expected: No result (data not in database)
- Category: Empty result handling

### 6. Ambiguous Questions

- Question: "Can I take algorithms next semester?"
- Expected: Courses with "algorithms" but unclear prerequisites
- Category: Uncertainty handling

## Retrieval Evaluation Metrics

### Recall@K

Proportion of queries where the expected document appeared in top K results:

```
Recall@5 = (queries with expected doc in top 5) / total_queries
```

### Mean Reciprocal Rank (MRR)

Average rank of first relevant document:

```
MRR = mean(1 / rank_of_first_relevant_doc)
```

### Precision@K

Proportion of retrieved documents that are relevant:

```
Precision@5 = (relevant docs in top 5) / 5
```

## Phase Breakdown

### ✅ Phase 1: Schema & Ingestion (COMPLETE)

- [x] Extend `courses` table with academic fields
- [x] Create `rag_documents` table with pgvector support
- [x] Enable pgvector extension in Supabase migration
- [x] Document construction logic (deterministic)
- [x] Embedding service (OpenRouter, batch capable)
- [x] Ingestion pipeline (idempotent)
- [x] Unit tests for document construction

### ⏳ Phase 2: Query-Time Retrieval

- [ ] Complete RPC integration for vector similarity search
- [ ] Implement metadata filtering in retrieval
- [ ] Build error handling for edge cases
- [ ] Ranking and score normalization
- [ ] Integration tests

### ⏳ Phase 3: Context Building & LLM Integration

- [ ] RAG context formatter with source preservation
- [ ] OpenRouter LLM response generation (reuse existing service)
- [ ] Citation/source tracking in responses

### ⏳ Phase 4: Evaluation & Testing

- [ ] Build evaluation dataset (30-50 questions)
- [ ] Implement Recall@K and MRR metrics
- [ ] Regression testing framework
- [ ] Manual spot-checking for edge cases

## Data Flow

### Ingestion

```
Supabase courses table
  ↓
CourseRecord (Python dataclass)
  ↓
construct_course_document()
  ↓
RagDocument (with deterministic text + metadata)
  ↓
EmbeddingClient.embed_batch()
  ↓
[1536-dim vectors]
  ↓
Supabase rag_documents table (with pgvector column)
```

### Retrieval

```
User question
  ↓
EmbeddingClient.embed()
  ↓
[1536-dim query embedding]
  ↓
Supabase RPC: retrieve_similar_documents()
  ↓
pgvector cosine similarity search
  ↓
Metadata filtering (optional)
  ↓
Top-K results with scores
  ↓
RetrievalResult objects
```

## Known Limitations & Future Work

1. **LLM Response Generation**: Not yet implemented. Retrieval API is independent.
2. **Hybrid Search**: Currently vector-only; lexical/BM25 search could be added.
3. **Chunking**: Currently no chunking. Course records fit naturally in context window.
4. **Update Mechanism**: Content hash based. Full refresh is safe but could be optimized.
5. **Fine-tuned Models**: Currently using general-purpose embedding model.
6. **Batch Retrieval**: Single-query retrieval only; batch queries not yet supported.

## References

- [pgvector documentation](https://github.com/pgvector/pgvector)
- [Supabase Vector Documentation](https://supabase.com/docs/guides/database/extensions/pgvector)
- [OpenRouter Embeddings API](https://openrouter.ai/)
