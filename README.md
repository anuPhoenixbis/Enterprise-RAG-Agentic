# Enterprise Agentic RAG

An enterprise-oriented **Agentic Retrieval-Augmented Generation (RAG)** system built with **LangGraph, FastAPI, Qdrant, Gemini Embeddings, Groq, Portkey, NeMo Guardrails, FlashRank, and RAGAS**.

The system is designed to answer technical questions from a controlled knowledge base while handling conversational queries, query planning, semantic retrieval, reranking, safety checks, response generation, and automated evaluation.

---

## 🚀 Overview

Traditional RAG pipelines usually follow a simple flow:

```text
Query → Retrieve → Generate

This project extends that architecture into an agentic RAG pipeline:

User Query
    │
    ▼
┌─────────────────────┐
│   NeMo Guardrails   │
│ Safety / Relevance  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   LangGraph Planner │
│ Intent + Query      │
│ Refinement           │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
Conversational  Technical
     │           │
     │           ▼
     │    ┌───────────────┐
     │    │ Gemini        │
     │    │ Embeddings    │
     │    └───────┬───────┘
     │            ▼
     │    ┌───────────────┐
     │    │    Qdrant     │
     │    │ Vector Search │
     │    └───────┬───────┘
     │            ▼
     │    ┌───────────────┐
     │    │   FlashRank   │
     │    │ Semantic      │
     │    │ Reranking     │
     │    └───────┬───────┘
     │            ▼
     └──────► Response Generation
                  │
                  ▼
             Final Answer

The project also includes a dedicated evaluation dashboard for measuring RAG quality using RAGAS-based metrics and deterministic tool-correctness checks.

✨ Key Features
🤖 Agentic RAG

Instead of blindly retrieving documents for every query, a LangGraph-based planner first determines whether a request is conversational or requires knowledge retrieval.

For technical questions, the planner can refine the user's query into a retrieval-oriented search query.

🧠 Semantic Retrieval

Documents are:

Parsed
Split into meaningful chunks
Embedded
Stored in Qdrant
Retrieved using vector similarity

The system retrieves multiple candidates before applying a dedicated reranking stage.

🎯 Semantic Reranking

Retrieved candidates are reranked using FlashRank to improve the relevance of the context passed to the final LLM.

Qdrant
  ↓
Top-K candidates
  ↓
FlashRank
  ↓
Most relevant context
  ↓
LLM
🛡️ NeMo Guardrails

The application contains an input/output safety layer that handles:

Off-topic requests
Prompt injection attempts
Jailbreak attempts
Greetings
Capability questions
Farewell interactions

The guardrail layer prevents irrelevant requests from entering the main RAG pipeline.

🌐 LLM Gateway

LLM requests are routed through Portkey to provide a centralized gateway layer for:

Model routing
Fallback strategies
Retry handling
Caching
Metadata
Observability
⚡ Groq Inference

The primary generation and planning models run through Groq's OpenAI-compatible API.

The project separates:

Production LLM usage
Planner/classification usage
Evaluation/judge usage

This prevents evaluation workloads from consuming the same API budget as the main application.

📊 RAG Evaluation

A dedicated Streamlit evaluation interface runs multiple experiments against a golden dataset.

Current evaluation metrics include:

Faithfulness
Answer Relevancy
Context Precision
Context Recall
Answer Correctness
Tool Correctness

The first five are evaluated using an LLM-based judge, while Tool Correctness uses a deterministic Jaccard-based comparison.

🔍 Observability

Pydantic Logfire is integrated across the application to trace:

User interactions
Guardrail checks
Planner decisions
Knowledge retrieval
Semantic reranking
LLM synthesis
Evaluation experiments

This makes latency and failure points visible across the pipeline.

🏗️ Architecture
1. Document Ingestion
Documents
   │
   ▼
Document Parsing
   │
   ▼
Chunking
   │
   ▼
Metadata
   │
   ▼
Gemini Embeddings
   │
   ▼
Qdrant Vector Database

The ingestion pipeline supports document formats including:

PDF
DOCX
PPTX
TXT
HTML

Chunks are stored together with their associated metadata before being embedded and inserted into the vector database.

2. Query Pipeline
                    User
                     │
                     ▼
             FastAPI /query
                     │
                     ▼
             NeMo Guardrails
                     │
             ┌───────┴────────┐
             │                │
         Rejected          Allowed
             │                │
             ▼                ▼
          Refusal        LangGraph Planner
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Conversational       Technical
                    │                   │
                    │                   ▼
                    │              Query Embedding
                    │                   │
                    │                   ▼
                    │                Qdrant
                    │                   │
                    │                   ▼
                    │              FlashRank
                    │                   │
                    └──────────┬────────┘
                               ▼
                         Response LLM
                               │
                               ▼
                         Final Response
🧩 LangGraph Agent

The core reasoning workflow is implemented using LangGraph.

The graph contains three primary nodes:

Planner
   │
   ├── CONVERSATIONAL ─────► Responder
   │
   └── Technical ──────────► Retriever
                                  │
                                  ▼
                              Responder
Planner

Determines whether the user's message:

Can be answered conversationally
Requires retrieval from the enterprise knowledge base

For technical queries, the planner also produces a refined retrieval query.

Retriever

Responsible for:

Embedding the query
Searching Qdrant
Retrieving candidate documents
Semantic reranking
Preparing the final context
Responder

Generates the final answer using:

Conversation history
Retrieved context
The user's current query
Enterprise-specific response instructions
🛡️ Guardrail Strategy

The application uses NeMo Guardrails before the main agentic pipeline.

Conceptually:

User Input
    │
    ▼
Guardrail Layer
    │
    ├── Off-topic ───────► Refuse
    │
    ├── Jailbreak ───────► Refuse
    │
    ├── Greeting ────────► Conversational Response
    │
    └── Valid Technical ► RAG Pipeline

The assistant is intended to operate within a defined enterprise technical domain rather than acting as a general-purpose chatbot.

📚 Knowledge Base

The knowledge base is separated into:

DATA/
├── true_data/
└── noisy_data/

This separation is used during ingestion and evaluation to experiment with retrieval quality and distinguish useful technical knowledge from irrelevant/noisy content.

🔎 Retrieval Pipeline

The retrieval process follows:

User Query
    │
    ▼
Query Refinement
    │
    ▼
Gemini Embedding
    │
    ▼
Qdrant Similarity Search
    │
    ▼
Candidate Documents
    │
    ▼
FlashRank Reranking
    │
    ▼
Top Relevant Context

The system intentionally performs retrieval followed by reranking rather than relying solely on vector similarity.

📈 Evaluation Framework

The project contains a separate Streamlit evaluation application:

evals/
├── app.py
├── pipeline.py
├── metrics.py
└── ...

The evaluation workflow is divided into multiple phases.

Phase 1 — Run the Live Pipeline

The golden dataset is executed against the current RAG pipeline.

The resulting data records:

User question
Actual response
Actual retrieved contexts
Tools called
Other pipeline outputs
Phase 2 — Evaluate RAG Quality

RAGAS evaluates generated responses against the golden dataset.

Metric	Purpose
Faithfulness	Measures whether the answer is supported by retrieved context
Answer Relevancy	Measures relevance of the answer to the user's question
Context Precision	Measures whether retrieved context is relevant
Context Recall	Measures whether required information was retrieved
Answer Correctness	Compares the generated answer with the reference answer
Tool Correctness	Compares expected and actually invoked tools

The evaluation judge uses a separate Groq API key so that evaluation workloads remain isolated from normal production inference.

🧪 Evaluation Design

The evaluation pipeline deliberately controls request volume to account for model API rate limits.

It processes samples sequentially and inserts cooldown periods between experiments.

Context is also truncated and limited before being passed to the evaluator:

Golden Dataset
      │
      ▼
Valid Samples
      │
      ▼
Context Truncation
      │
      ▼
RAGAS Metric
      │
      ▼
Groq Judge
      │
      ▼
Per-sample Scores
      │
      ▼
Pandas DataFrame
🗂️ Project Structure
RAG_chatbot/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── agents/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── nodes/
│   │       ├── planner.py
│   │       ├── retriever.py
│   │       └── responder.py
│   │
│   ├── gateway/
│   │   └── client.py
│   │
│   └── ...
│
├── evals/
│   ├── app.py
│   ├── pipeline.py
│   ├── metrics.py
│   └── ...
│
├── DATA/
│   ├── true_data/
│   └── noisy_data/
│
├── streamlit_app.py
├── requirements.txt
├── .python-version
├── .gitignore
└── README.md
⚙️ Tech Stack
Category	Technology
Backend	FastAPI
Agent Orchestration	LangGraph
LLM Inference	Groq
LLM Gateway	Portkey
Embeddings	Gemini Embeddings
Vector Database	Qdrant
Reranking	FlashRank
Guardrails	NeMo Guardrails
Evaluation	RAGAS
UI	Streamlit
Observability	Pydantic Logfire
Document Processing	Unstructured, PyPDF, python-docx, python-pptx, BeautifulSoup
Language	Python
🔐 Environment Variables

Create a .env file for local development.

Example:

GEMINI_API_KEY=

QDRANT_API_KEY=
QDRANT_CLUSTER_ENDPOINT=

GROQ_API_KEY=
GROQ_MODEL=
GROQ_MODEL_CLASSIFICATION=
GROQ_FALLBACK_MODEL=
GROQ_FALLBACK_API_KEY=

PORTKEY_API_KEY=
GROQ_SLUG_1=
GROQ_SLUG_2=

LOGFIRE_TOKEN=

JUDGE_GROQ=
JUDGE_MODEL=

Never commit .env or API keys to GitHub.

🛠️ Local Setup
1. Clone the repository
git clone <your-repository-url>
cd RAG_chatbot
2. Create a virtual environment
Windows
python -m venv .venv
.venv\Scripts\activate
Linux / macOS
python -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables

Create:

.env

and add the required API credentials.

▶️ Running the Application
Start the FastAPI backend
uvicorn app.main:app --reload

The API will be available at:

http://localhost:8000

Swagger documentation:

http://localhost:8000/docs
Start the Streamlit frontend
streamlit run streamlit_app.py

The application will open at:

http://localhost:8501
Start the Evaluation Dashboard
streamlit run evals/app.py

The evaluation dashboard will provide access to:

Phase 1 → Live pipeline execution
Phase 2 → RAGAS evaluation
🔬 Example Query Flow

Example technical query:

How does Kubernetes Horizontal Pod Autoscaling work?

The request goes through:

User
 ↓
NeMo Guardrails
 ↓
Planner
 ↓
Query Refinement
 ↓
Gemini Embedding
 ↓
Qdrant
 ↓
FlashRank
 ↓
Relevant Context
 ↓
Groq LLM
 ↓
Final Answer

A conversational query such as:

Hello

can bypass document retrieval:

User
 ↓
Guardrails
 ↓
Planner
 ↓
CONVERSATIONAL
 ↓
Responder
🎯 Design Goals

The project was built around several engineering goals:

Reliability

Use structured orchestration, model routing, fallback strategies, and observability rather than a single monolithic LLM call.

Retrieval Quality

Combine vector similarity with semantic reranking to improve the quality of context supplied to the generator.

Safety

Prevent irrelevant, malicious, or off-domain requests from reaching the core knowledge pipeline.

Observability

Trace individual stages of the application to identify latency and failures across the system.

Evaluability

Treat RAG quality as something that should be measured rather than assumed.

🚧 Current Limitations

This project is primarily intended as a local engineering and experimentation environment.

Some components, particularly local semantic reranking with FlashRank, can introduce significant CPU and model initialization overhead depending on the execution environment.

The evaluation layer also deliberately uses conservative request batching and cooldowns to operate within external model API rate limits.

🔮 Future Improvements

Potential future improvements include:

Persistent reranker/model initialization
Parallelized evaluation workflows
Better structured planner outputs
More robust intent classification
Retrieval score calibration
Hybrid keyword + vector retrieval
Multi-query retrieval
Improved evaluation datasets
Automated regression testing for RAG quality
Production-oriented deployment architecture
Evaluation tracking across model versions
📌 What This Project Demonstrates

This project goes beyond a basic "chatbot + vector database" implementation.

It demonstrates practical experience with:

RAG
├── Document ingestion
├── Chunking
├── Embeddings
├── Vector databases
├── Semantic retrieval
├── Reranking
│
Agentic Systems
├── LangGraph
├── Query planning
├── Conditional routing
└── Conversation memory
│
LLM Engineering
├── Groq
├── Portkey
├── Model fallback
└── Prompt orchestration
│
AI Safety
├── NeMo Guardrails
├── Prompt injection handling
└── Off-topic detection
│
Evaluation
├── RAGAS
├── Golden datasets
├── LLM-as-a-Judge
└── Tool correctness
│
Observability
└── Pydantic Logfire
📄 License

This project is intended for educational, experimental, and portfolio purposes.


### One change I'd make for your GitHub presentation

For the **very top of the README**, I'd add a compact architecture banner immediately under the title, something like:

```markdown
> **Enterprise Agentic RAG** — A LangGraph-powered RAG system with Qdrant retrieval, FlashRank reranking, N
