# Multi-Agent Research Assistant: Intelligent Document Analysis System

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.127+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent document analysis system powered by a team of specialized AI agents that work collaboratively to answer complex questions about user-uploaded documents. By combining semantic search, multi-step reasoning, and iterative refinement, the system provides comprehensive, well-cited answers with complete transparency into the decision-making process.

**Key Innovation:** Instead of a single AI model, this system deploys a coordinated team of four specialized agents—Planner, Retriever, Evaluator, and Synthesizer—each optimized for a specific aspect of the research pipeline. This multi-agent architecture enables adaptive query strategies, quality assurance, and iterative improvement of retrieval results.

---

## 🎯 Features

### Document Processing & Management
- **PDF Upload & Extraction**: Advanced multi-column text extraction using PyMuPDF with intelligent reading order detection
- **Intelligent Chunking**: Context-aware text segmentation with configurable chunk size and overlap to preserve semantic coherence
- **Semantic Embeddings**: OpenAI's `text-embedding-3-small` model for high-quality vector representations
- **Multi-Chat Support**: Organize documents into separate chat sessions, with queries scoped to specific document collections
- **Persistent Storage**: ChromaDB vector database for efficient similarity search, PostgreSQL for metadata and chat history

### Multi-Agent Intelligence System
- **Planner Agent**: Analyzes queries, resolves ambiguous references using conversation history, and generates optimal retrieval strategies
- **Retriever Agent**: Executes similarity searches across vector database with configurable top-k parameters and document filtering
- **Evaluator Agent**: Assesses whether retrieved context is sufficient to answer the query, measuring coverage, depth, and confidence
- **Synthesizer Agent**: Generates coherent, well-structured answers with proper source citations
- **Refinement Controller**: Orchestrates iterative retrieval refinement when initial results are insufficient (up to 3 iterations)

### Advanced Capabilities
- **Conversational Memory**: Redis-based session management for multi-turn dialogues with 1-hour TTL
- **Adaptive Retrieval**: Dynamic adjustment of search queries and top-k based on question complexity
- **Citation Management**: Automatic source tracking with document ID, page number, and chunk-level granularity
- **Reasoning Transparency**: Complete trace of agent decisions, including planning steps, evaluations, and synthesis logic
- **Quality Assurance**: Confidence scoring and sufficiency checks before answer generation
- **Error Resilience**: Comprehensive retry logic with exponential backoff for API calls and database operations

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   Document   │      │     Chat     │      │    Health    │ │
│  │   Endpoints  │      │  Endpoints   │      │    Check     │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     Multi-Agent Orchestration                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Refinement Controller (Iterative Improvement Loop)      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐  ┌────────────┐ │
│  │ Planner  │──>│Retriever │──>│ Evaluator │─>│Synthesizer │ │
│  │  Agent   │   │  Agent   │   │   Agent   │  │   Agent    │ │
│  └──────────┘   └──────────┘   └───────────┘  └────────────┘ │
│       │                │              │              │         │
├───────┼────────────────┼──────────────┼──────────────┼─────────┤
│       v                v              v              v         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              LLM Integration Layer (GPT-4o)             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Document Processing Pipeline                 │
│  ┌────────┐   ┌─────────┐   ┌─────────┐   ┌──────────────┐   │
│  │ Upload │──>│ Extract │──>│  Chunk  │──>│ Embed & Store│   │
│  └────────┘   └─────────┘   └─────────┘   └──────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                       Storage & Memory Layer                    │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌────────────┐  │
│  │ ChromaDB │  │PostgreSQL│  │   Redis    │  │   OpenAI   │  │
│  │(Vectors) │  │(Metadata)│  │ (Sessions) │  │ Embeddings │  │
│  └──────────┘  └──────────┘  └────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: Query Processing Pipeline

