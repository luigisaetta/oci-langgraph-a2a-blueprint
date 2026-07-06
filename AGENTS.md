# AGENTS.md

This project contains a blueprint and a set of guidelines for building and deploying a LangGraph agent on Oracle Cloud Infrastructure as an A2A-compatible server.

## Project Guidelines

- All documentation and Markdown files must always be written in English.
- Specifications must be written before implementation and stored under the `specs/` directory.
- Code must be generated only after the relevant specification exists.
- Implemented code must conform to the approved specification.
- The repository must remain focused on the blueprint goal: deploy a LangGraph agent on OCI and expose it through an A2A-compatible server interface.
- A2A protocol behavior, agent card metadata, task lifecycle, request and response payloads, and error handling must be specified before implementation.
- OCI deployment choices, required services, IAM assumptions, networking requirements, configuration, and runtime environment variables must be documented in the relevant specification before implementation.
- Python code must be formatted with `black`.
- Python code must be checked with `pylint`.
- New functionality must include unit tests written with `pytest`.
- Unit tests must provide sufficient coverage, with a target above 80%.
- Tests must be executed in the project Conda environment for this repository.
- Significant features, fixes, refactorings, specification updates, deployment changes, and documentation updates must be recorded in `CHANGELOG.md` under the current date.
- Done means: specification written or updated, code formatted, tests written, pylint checks completed, tests executed, and all test and pylint issues resolved.

## Python Code Conventions

Every Python source file must start with a multiline header using this format:

```python
"""
Author: L. Saetta
Date last modified: YYYY-MM-DD
License: MIT
Description: Brief description of the responsibilities and functions contained in this file.
"""
```

Use the actual modification date when creating or updating a Python source file.

All generated Python code must include accurate docstrings for modules, classes, methods, and functions where applicable. Docstrings must follow the Google Python docstring format and clearly describe purpose, arguments, return values, raised exceptions, and relevant behavior.

## Human Readability and Maintainability

Code generated for this repository must be optimised for human readability first.

Generated code must be easy to read, review, test, and maintain by a human engineer. Prefer clear structure and explicit intent over cleverness, dense abstractions, or overly compact expressions.

Follow these principles:

- Use descriptive names for modules, classes, functions, methods, variables, and tests.
- Keep functions focused on one clear responsibility.
- Prefer straightforward control flow over deeply nested logic.
- Extract helpers only when they reduce real complexity or meaningful duplication.
- Keep public behavior easy to trace from A2A request input to LangGraph execution and A2A response output.
- Make error handling explicit and predictable.
- Avoid hidden side effects and implicit global state.
- Keep configuration access centralized and easy to audit.
- Keep OCI-specific integration code isolated from core agent and protocol logic where practical.
- Use comments sparingly, only when they clarify non-obvious decisions or complex logic.
- Preserve consistency with the existing code style and project structure.
- Write tests that describe behavior clearly and can be understood as executable documentation.

Readable code is part of the quality bar for this project. A change is not considered complete if it works technically but is unnecessarily difficult to understand or maintain.

## Spec-Driven Development Workflow

1. Write or update the specification in `specs/`.
2. Review the specification for scope, behavior, acceptance criteria, and test expectations.
3. Implement the code according to the specification.
4. Add or update unit tests.
5. Run formatting, linting, and tests.
6. Fix all issues before considering the work done.

## A2A and LangGraph Design Expectations

- Treat the A2A server contract as a stable public interface.
- Keep protocol schemas, request validation, response serialization, and task status mapping explicit and tested.
- Keep LangGraph graph construction, node behavior, state definitions, and tool integrations documented in specifications.
- Prefer deterministic and testable agent behavior in examples.
- Keep sample prompts, model settings, and OCI configuration visible and easy to change.
- Never hard-code secrets, tenancy-specific identifiers, API keys, private endpoints, or local machine paths.
- Provide local execution instructions and OCI deployment instructions whenever a feature affects runtime behavior.
