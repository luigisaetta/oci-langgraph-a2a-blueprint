# AGENTS.md

This repository contains a blueprint and implementation guidance for building and deploying a LangGraph agent on Oracle Cloud Infrastructure as an A2A-compatible server.

## Repository purpose

Keep the repository focused on one goal: deploy a LangGraph agent on OCI and expose it through an A2A-compatible server interface.

All changes must preserve this purpose. Avoid adding unrelated frameworks, demos, deployment targets, or abstractions unless they are explicitly required by the specification being implemented.

## Language and documentation

* All documentation and Markdown files must be written in English.
* Keep documentation practical and close to the implementation.
* Public behaviour must be documented when it changes.
* Local execution instructions and OCI deployment instructions must be updated whenever a feature affects runtime behaviour.

## Spec-driven development workflow

Follow this workflow for significant features, fixes, refactorings, deployment changes, and protocol changes:

1. Read the relevant existing specification.
2. If no relevant specification exists, create one under `specs/` before implementation.
3. Review the specification for scope, behaviour, acceptance criteria, error handling, configuration, and test expectations.
4. Implement code according to the specification.
5. Add or update unit tests.
6. Run the relevant formatting, linting, testing, and coverage checks.
7. Update `CHANGELOG.md` when the change is significant.
8. Summarise what changed and which checks were run.

Code must not be generated for significant behaviour until the relevant specification exists and has clear acceptance criteria.

## Codex working rules

When working in this repository, Codex should:

* Inspect the existing project structure before editing.
* Prefer small, coherent changes over broad rewrites.
* Reuse existing modules, helpers, configuration patterns, and test fixtures before adding new ones.
* Preserve user changes already present in the working tree.
* Avoid speculative changes that are not requested by the user or required by the specification.
* Avoid introducing unrelated abstractions, frameworks, deployment targets, or examples.
* Do not create commits unless explicitly asked.
* Do not add new production dependencies without a clear reason.
* Do not run destructive commands or discard existing changes unless explicitly requested.
* Do not invent details about A2A, OCI, IAM, networking, LangGraph, or deployment behaviour.
* When uncertain, document the assumption, leave a clear TODO, or ask for clarification.

## Python environment

Use the project Conda environment for local development and tests.

If an environment definition exists, prefer it for setup. If the environment already exists, activate it before running checks.

Do not assume globally installed Python packages are available.

## Required checks

Run the relevant checks before considering work complete.

At a minimum, use the project standard tools for:

* Python formatting with `black`.
* Python linting with `pylint`.
* Unit testing with `pytest`.
* Coverage reporting when tests or behaviour are affected.

The target unit test coverage is above 80 percent.

If a check cannot be run because the environment or dependencies are missing, state that clearly in the final summary and explain what prevented the check.

## Python code conventions

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

All generated Python code must include accurate docstrings for modules, classes, methods, and functions where applicable.

Docstrings must follow the Google Python docstring format and clearly describe:

* Purpose.
* Arguments.
* Return values.
* Raised exceptions.
* Relevant behaviour and side effects.

## Human readability and maintainability

Code generated for this repository must be optimised for human readability first.

Generated code must be easy to read, review, test, and maintain by a human engineer. Prefer clear structure and explicit intent over cleverness, dense abstractions, or overly compact expressions.

Follow these principles:

* Use descriptive names for modules, classes, functions, methods, variables, and tests.
* Keep functions focused on one clear responsibility.
* Prefer straightforward control flow over deeply nested logic.
* Extract helpers only when they reduce real complexity or meaningful duplication.
* Keep public behaviour easy to trace from A2A request input to LangGraph execution and A2A response output.
* Make error handling explicit and predictable.
* Avoid hidden side effects and implicit global state.
* Keep configuration access centralised and easy to audit.
* Keep OCI-specific integration code isolated from core agent and protocol logic where practical.
* Use comments sparingly, only when they clarify non-obvious decisions or complex logic.
* Preserve consistency with the existing code style and project structure.
* Write tests that describe behaviour clearly and can be understood as executable documentation.

Readable code is part of the quality bar for this project. A change is not complete if it works technically but is unnecessarily difficult to understand or maintain.

## A2A and LangGraph design expectations

* Treat the A2A server contract as a stable public interface.
* Keep protocol schemas, request validation, response serialisation, task status mapping, and error payloads explicit and tested.
* Keep LangGraph graph construction, node behaviour, state definitions, and tool integrations documented in specifications.
* Prefer deterministic and testable agent behaviour in examples.
* Keep sample prompts, model settings, and OCI configuration visible and easy to change.
* Do not hard-code secrets, tenancy-specific identifiers, API keys, private endpoints, or local machine paths.
* Provide local execution instructions and OCI deployment instructions whenever a feature affects runtime behaviour.

## OCI configuration and security

Never commit or hard code:

* API keys.
* Private keys.
* Passwords.
* OCI tenancy OCIDs.
* User OCIDs.
* Compartment OCIDs.
* Private endpoints.
* Local machine paths.
* Customer or environment specific identifiers.

Use environment variables, configuration files excluded from version control, or documented placeholders.

When adding configuration, document:

* Variable name.
* Purpose.
* Whether it is required.
* Safe example value.
* Where it is used.

## Testing expectations

New functionality must include unit tests written with the project standard testing framework.

Tests should cover:

* Successful request and response paths.
* Validation failures.
* Error mapping.
* Task lifecycle transitions.
* Configuration loading.
* OCI integration boundaries using mocks or fakes.
* LangGraph node and state behaviour where applicable.

Tests should avoid real OCI calls unless explicitly marked as integration tests.

## Dependency policy

Before adding a dependency:

* Check whether the repository already has an equivalent library or helper.
* Prefer standard library functionality when practical.
* Add the dependency to the appropriate environment or requirements file.
* Explain why the dependency is needed.
* Update documentation if setup steps change.

Do not introduce new frameworks unless the specification requires them.

## Changelog policy

Update `CHANGELOG.md` when a change is significant, including:

* Features.
* Fixes.
* Refactorings.
* Specification updates.
* Deployment changes.
* Documentation updates.
* Test strategy changes.

Keep changelog entries concise and understandable.

## Definition of done

A change is done only when:

* The relevant specification has been written or updated.
* The implementation conforms to the specification.
* The relevant formatting, linting, testing, and coverage checks have been considered.
* Unit tests have been written or updated when behaviour changes.
* Documentation has been updated when public behaviour, setup, or deployment changes.
* `CHANGELOG.md` has been updated when required.
* Any inability to run checks has been clearly documented.