```
User Query
    │
    ├─> 1. Session Validation (Redis)
    │
    ├─> 2. Planner Agent
    │      • Resolve ambiguous references (conversation history)
    │      • Classify question type (definition, comparison, etc.)
    │      • Generate search queries with optimal top_k
    │
    ├─> 3. Retriever Agent
    │      • Execute similarity search (ChromaDB)
    │      • Filter by chat's document collection
    │      • Retrieve top-k most relevant chunks
    │
    ├─> 4. Evaluator Agent
    │      • Assess context sufficiency
    │      • Calculate confidence score
    │      • Identify missing aspects
    │
    ├─> 5. Refinement Controller (if needed)
    │      • Generate refinement queries
    │      • Additional retrieval iterations (max 3)
    │      • Re-evaluate merged context
    │
    ├─> 6. Synthesizer Agent
    │      • Generate final answer from context
    │      • Extract and format citations
    │      • Store in conversation history
    │
    └─> Response
           • Answer with citations
           • Reasoning trace
           • Processing summary
           • Refinement iterations
```

---

## 🤖 The Agent Team

### 1. Planner Agent
**Role:** Query Analyst & Strategy Designer

The Planner is the first agent in the pipeline, responsible for understanding user intent and designing an optimal retrieval strategy.

**Capabilities:**
- **Context Resolution**: Uses conversation history to resolve pronouns and ambiguous references (e.g., "What about its disadvantages?" → understands "its" refers to previous topic)
- **Question Classification**: Identifies question type (definition, comparison, pros/cons, explanation, procedural) to tailor retrieval strategy
- **Dynamic Search Generation**: Creates 1-N search queries with adaptive top_k values based on question complexity
- **Reasoning Transparency**: Logs planning decisions for debugging and user visibility

**Example Workflow:**
```
User: "Compare transformer and RNN architectures"
Planner Output:
{
  "resolved_question": "Compare transformer and RNN architectures",
  "question_type": "comparison",
  "search_queries": [
    {"query": "transformer architecture", "top_k": 5},
    {"query": "RNN architecture", "top_k": 5},
    {"query": "transformer vs RNN comparison", "top_k": 3}
  ],
  "max_searches": 3
}
```

### 2. Retriever Agent
**Role:** Document Discovery Specialist

Executes the retrieval plan by performing semantic similarity searches against the vector database.

**Capabilities:**
- **Semantic Search**: Uses cosine similarity on embeddings to find contextually relevant chunks
- **Document Filtering**: Restricts search to documents associated with specific chat sessions
- **Configurable Retrieval**: Supports dynamic top_k and search query parameters
- **Retry Logic**: Automatic retry with exponential backoff for transient failures

**Key Feature:** Unlike traditional keyword search, semantic search understands conceptual similarity—queries about "machine learning speed" will match chunks discussing "training performance" even without exact keyword overlap.

### 3. Evaluator Agent
**Role:** Quality Assurance Inspector

Assesses whether retrieved context is sufficient to answer the user's question before generating a response.

**Capabilities:**
- **Sufficiency Assessment**: Determines if context provides adequate information
- **Confidence Scoring**: Assigns 0-1 confidence score based on coverage and depth
- **Gap Analysis**: Identifies missing aspects that should be addressed
- **Follow-up Suggestions**: Recommends additional search queries if context is insufficient

**Decision Criteria:**
- **Coverage**: Are all required aspects of the question addressed?
- **Depth**: Is the information detailed enough or too surface-level?
- **Completeness**: For comparisons, are both sides covered? For pros/cons, are both addressed?

**Example Evaluation:**
```json
{
  "is_sufficient": false,
  "confidence_score": 0.6,
  "missing_aspects": [
    "Disadvantages of transformer architecture not covered",
    "Performance comparison metrics missing"
  ],
  "suggested_followups": [
    "transformer architecture limitations",
    "RNN vs transformer benchmark results"
  ]
}
```

### 4. Synthesizer Agent
**Role:** Answer Composer & Citation Manager

Generates the final answer by synthesizing information from retrieved context while maintaining strict source attribution.

**Capabilities:**
- **Context-Grounded Answers**: Only uses information present in retrieved documents—no hallucination
- **Citation Extraction**: Automatically tracks sources with document ID, page number, and chunk ID
- **Structured Formatting**: Produces clear, well-organized responses
- **Conversation Storage**: Updates session history for multi-turn dialogues

**Key Principles:**
- Never speculates beyond provided context
- Explicitly states when information is unavailable
- Deduplicates citations while preserving all source references

### Refinement Controller (Orchestrator)
**Role:** Iterative Improvement Coordinator

