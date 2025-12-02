# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project Context: Rail Transit Staff AI Assessment System

## 1. Tech Stack & Environment
- **Backend**: Python 3.9+, Django 4.x, Django REST Framework (DRF).
- **Database**: SQLite 3 (Strictly used for dev & mvp).
- **Frontend**: Vue 3, Vite, Element Plus, ECharts, Axios.
- **Style**: PEP 8 (Python), Prettier/ESLint (JS/Vue).

## 2. Backend Guidelines (Django)
- **Architecture**:
  - Follow "Fat Models, Thin Views" or use a dedicated `services/` layer for complex logic (e.g., Exam Generation).
  - Use **Class-Based Views (CBVs)** or **ViewSets** for API endpoints.
- **Models**:
  - All models MUST inherit from a base abstract model with `created_at` and `updated_at`.
  - Use `related_name` explicitly in ForeignKeys.
  - JSONField is permitted for `Question.options`.
- **API**:
  - Use DRF `ModelSerializer`.
  - Return standard HTTP status codes (200, 201, 400, 401, 404).
  - URLs must follow RESTful conventions (e.g., `POST /api/exam/generate/`).

## 3. Frontend Guidelines (Vue 3)
- **Syntax**: MUST use **Composition API** with `<script setup lang="ts">`.
- **UI Library**: Use **Element Plus** for all standard components.
- **State**: Use `ref` for primitives, `reactive` for objects.
- **HTTP**: Encapsulate Axios requests in `src/api/` modules, strictly typed.

## 4. Key Business Logic (Constraints)
- **Exam Generation**:
  - Logic: 50% Weak Tags (<60 score) + 30% Random + 20% New.
  - Constraint: Exclude questions answered by user in last 24h.
- **Scoring & Profiling**:
  - Formula: `New_Score = (Old_Score * 0.7) + (Current_Accuracy * 100 * 0.3)`.
  - Trigger: Execute capability profile update immediately after `ExamPaper` submission.

## 5. Directory Structure
```text
backend/
  apps/
    users/       # Auth & User Profile
    core/        # Questions, Tags, Exam Logic
    analysis/    # Capability Profile & ECharts Data
  config/        # settings.py, urls.py

frontend/
  src/
    api/         # Axios wrappers
    components/  # Reusable UI
    views/       # Page views (Login, Dashboard, Exam)
    stores/      # Pinia stores (User session)