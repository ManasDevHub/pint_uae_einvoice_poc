---
title: UAE PINT AE E-Invoice Engine
emoji: 🚀
colorFrom: blue
colorTo: sky
sdk: docker
pinned: false
---

# UAE PINT AE E-Invoicing Validation Engine

Enterprise-grade validation engine aligned with **UAE PINT AE** mandatory field requirements. This platform provides real-time validation, batch processing, and analytics for e-invoice compliance.

## 🚀 Deployment (Hugging Face Spaces)

This repository is configured for automatic deployment on [Hugging Face Spaces](https://huggingface.co/spaces) using Docker.

### Features
- **Zero CORS**: Unified FastAPI + React architecture.
- **Persistent History**: SQLite database persists without a credit card.
- **Free 24/7**: No-cost hosting on basic hardware.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React (Vite)
- **Container**: Docker (Multi-stage)
- **Database**: SQLite (managed via SQLAlchemy)

## 📂 Project Structure
- `app/`: FastAPI application logic and API endpoints.
- `frontend/`: React components and dashboard UI.
- `rules/`: Compliance rules and business logic for UAE PINT AE.
- `data/`: Sample payloads and reference data (includes templates).
- `scripts/`: Manual test scripts and utility tools.
- `archive/`: Old logs and temporary binaries (like ngrok).

---
*Developed for technical and functional compliance with the UAE E-Invoicing mandate.*