Manages the refinement loop when initial retrieval is insufficient.

**Workflow:**
1. Initial retrieval and evaluation
2. If insufficient (confidence < 0.7), generate refinement queries from Evaluator feedback
3. Execute additional retrieval (up to 2 refinement queries)
4. Merge new documents with existing context
5. Re-evaluate merged context
6. Repeat up to 3 total iterations or until sufficient

**Convergence:** Prevents infinite loops with max iteration cap and minimum confidence threshold (0.7).

---

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI 0.127+**: High-performance async API framework with automatic OpenAPI documentation
- **Uvicorn**: ASGI server for production deployment
- **Pydantic 2.12+**: Data validation and settings management with type safety

### AI & Agent Framework
- **OpenAI GPT-4o-mini**: Primary LLM for agent reasoning (Planner, Evaluator, Synthesizer)
- **OpenAI Embeddings API**: `text-embedding-3-small` model for semantic vector generation
- **LangChain**: Text splitters (`RecursiveCharacterTextSplitter`) for intelligent chunking
- **Custom Agent Framework**: Base agent classes with reasoning trace capabilities

### Vector Database & Search
- **ChromaDB 1.3+**: Persistent vector store with cosine similarity search
  - *Why ChromaDB?* Lightweight, easy deployment, excellent for document-scale workloads (thousands to millions of chunks)
  - Persistent storage with automatic indexing
  - Efficient metadata filtering for multi-tenant support

### Relational Database
- **PostgreSQL 15**: Document metadata, chat history, and user sessions
- **SQLAlchemy 2.0+**: ORM with async support and declarative models
- **Alembic**: Database migrations with version control

### Memory & Caching
- **Redis 7.1+**: Session management with TTL-based expiration
  - Stores conversation history for multi-turn context
  - 1-hour session lifetime (configurable via `SESSION_TTL_SECONDS`)
  - Automatic cleanup of expired sessions

### Document Processing
- **PyMuPDF (fitz) 1.26+**: Superior PDF text extraction for multi-column academic papers
  - *Why PyMuPDF?* Handles complex layouts better than alternatives (pdfplumber, pypdf2)
  - Preserves reading order in multi-column documents
  - Word-level extraction flags for accurate spacing
- **LangChain Text Splitters**: Recursive character splitting with semantic boundary preservation

### Infrastructure & Deployment
- **Docker & Docker Compose**: Containerized deployment with PostgreSQL, Redis, and pgAdmin
- **Tenacity 9.1+**: Retry logic with exponential backoff for resilience
- **Python 3.13+**: Leverages latest Python performance improvements

---

## 📡 API Endpoints

### Document Management

#### Upload Documents
```http
POST /api/upload/files
Content-Type: multipart/form-data

Form Data:
  chat_id: integer (required) - Chat session to associate documents with
  files: file[] (required) - PDF files to upload
```

**Response:**
```json
{
  "results": [
    {
      "filename": "research_paper.pdf",
      "status": "success",
      "pages_processed": 12,
      "chunks_created": 48,
      "embeddings_generated": 48,
      "stored_in_vector_db": 48
    }
  ],
  "summary": {
    "total_files": 1,
    "successful": 1,
    "failed": 0,
    "total_chunks": 48
  }
}
```

#### List Documents
```http
GET /api/documents?chat_id={chat_id}
```

**Response:**
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "research_paper.pdf",
      "status": "completed",
      "created_at": "2026-01-08T10:30:00Z",
      "chat_ids": [1, 2]
    }
  ]
}
```

#### Delete Document
```http
DELETE /api/documents/{document_id}
```

### Chat & Query

#### Start Chat Session
```http
POST /api/chat/start
Content-Type: application/json

