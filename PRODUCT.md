# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are medical students practicing clinical reasoning and medical teachers supervising training. Students need a safe virtual patient environment to practice inquiry, differential diagnosis, examination selection, guideline evidence lookup, and communication. Teachers need class-level scoring, common missing points, citation accuracy, and report summaries.

## Product Purpose

“临思智训” is an AI standardized patient clinical reasoning training platform for medical education. It is not used for real clinical diagnosis. It helps students practice with virtual teaching cases, receive process scoring, inspect traceable guideline citations, and generate training reports.

## Positioning

The product turns AI+medicine interdisciplinary work into a usable teaching workflow: PatientAgent simulates scripted virtual patients, RetrievalAgent retrieves guideline evidence, ScoringAgent evaluates clinical thinking, SafetyAgent enforces education-only boundaries, and ReportAgent closes the training loop.

## Operating Context

The project lives at `D:\cc项目\ai+medicine`. The frontend is Vue 3, TypeScript, Vite, HTML, CSS, and JavaScript. The backend is Python with FastAPI, a Flask auxiliary module, LangChain-ready RAG structure, Milvus and ChromaDB adapter placeholders, TTS placeholders, Neo4j placeholders, and mock medical education data.

## Capabilities and Constraints

Confirmed capabilities include AI standardized patient chat, default “急诊胸痛” case, controlled patient replies from case scripts, clinical reasoning scoring, missing-point detection, traceable guideline knowledge base, teacher dashboard, training report, Agent workflow, RAG skeleton, and medical education knowledge graph.

Constraint: all cases are virtual teaching cases. The platform must not contain real patient data and must not generate real diagnostic or treatment advice.

## Evidence on Hand

- `data/cases.json`: virtual teaching cases.
- `data/guidelines.json`: guideline, textbook, and consensus mock knowledge sources.
- `data/teacher_dashboard.json`: class-level teaching dashboard metrics.
- `data/medical_kg.json`: medical education knowledge graph mock data.
- `backend/app/main.py`: FastAPI endpoints for training, scoring, reports, RAG, and graph.

## Product Principles

- Make training usable before explaining architecture.
- Keep AI patient behavior constrained by virtual case scripts.
- Always expose citations and safety notes beside feedback.
- Score the learning process, not only the final answer.
- Give teachers a feedback loop they can act on.

## Accessibility & Inclusion

The interface uses Chinese text, high contrast, keyboard-reachable controls, responsive layouts, non-color-only warning text, and reduced-motion-friendly animation.
