# Project: Analyser

This repository contains a tool for extracting nutrition and amino acid information from protein powder labels, consisting of a Python CLI/backend and a Next.js frontend.

## 🛠 Build, Lint, & Test

### Python Backend
*   **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -e .[dev]
    ```
*   **Run CLI:**
    ```bash
    python cli.py --help
    ```
*   **Run Tests:**
    *   **Run all tests:** `pytest`
    *   **Run a specific test file:** `pytest tests/test_extractor.py`
    *   **Run a single test case:** `pytest tests/test_extractor.py::TestNutritionExtractor::test_profile_type`
    *   **Run with output:** `pytest -s`

### Frontend (`/frontend`)
*   **Install Dependencies:**
    ```bash
    cd frontend && npm install
    ```
*   **Run Development Server:**
    ```bash
    cd frontend && npm run dev
    ```
*   **Lint:**
    ```bash
    cd frontend && npm run lint
    ```
*   **Build:**
    ```bash
    cd frontend && npm run build
    ```

## 📐 Code Style & Conventions

### Python (Backend)
*   **Style Guide:** Follow **PEP 8** standards.
*   **Formatting:**
    *   Use 4 spaces for indentation.
    *   Limit line length to ~88-100 characters (follow surrounding code).
*   **Imports:**
    *   Group imports: Standard library -> Third-party -> Local application.
    *   Use absolute imports for project modules (e.g., `from extractors import ...`).
*   **Type Hinting:**
    *   **Mandatory** for function arguments and return values.
    *   Use `typing` module (e.g., `Optional`, `List`, `Dict`) or modern syntax (`|`, `list[]`) where supported (Project requires Python >=3.10).
*   **Naming:**
    *   Variables/Functions: `snake_case`
    *   Classes: `PascalCase`
    *   Constants: `UPPER_CASE`
*   **File Paths:**
    *   **CRITICAL:** ALWAYS use `pathlib.Path` instead of string manipulation (os.path) for file paths.
*   **Docstrings:**
    *   Use Google-style docstrings for functions and classes.
    *   Include a brief description, arguments, and return values.
*   **Error Handling:**
    *   Use specific exceptions (e.g., `click.ClickException`, `ValueError`).
    *   Use `try/except` blocks where external failures (IO, API) are expected.

### TypeScript / React (Frontend)
*   **Style Guide:** Follow standard React/Next.js conventions.
*   **Naming:**
    *   Components: `PascalCase` (e.g., `ProductCard.tsx`)
    *   Functions/Variables: `camelCase`
    *   Files: `kebab-case` or `PascalCase` matching the component name.
*   **Types:**
    *   Use strict TypeScript types. Avoid `any` whenever possible.
    *   Define interfaces for props and data structures.
*   **Styling:**
    *   Use **Tailwind CSS** classes (inferred from dependencies).
*   **State Management:**
    *   Prefer React Server Components for data fetching where appropriate.

## 🤖 Agent Workflow
*   **Context First:** Before making changes, search for similar implementations to match the existing pattern.
*   **Validation:**
    *   Backend: Always run `pytest` after modifying Python logic.
    *   Frontend: Run `npm run lint` and verify the build if working on UI.
*   **Dependencies:**
    *   Do not add new dependencies without checking if an existing library serves the purpose.
    *   If adding a Python dependency, update `pyproject.toml` (and `requirements.txt` if used for lock-file purposes).
*   **Refactoring:**
    *   Keep functions small and focused.
    *   Extract complex logic into helper functions or classes.

## 🔍 Key Directories
*   `cli.py`: Main entry point for the CLI.
*   `extractors/`: Core logic for data extraction (Nutrition, Amino Acids).
*   `scorer.py`: Logic for scoring protein powders (Cut/Bulk/Clean modes).
*   `frontend/app/`: Next.js App Router pages.
*   `tests/`: Pytest test suite.