{
  "user_id": "user123",
  "chat_name": "AI Research Discussion"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "chat_id": 5,
  "user_id": "user123",
  "created_at": "2026-01-08T10:35:00Z",
  "expires_at": "2026-01-08T11:35:00Z"
}
```

#### Query Documents
```http
POST /api/chat/query
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "chat_id": 5,
  "query": "What are the main advantages of transformer architectures?"
}
```

**Response:**
```json
{
  "query": "What are the main advantages of transformer architectures?",
  "answer": "Based on the provided documents, transformer architectures offer several key advantages:\n\n1. **Parallelization**: Unlike RNNs, transformers can process all tokens simultaneously during training, significantly reducing training time.\n\n2. **Long-range Dependencies**: The self-attention mechanism allows transformers to capture relationships between distant tokens without the vanishing gradient problem.\n\n3. **Scalability**: Transformers scale efficiently with model size and data, enabling models with billions of parameters.\n\n[Sources: transformer_overview.pdf (p.3), attention_mechanisms.pdf (p.7)]",
  "sources": [
    {
      "document_id": "transformer_overview.pdf",
      "page_number": 3,
      "chunk_id": "a1b2c3d4-..."
    },
    {
      "document_id": "attention_mechanisms.pdf",
      "page_number": 7,
      "chunk_id": "e5f6g7h8-..."
    }
  ],
  "num_sources": 2,
  "plan": {
    "resolved_question": "What are the main advantages of transformer architectures?",
    "question_type": "pros_cons",
    "search_queries": [
      {"query": "transformer architecture advantages benefits", "top_k": 5}
    ]
  },
  "evaluation": {
    "is_sufficient": true,
    "confidence_score": 0.85,
    "missing_aspects": [],
    "suggested_followups": []
  },
  "refinement_summary": {
    "total_iterations": 1,
    "final_confidence": 0.85,
    "total_documents_retrieved": 5
  },
  "processing_summary": {
    "total_agents_used": 4,
    "agents_list": ["Planner", "Retriever", "Evaluator", "Synthesizer"],
    "total_reasoning_steps": 12,
    "refinement_iterations": 0
  },
  "agent_reasoning": [
    {
      "agent": "Planner",
      "step_type": "query_analysis",
      "description": "Classified as pros_cons question type",
      "timestamp": "2026-01-08T10:36:01.234Z"
    }
  ]
}
```

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running",
  "database": "healthy",
  "redis": "healthy",
  "vector_db_items": 1248,
  "settings": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "text-embedding-3-small",
    "session_ttl_seconds": 3600
  }
}
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.13+** ([Download](https://www.python.org/downloads/))
- **Docker & Docker Compose** ([Install Guide](https://docs.docker.com/get-docker/))
- **OpenAI API Key** ([Get API Key](https://platform.openai.com/api-keys))

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/multi-agent-research-assistant.git
cd multi-agent-research-assistant/backend
```

### Step 2: Environment Configuration
Create a `.env` file in the backend directory:

```bash
# .env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=100

# Database Configuration
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/multi-agent
DB_ECHO=false

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=document_chunks

# Text Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=50

# File Storage
UPLOAD_DIRECTORY=./pdfs

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
SESSION_TTL_SECONDS=3600
```

### Step 3: Start Infrastructure Services
```bash
cd docker
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis Stack (port 6379, Web UI on 8001)
- pgAdmin (port 5050)

### Step 4: Install Python Dependencies
```bash
cd ..  # back to backend directory
pip install -e .
```

### Step 5: Run Database Migrations
```bash
alembic upgrade head
```

### Step 6: Start the API Server

**Development Mode:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 7: Verify Installation
Navigate to `http://localhost:8000/docs` to access the interactive API documentation (Swagger UI).

---

## 💡 Usage Examples

### Example 1: Upload a Research Paper
```bash
curl -X POST "http://localhost:8000/api/upload/files" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "chat_id=1" \
  -F "files=@attention_is_all_you_need.pdf"
```

### Example 2: Simple Question
```bash
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "chat_id": 1,
    "query": "What is the self-attention mechanism?"
  }'
```

**Response:** Clear definition with page-level citations.

### Example 3: Complex Multi-Part Query

**Query:** "Compare the computational efficiency of transformers versus RNNs, and explain why transformers are preferred for large-scale models."

**Processing Summary:**
- Planner creates 4 targeted search queries
- Initial retrieval: 16 chunks, confidence 0.65 (insufficient)
- Refinement triggered: 2 additional queries
- Final confidence: 0.82 (sufficient)
- Answer generated with 4 source citations

