<h1 align="center">

Production Reliability for LLM Applications

</h1>

<p align="center">

An end-to-end AI Quality Engineering project demonstrating how to transform an unstable Large Language Model (LLM) application into a production-ready system through evaluation, root cause analysis, reliability engineering, guardrails, and production validation.

</p>

<p align="center">

<img src="https://img.shields.io/badge/Python-3.12-blue?logo=python"/>
<img src="https://img.shields.io/badge/FastAPI-Production-green?logo=fastapi"/>
<img src="https://img.shields.io/badge/React-Frontend-61DAFB?logo=react"/>
<img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-black"/>
<img src="https://img.shields.io/badge/AI%20Quality%20Engineering-orange"/>
<img src="https://img.shields.io/badge/Reliability%20Engineering-success"/>
<img src="https://img.shields.io/badge/License-MIT-success"/>

</p>

---

# 🎥 Project Walkthrough

> Watch the complete engineering workflow — from identifying probabilistic instability to validating a production-ready AI system.

<p align="center">

[![Watch the Full Walkthrough](./assets/video-thumbnail.png)](https://youtube.com/YOUR_VIDEO)

</p>

---

# Project Overview

Modern AI applications powered by Large Language Models are inherently **probabilistic**.

Unlike traditional software, identical inputs do not always produce identical outputs. The same request may generate different intent classifications, confidence scores, routing decisions, and responses, creating operational risks that cannot be addressed through conventional software testing alone.

This project demonstrates a complete **AI Quality Engineering** workflow for measuring, explaining, improving, protecting, and validating the operational reliability of LLM-based systems before production deployment.

Rather than focusing on model development, this repository focuses on **engineering practices required to operate AI systems safely and reliably at scale.**

---

# Why This Project Exists

Imagine you're responsible for an AI application serving thousands of users every day.

A production incident is reported.

Identical user requests begin producing different behaviors.

Some requests are routed correctly.

Others are routed somewhere else.

Some receive different responses.

Others cannot even be classified with sufficient confidence.

At scale, this leads to:

- Increased operational costs
- Incorrect routing decisions
- SLA violations
- Inconsistent customer experiences
- Reduced trust in AI systems

This project demonstrates how AI Quality Engineering can systematically investigate, explain, and solve this class of production problems.

---

# Engineering Workflow

The project reproduces a real production incident and progressively transforms an unstable AI system into a production-ready application.

```text
                 Production Incident
                         │
                         ▼
            Situation 01 — Evaluation
                         │
                         ▼
      Situation 02 — Root Cause Analysis
                         │
                         ▼
   Situation 03 — Reliability Engineering
                         │
                         ▼
           Situation 04 — Guardrails
                         │
                         ▼
      Situation 05 — Production Quality
                         │
                         ▼
                Production Ready
```

---

# Engineering Pipeline

| Situation | Goal | Primary Outcome |
|-----------|------|-----------------|
| **Situation 01 — Evaluation** | Measure probabilistic behavior | Objective evidence of operational instability |
| **Situation 02 — Root Cause Analysis** | Explain why instability exists | Prompt Ambiguity identified as the primary root cause |
| **Situation 03 — Reliability Engineering** | Improve repeatability and predictability | Consistency increased from ~36% to over 90% |
| **Situation 04 — Guardrails** | Prevent future regressions | Multi-layer production protection |
| **Situation 05 — Production Quality** | Validate production readiness | System approved for production deployment |

---

# System Architecture

</p>

The architecture intentionally separates the **unstable baseline application** from the engineering workflow responsible for measuring, improving, protecting, and validating production behavior.

The project is composed of:

- React Frontend
- FastAPI Backend
- Intent Classification Engine
- Routing Engine
- Evaluation Framework
- Reliability Layer
- Guardrails Engine
- Production Quality Assessment
- Executive Dashboard

Each engineering situation builds upon the previous one, following the same workflow commonly adopted by mature AI engineering teams.

---

# Repository Structure

```text
production-reliability-for-llm-applications
│
├── unstable-ai-router/
│   ├── frontend/                 # React application
│   └── backend/                  # FastAPI backend
│
├── situation-01-evaluation/      # Measure instability
│
├── situation-02-root-cause-analysis/
│                                 # Identify causal factors
│
├── situation-03-reliability-engineering/
│                                 # Improve system reliability
│
├── situation-04-guardrails/      # Prevent regressions
│
├── situation-05-production-quality/
│                                 # Production readiness assessment
│
├── executive-dashboard/          # Consolidated executive metrics
│
├── project_metrics.json          # Single source of truth
│
├── FINAL_PROJECT_ASSESSMENT.md   # Final engineering assessment
│
└── README.md
```

---

# Engineering Philosophy

Traditional software is deterministic.

LLM-based systems are probabilistic.

Because of that, the engineering challenge shifts from validating whether responses are simply **right or wrong** to controlling acceptable boundaries of:

- Predictability
- Repeatability
- Reliability
- Observability
- Operational Safety

The objective is **not** to eliminate probabilistic behavior.

The objective is to reduce variability to an operationally acceptable level, making AI systems predictable, explainable, and reliable enough for production use.

---

# Quick Start

## Prerequisites

Before running the project, make sure you have:

- Python 3.12+
- Node.js 20+
- npm
- Git

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/production-reliability-for-llm-applications.git

cd production-reliability-for-llm-applications
```

Install the frontend dependencies:

```bash
cd unstable-ai-router/frontend

npm install
```

Install the backend dependencies:

```bash
cd ../backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Configure your environment:

```bash
cp .env.example .env
```

Then add your OpenAI API credentials.

---

# Running the Application

Start the backend:

```bash
npm run backend
```

Start the frontend:

```bash
npm run frontend
```

Frontend

```
http://localhost:5173
```

Backend

```
http://localhost:8000
```

---

# Running the Engineering Workflow

Each situation represents a different engineering phase.

Run them individually:

```bash
npm run situation-01
```

Evaluation

---

```bash
npm run situation-02
```

Root Cause Analysis

---

```bash
npm run situation-03
```

Reliability Engineering

---

```bash
npm run situation-04
```

Guardrails

---

```bash
npm run situation-05
```

Production Quality Assessment

---

Or execute the complete engineering workflow:

```bash
npm run situations
```

Generate the Executive Dashboard:

```bash
npm run dashboard
```

---

# Engineering Results

The project starts with an intentionally unstable AI application and progressively transforms it into a production-ready system.

| Metric | Before | After |
|---------|-------:|------:|
| Consistency Rate | ~36% | **92%+** |
| Reliability Score | 28 / 100 | **91 / 100** |
| Production Readiness | ❌ Not Ready | ✅ Production Ready |
| Root Cause Visibility | Unknown | Fully Explained |
| Guardrails | None | Multi-layer Protection |
| Production Assessment | Failed | Approved |

---

# Technology Stack

### Backend

- Python
- FastAPI
- OpenAI API

### Frontend

- React
- TypeScript
- Vite

### AI Engineering

- Prompt Engineering
- Intent Classification
- Routing Engine
- Reliability Engineering
- Root Cause Analysis
- Production Guardrails
- LLM Evaluation

### Reports & Visualization

- Matplotlib
- JSON Reports
- Markdown Reports
- Executive Dashboard

---

# Project Scope

This repository intentionally focuses on **production reliability** rather than model development.

| Included | Not Included |
|----------|--------------|
| AI Quality Engineering | Model Training |
| Reliability Engineering | Fine-Tuning |
| Root Cause Analysis | Dataset Creation |
| LLM Evaluation | Model Architecture |
| Production Guardrails | RAG Implementation |
| Production Validation | Model Optimization |

---

# Key Takeaways

Building AI applications is becoming increasingly accessible.

Building **reliable AI applications** remains an engineering challenge.

This project demonstrates that production AI systems should be engineered using the same principles applied to any mission-critical software:

- Measure before changing.
- Explain before fixing.
- Stabilize before deploying.
- Protect against regressions.
- Continuously validate production readiness.

Reliable AI is not achieved through better prompts alone.

It is achieved through disciplined engineering.

---

# Connect With Me

<a href="https://www.linkedin.com/in/nicolas-barth">
<img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white"/>
</a>
