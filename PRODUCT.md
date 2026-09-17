# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Medical students study 3D anatomy, identify structures and complete quizzes. Teachers manage materials and exam settings. Administrators approve teacher accounts and control Skill activation, role permissions and hourly usage budgets.

## Product Purpose

“临思智训” focuses on 3D anatomy observation, traceable textbook evidence, knowledge relationships and practice feedback. It is for education and competition demonstrations, not diagnosis, treatment or clinical decision support.

## Positioning

AnatomyTutor links resources through three read-only Skills: model structure search, textbook retrieval and anatomy graph queries. The current implementation is bounded local tool orchestration, not autonomous LLM reasoning. Skills remain disabled until an administrator approves them.

## Operating Context

Vue 3, TypeScript, Vite, Three.js and FastAPI. SQLite stores authentication sessions and Skill configuration/call records. JSON and local assets store teaching content, model metadata and quiz caches. Earlier clinical training, RAG, voice and digital-human modules remain compatibility or experimental components, not the primary product story.

## Capabilities and Constraints

Implemented: interactive 3D anatomy, structure highlighting, textbook lookup, anatomy graph browsing, configurable quizzes with server-side grading, email registration, teacher approval, administrator-controlled Skills and authenticated anatomy tool orchestration. Some dashboards and learning-review data remain demonstrations. Graph hierarchy is not a verified spatial, vascular or innervation model. Learning effectiveness still requires evaluation.

Constraint: all cases are virtual teaching cases. The platform must not contain real patient data and must not generate real diagnostic or treatment advice.

## Evidence on Hand

- `frontend/public/anatomy/atlas.json` and `organs.json`: model structure sources.
- `data/anatomy_term_glossary.json`: bilingual terminology.
- `backend/app/knowledge_graph_service.py`: anatomy hierarchy built from those sources.
- `backend/app/services/anatomy_skills.py`: read-only retrieval adapters.
- `backend/app/services/skill_registry.py`: persisted permissions and usage accounting.
- `backend/tests/test_skills.py`: governance, concurrency and API regression tests.

## Product Principles

- Keep anatomy learning as the primary experience.
- Show actual evidence and real tool-call outcomes, not invented traces.
- Treat retrieved text as data, not executable instructions.
- Keep administrators in control of capability activation and permissions.
- Show missing evidence explicitly instead of fabricating explanations.
- Preserve server-side answers and grade students on the server.

## Accessibility & Inclusion

The interface uses Chinese text, high contrast, keyboard-reachable controls, responsive layouts, non-color-only warning text, and reduced-motion-friendly animation.