**Sample Answer:**
```
Transformers demonstrate superior computational efficiency through massive 
parallelization during training—all tokens processed simultaneously vs 
RNN's sequential processing. This enables 10-100x training speedups on 
modern GPUs [transformer_analysis.pdf, p.12].

Despite higher memory footprint (O(n²) vs O(1)), transformers achieve 
higher throughput through batch processing and enable billion-parameter 
models that would be impractical with RNNs [scaling_laws.pdf, p.15].

[4 sources cited]
```

---

## 🔧 System Design & Data Flow

### Query Processing with Iterative Refinement

```
User Query
    │
    ├─> Session Validation
    │      • Check Redis for session_id
    │      • Retrieve conversation history
    │      • Extend session TTL
    │
    ├─> PLANNER AGENT
    │      • Analyze query with conversation context
    │      • Resolve "it", "this", "that" → specific entities
    │      • Classify question type
    │      • Generate 1-N search queries with top_k
    │
    ├─> RETRIEVER AGENT (Initial)
    │      • Execute similarity searches
    │      • Filter by chat's document collection
    │      • Retrieve top_k chunks per query
    │      • Merge and deduplicate results
    │
    ├─> EVALUATOR AGENT (Iteration 1)
    │      • Assess context sufficiency
    │      • Calculate confidence score
    │      • Identify gaps (missing aspects)
    │      • Generate suggested follow-ups
    │
    ├─> REFINEMENT CONTROLLER
    │      • If insufficient (confidence < 0.7):
    │         ├─> Generate refinement queries from gaps
    │         ├─> RETRIEVER AGENT (Iteration 2)
    │         ├─> Merge with previous context
    │         └─> EVALUATOR AGENT (Iteration 2)
    │      • Repeat up to 3 iterations total
    │      • Track refinement history
    │
    ├─> SYNTHESIZER AGENT
    │      • Generate answer from final context
    │      • Extract citations (doc_id, page, chunk_id)
    │      • Format response
    │      • Update conversation history (Redis + PostgreSQL)
    │
    └─> Response Assembly
           • Answer with citations
           • Processing summary (agents used, iterations)
           • Complete reasoning trace
           • Refinement metrics
```

### Citation Mechanism

Citations are automatically tracked with `{document_id, page_number, chunk_id}`, deduplicated by page, and verified by the Evaluator to ensure claims are grounded in retrieved context.

---

## ⚡ Performance Characteristics

### Response Times (Typical)
- **Simple queries** (single search, no refinement): 2-4 seconds
- **Complex queries** (multiple searches, 1 refinement iteration): 5-8 seconds
- **Maximum latency** (3 iterations, multiple searches): 10-15 seconds

**Bottlenecks:**
- LLM API calls: 1-2s per agent invocation
- Embedding generation: ~500ms per batch of 100 chunks
- Vector search: <100ms per query

### Scalability
- **Document Capacity**: Tested with up to 500 documents (~10,000 chunks) per chat
- **Concurrent Sessions**: Redis supports thousands of active sessions
- **Vector Database**: ChromaDB scales to millions of vectors on modest hardware

### Cost Estimates (OpenAI API)

**Per Document Upload (avg 20-page PDF):**
- Text extraction: Free (PyMuPDF)
- Chunking: Free (local processing)
- Embeddings: ~40 chunks × $0.00002/1K tokens ≈ $0.0008
- **Total: < $0.001 per document**

**Per Query:**
- Planner: ~500 tokens × $0.00015/1K tokens ≈ $0.000075
- Evaluator: ~800 tokens × $0.00015/1K tokens ≈ $0.00012
- Synthesizer: ~1500 tokens × $0.00015/1K tokens ≈ $0.000225
- **Total: ~$0.0004 per query** (without refinement)
- **With 2 refinement iterations: ~$0.0008 per query**

*Costs based on GPT-4o-mini pricing (January 2026). Adjust for different models.*

---

## 🛡️ Error Handling & Reliability

### Retry Mechanisms

**LLM API Calls** (Planner, Evaluator, Synthesizer):
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ConnectionError),
    reraise=True
)
```

**Vector Database Operations** (Retriever):
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
```

### Error Response Formats

**400 Bad Request** (Invalid Input):
```json
{
  "detail": "Query cannot be empty"
}
```

