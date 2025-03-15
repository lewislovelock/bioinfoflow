# BioinfoFlow Web UI Blueprint

This blueprint outlines the development plan for the BioinfoFlow web UI, a tool for managing bioinformatics workflows. It is designed to guide the implementation using **FastAPI** for the backend and a modern frontend stack featuring **TypeScript**, **Next.js**, **React**, **Shadcn UI**, **Radix UI**, and **Tailwind CSS**. This document is intended for use with Cursor IDE and Claude Sonnet to ensure consistent and efficient coding.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Backend (FastAPI)](#backend-fastapi)
   - [API Endpoints](#api-endpoints)
   - [Data Models](#data-models)
   - [Error Handling](#error-handling)
3. [Frontend (Next.js, React, TypeScript)](#frontend-nextjs-react-typescript)
   - [Page Structure](#page-structure)
   - [Component Breakdown](#component-breakdown)
   - [Styling and UI](#styling-and-ui)
   - [State Management](#state-management)
4. [Development Guidelines](#development-guidelines)
   - [Coding Standards](#coding-standards)
   - [Testing](#testing)
   - [Documentation](#documentation)
5. [Next Steps for Claude Sonnet](#next-steps-for-claude-sonnet)

---

## Project Overview
The BioinfoFlow web UI aims to deliver an intuitive interface for managing bioinformatics workflows. The Minimum Viable Product (MVP) will focus on the following core features:
- **Uploading/selecting workflows**: Users can upload workflow YAML files or choose from existing ones.
- **Running workflows**: Start a workflow with basic configuration options.
- **Monitoring progress**: Display real-time status updates for running workflows.
- **Viewing results**: Show workflow outputs and logs.

The backend will use **FastAPI** for its speed and automatic API documentation, while the frontend leverages **Next.js** for server-side rendering, **React** for a component-based UI, and **TypeScript** for type safety. The UI will be styled with **Shadcn UI**, **Radix UI**, and **Tailwind CSS** for a modern, responsive design.

---

## Backend (FastAPI)

### API Endpoints
Build a RESTful API with the following endpoints to support the MVP:
- **`POST /workflows`**: Upload a workflow YAML file.
  - Request: Workflow file (multipart/form-data).
  - Response: Workflow ID and metadata.
- **`GET /workflows`**: List all available workflows.
  - Response: Array of workflow metadata (ID, name, etc.).
- **`POST /runs`**: Start a new workflow run.
  - Request: Workflow ID and optional parameters.
  - Response: Run ID and initial status.
- **`GET /runs/{run_id}`**: Get details of a specific run.
  - Response: Run status, progress, and metadata.
- **`GET /runs/{run_id}/logs`**: Retrieve logs for a specific run.
  - Response: Log text or structured log data.

### Data Models
Use **Pydantic** to define request and response schemas:
- `Workflow`: ID, name, file path, creation date.
- `Run`: ID, workflow ID, status (e.g., "pending", "running", "completed", "failed"), start time, end time.
- `Log`: Run ID, timestamp, message.

These models ensure data validation and generate automatic API docs via FastAPI.

### Error Handling
- Use FastAPI’s exception handlers to return consistent JSON error responses (e.g., `{"error": "Invalid YAML format"}`).
- Handle common errors: invalid workflow files, missing inputs, or server issues.
- Log errors for debugging using Python’s `logging` module.

---

## Frontend (Next.js, React, TypeScript)

### Page Structure
Organize the app using Next.js pages for routing:
- **`/`**: Home page with a list of workflows (`WorkflowList`).
- **`/runs/[run_id]`**: Run details page showing status (`RunStatus`) and logs (`LogViewer`).
- **`/workflows/new`**: Upload and configure a new workflow (`WorkflowRunner`).

### Component Breakdown
Create reusable React components:
- **`WorkflowList`**: Displays a table or grid of workflows with options to select or run.
- **`WorkflowRunner`**: Form to upload a workflow or start a run with input options.
- **`RunStatus`**: Progress bar or status indicator for a running workflow.
- **`LogViewer`**: Scrollable log display with filtering or formatting options.

### Styling and UI
Leverage the following libraries for a polished, responsive UI:
- **Shadcn UI**: Use pre-built components (e.g., buttons, forms) customized to fit the app’s design.
- **Radix UI**: Implement accessible primitives (e.g., modals, dropdowns) where needed.
- **Tailwind CSS**: Apply utility classes for layout, spacing, and typography.

Ensure the UI adapts to different screen sizes (mobile, tablet, desktop).

### State Management
For the MVP, use React’s built-in hooks:
- **`useState`**: Manage local component state (e.g., form inputs).
- **`useEffect`**: Fetch data from the API (e.g., workflow list, run status).
- **`useContext`**: Share global state (e.g., current run ID) if needed.

For future complexity, consider **Zustand** or **Redux**.

---

## Development Guidelines

### Coding Standards
- **Frontend**: Use camelCase for variables, PascalCase for components, and TypeScript for all code.
- **Backend**: Follow PEP 8 for Python (e.g., snake_case for variables).
- Keep functions and components small and focused.

### Testing
- **Backend**: Use `pytest` for unit tests (e.g., API endpoint behavior) and integration tests (e.g., database interactions).
- **Frontend**: Use `Jest` and `React Testing Library` to test components and API calls.
- Aim for 80%+ coverage of critical paths.

### Documentation
- **Backend**: Add docstrings to FastAPI routes and Pydantic models.
- **Frontend**: Use JSDoc comments for components and utility functions.
- Keep this `BLUEPRINT.md` updated with progress and changes.

---

## Next Steps for Claude Sonnet
Hey Claude! This blueprint is your guide to help me build the BioinfoFlow web UI. Here’s how you can assist:

1. **Backend Setup**:
   - Create a FastAPI app with the listed endpoints.
   - Define Pydantic models for workflows, runs, and logs.
   - Suggest a simple file-based or SQLite database setup for the MVP.

2. **Frontend Kickoff**:
   - Set up a Next.js project with TypeScript, Shadcn UI, Radix UI, and Tailwind CSS.
   - Scaffold the page structure (`/`, `/runs/[run_id]`, `/workflows/new`).
   - Build the `WorkflowList` component with a mock API call.

3. **Integration**:
   - Help me connect the frontend to the backend using `fetch` or `axios`.
   - Suggest how to poll the `/runs/{run_id}` endpoint for status updates.

Start with the backend endpoints or the frontend setup—your choice! Let me know if you need clarification or want to focus on a specific part first. Let’s build this step by step!

---