**404 Not Found** (Invalid Session/Chat):
```json
{
  "detail": "Invalid session or session expired"
}
```

**500 Internal Server Error** (Processing Failure):
```json
{
  "detail": "Failed to process query"
}
```

### Failure Handling

| **Scenario** | **Handling Strategy** |
|--------------|----------------------|
| PDF parsing fails | Return `FileProcessingError` with specific reason (corrupted file, no text, etc.) |
| Embedding API timeout | Retry 3 times with exponential backoff; fail request if all attempts fail |
| Vector DB disconnection | Retry with exponential backoff; return degraded health check status |
| LLM rate limit | Tenacity automatically handles with wait intervals |
| Session expired | Return 404 with clear message; user must create new session |
| Insufficient context after max iterations | Return partial answer with disclaimer + suggested follow-ups |

---

## ⚙️ Configuration & Environment

### Environment Variables

| **Variable** | **Default** | **Description** |
|--------------|-------------|-----------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key for embeddings and LLM |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `EMBEDDING_BATCH_SIZE` | `100` | Chunks per embedding API call |
| `DATABASE_URL` | `postgresql+psycopg2://...` | PostgreSQL connection string |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_db` | ChromaDB storage path |
| `CHROMA_COLLECTION_NAME` | `document_chunks` | Collection name |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `MAX_FILE_SIZE_MB` | `50` | Maximum PDF file size |
| `UPLOAD_DIRECTORY` | `./pdfs` | Local PDF storage |
| `REDIS_HOST` | `localhost` | Redis server host |
| `REDIS_PORT` | `6379` | Redis server port |
| `SESSION_TTL_SECONDS` | `3600` | Session expiration (1 hour) |

### Agent Configuration (Code-Level)

**Planner Config** ([app/models/agents.py](app/models/agents.py)):
```python
class PlannerConfig(BaseModel):
    model: str = "gpt-4o-mini"
    max_retries: int = 3
    max_history_records: int = 2  # Conversation turns to include
    temperature: float = 0.3
    max_tokens: int = 2000
```

**Refinement Controller** ([app/services/chat_service.py](app/services/chat_service.py)):
```python
max_refinement_iterations: int = 3
min_confidence_threshold: float = 0.7
```

### Development vs. Production Settings

**Development:**
```bash
# .env.development
DB_ECHO=true  # Log all SQL queries
UVICORN_RELOAD=true
LOG_LEVEL=DEBUG
```

**Production:**
```bash
# .env.production
DB_ECHO=false
UVICORN_WORKERS=4  # Multiple workers for concurrency
LOG_LEVEL=INFO
```

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app initialization, health check
│   ├── agents/                    # Multi-agent system
│   │   ├── base.py                # Abstract Agent and LLMAgent classes
│   │   ├── planner.py             # Planner agent (query analysis)
│   │   ├── retriver.py            # Retriever agent (vector search)
│   │   ├── evaluator.py           # Evaluator agent (context assessment)
│   │   ├── synthesizer.py         # Synthesizer agent (answer generation)
│   │   ├── refinement_controller.py # Iterative refinement logic
│   │   └── prompts.py             # Agent system prompts
│   ├── core/                      # Core infrastructure
│   │   ├── config.py              # Settings management (Pydantic)
│   │   ├── database.py            # ChromaDB client
│   │   └── relation_database.py   # PostgreSQL session management
│   ├── llm/
│   │   └── llm.py                 # OpenAI client initialization
│   ├── memory/
│   │   ├── redis_client.py        # Redis connection
│   │   └── session_store.py       # Session CRUD operations
│   ├── models/                    # SQLAlchemy & Pydantic models
│   │   ├── agents.py              # Agent configuration models
│   │   ├── chat.py                # Chat and Document ORM models
│   │   └── memory.py              # Conversation history models
│   ├── repositories/              # Data access layer
│   │   ├── chat_repository.py     # Chat CRUD operations
│   │   └── document_repository.py # Document CRUD operations
│   ├── routes/                    # API endpoints
│   │   ├── chat.py                # Chat session and query endpoints
│   │   └── files_router.py        # Document upload/management
│   ├── schema/                    # Request/response schemas
│   │   ├── chat.py                # Chat API schemas
│   │   ├── document.py            # Document API schemas
│   │   └── query.py               # Query API schemas
│   ├── services/                  # Business logic layer
│   │   ├── chat_service.py        # Query orchestration
│   │   ├── files_service.py       # PDF processing
│   │   ├── text_chunker.py        # Document chunking
│   │   ├── vector_embedings.py    # Embedding generation
│   │   ├── query_service.py       # Similarity search
│   │   └── prompt_generation.py   # Context formatting
│   └── exceptions/
│       └── document_exceptions.py # Custom exception classes
├── alembic/                       # Database migrations
│   ├── versions/                  # Migration scripts
│   └── env.py                     # Alembic configuration
├── docker/
│   └── docker-compose.yaml        # Infrastructure services
├── pyproject.toml                 # Dependencies
├── alembic.ini                    # Alembic config
└── README.md                      # This file
```

**Separation of Concerns:**
- **Routes**: HTTP request/response handling only
- **Services**: Business logic and agent orchestration
- **Repositories**: Database access (CRUD)
- **Agents**: AI-powered decision making and reasoning
- **Models**: Data structures (ORM + validation)

---

## 🚢 Deployment

### Local Deployment with Docker

1. **Build custom Docker image** (optional):
```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Update docker-compose.yaml**:
```yaml
services:
  backend:
    build: ../
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+psycopg2://user:password@postgres:5432/multi-agent
      - REDIS_HOST=redis-stack
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis-stack
    volumes:
      - ./pdfs:/app/pdfs
      - ./chroma_db:/app/chroma_db
```

3. **Deploy**:
```bash
docker-compose up -d
```

### Cloud Deployment

#### Railway / Render
1. Connect GitHub repository
2. Set environment variables (OpenAI API key, database URLs)
3. Deploy PostgreSQL and Redis add-ons
4. Configure health check endpoint: `/health`

#### AWS / GCP / Azure
1. **Compute**: Deploy on EC2/Compute Engine/App Service
2. **Database**: Use managed PostgreSQL (RDS/Cloud SQL/Azure Database)
3. **Cache**: Use managed Redis (ElastiCache/MemoryStore/Azure Cache)
4. **Storage**: Mount persistent volumes for `chroma_db` and `pdfs`
5. **Load Balancer**: Distribute traffic across multiple instances
6. **Auto-scaling**: Scale based on CPU/memory (target 70% utilization)

### Production Checklist
- [ ] Set `DB_ECHO=false` (disable SQL logging)
- [ ] Configure multiple Uvicorn workers (`--workers 4`)
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up monitoring (Prometheus, Datadog)
- [ ] Configure log aggregation (ELK stack, CloudWatch)
- [ ] Implement rate limiting (per user/session)
- [ ] Set up database backups (PostgreSQL + ChromaDB)
- [ ] Configure CORS policies
- [ ] Use secrets manager for API keys
- [ ] Test with load testing tools (Locust, k6)

---

## 🤝 Contributing & Development

### Extending the Agent System

To add a new agent:
1. Create agent class in [app/agents/](app/agents/) inheriting from `LLMAgent`
2. Add system prompt to [app/agents/prompts.py](app/agents/prompts.py)
3. Integrate into `ChatService.process_query()` orchestration
4. Use `self.add_reasoning_step()` to log decisions

### Customizing LLM Models

Modify `PlannerConfig` in [app/models/agents.py](app/models/agents.py) to change the model (e.g., `gpt-4` for higher quality) or use different models per agent in [app/services/chat_service.py](app/services/chat_service.py).

---

## 🔮 Future Enhancements

- **Real-time Streaming**: Server-Sent Events for live answer generation
- **Web Scraping Agent**: Fetch external sources when needed
- **OCR Integration**: Support scanned PDFs
- **Authentication**: Multi-user support with JWT
- **Analytics Dashboard**: Query metrics and agent performance
- **Custom Workflows**: User-configurable agent chains
- **Hybrid Search**: Combine semantic + keyword search (BM25)
- **Multi-language**: Support non-English documents

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 📧 Support

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Issues**: GitHub Issues

---

**Built for researchers, analysts, and knowledge workers who need intelligent document analysis at scale.**
