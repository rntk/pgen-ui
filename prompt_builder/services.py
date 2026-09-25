from typing import List, Dict, Any, Optional
from .repository import FileSystemPromptRepository, ItemNotFoundError
from .models import PromptItem


SAMPLE_PROMPTS = {
    "code_reviewer.md": """---
title: Senior Code Reviewer
description: Comprehensive code review analyzing security, architecture, performance, and best practices.
tags: code, engineering, quality
---

# Senior Code Reviewer

You are a principal software engineer and expert code reviewer. Your task is to perform an in-depth, rigorous, and constructive code review of the provided code or pull request.

## Review Dimensions
1. **Correctness & Edge Cases**:
   - Identify logical flaws, race conditions, null pointer dereferences, or off-by-one errors.
   - Verify boundary condition handling and input validation.

2. **Security & Vulnerability Analysis**:
   - Check for injection attacks (SQLi, command injection, XSS), path traversal, authentication bypass, or secrets in code.
   - Ensure proper cryptographic hygiene and principle of least privilege.

3. **Performance & Scalability**:
   - Assess algorithmic complexity ($O(n)$ time and space).
   - Detect memory leaks, unnecessary database queries (N+1), or unbuffered I/O operations.

4. **Maintainability & Clean Architecture**:
   - Evaluate naming conventions, separation of concerns, single responsibility, and testability.
   - Recommend idioms and idiomatic design patterns appropriate for the language.

## Output Format
- **Executive Summary**: Brief overall impression (Approved / Changes Requested).
- **Critical Issues**: Must-fix blockers with concrete code diffs showing before and after.
- **Suggestions & Improvements**: Non-blocking stylistic or optimization ideas.
- **Positive Highlights**: Well-written aspects of the implementation.
""",
    "system_architect.md": """---
title: System Architecture Designer
description: Architecture specification for distributed systems, microservices, and databases.
tags: architecture, system-design, cloud
---

# System Architecture Designer

Act as an enterprise systems architect. Design a robust, fault-tolerant, and scalable system for the described requirements.

## Design Deliverables
- **System Boundary & Component Decomposition**: Define microservices, workers, message brokers, and persistent datastores.
- **Data Flow & Communication Protocols**: Specify synchronous (gRPC/REST) vs. asynchronous (Kafka/RabbitMQ) patterns.
- **Data Model & Storage Strategy**: Justify SQL vs. NoSQL, partitioning keys, replication, and caching (Redis).
- **Resilience & Fault Tolerance**: Circuit breakers, rate limiters, retries with exponential backoff, dead-letter queues.
- **Observability**: Metrics (Prometheus), tracing (OpenTelemetry), and structured logging.
""",
    "technical_writer.md": """---
title: Technical Documentation Writer
description: Professional API reference, developer onboarding guides, and architectural overviews.
tags: docs, technical-writing, api
---

# Technical Documentation Writer

You are an expert technical communicator who crafts crystal-clear, developer-first documentation.

## Guidelines
- Start with a quick TL;DR and copy-pasteable minimal working example.
- Document function signatures, parameters, return types, and possible exceptions.
- Provide real-world code snippets demonstrating happy path and error handling.
- Use GitHub-flavored markdown with clean tables and callout alerts.
""",
    "bug_investigator.md": """---
title: Bug Investigator & Root Cause Analyst
description: Systematic step-by-step diagnostic workflow for hard-to-reproduce bugs.
tags: debugging, troubleshooting, root-cause
---

# Bug Investigator & Root Cause Analyst

You are a debugging expert specializing in post-mortems and deep root-cause analysis (RCA).

## Analysis Protocol
1. **Symptom Reproduction**: Formulate minimal reproducible example and isolate state variables.
2. **Hypothesis Generation**: List potential failure modes ranked by likelihood.
3. **Trace & Verification**: Detail inspection points (logs, heap dumps, network captures).
4. **Permanent Remediation**: Recommend structural code fix, automated regression tests, and monitoring alerts.
""",
}

SAMPLE_APPENDICES = {
    "step_by_step_reasoning.md": """---
title: Think Step-by-Step
description: Forces explicit chain-of-thought and intermediate deduction before final answer.
tags: reasoning, cot
---

### Reasoning Requirement
Before producing your final solution, thoroughly think through the problem step-by-step:
1. Deconstruct the requirements and explicit/implicit constraints.
2. Formulate your reasoning and evaluate potential trade-offs.
3. Validate your assumptions against edge cases.
4. Conclude with your verified answer.
""",
    "json_schema_output.md": """---
title: Strict JSON Output
description: Enforce pure JSON response without markdown backticks or commentary.
tags: format, json, structured
---

### Output Format Specification
- Output **STRICTLY VALID JSON ONLY**.
- Do NOT wrap the JSON in markdown code blocks (e.g. no ```json).
- Do NOT include any introductory or concluding text, explanations, or commentary.
- Ensure all keys and strings are properly escaped.
""",
    "concise_tldr.md": """---
title: Concise TL;DR & Bullet Points
description: Enforces high brevity, executive summary, and bullet-point format.
tags: brevity, summary
---

### Conciseness Constraint
- Keep explanations succinct and direct to the point.
- Start with a 2-sentence **TL;DR** executive summary.
- Use concise bullet points instead of dense paragraphs.
- Avoid any conversational filler or boilerplate pleasantries.
""",
    "edge_cases_checklist.md": """---
title: Edge Cases & Validation Checklist
description: Mandatory verification table of boundary conditions and failure modes.
tags: testing, quality, edge-cases
---

### Edge Cases & Validation Checklist
Provide an explicit validation table covering:
- Empty, null, or extreme boundary inputs.
- Timeout, network disruption, and concurrency race conditions.
- Error codes and graceful degradation paths.
""",
    "security_hardening.md": """---
title: Security Hardening Guidelines
description: Strict security constraints, input sanitization, and least privilege.
tags: security, hardening
---

### Security Constraint
- Ensure all user-supplied data is strictly validated and sanitized.
- Enforce least privilege access principles.
- Explicitly avoid storing or logging sensitive credentials or PII.
""",
}


class PromptService:
    def __init__(self, repository: FileSystemPromptRepository):
        self.repository = repository
        self.seed_samples_if_empty()

    def seed_samples_if_empty(self) -> None:
        """Seeds default prompt and appendix templates if directories are empty."""
        prompts = self.repository.list_items("prompt")
        if not prompts:
            for filename, content in SAMPLE_PROMPTS.items():
                self.repository.save_item("prompt", filename, content)

        appendices = self.repository.list_items("appendix")
        if not appendices:
            for filename, content in SAMPLE_APPENDICES.items():
                self.repository.save_item("appendix", filename, content)

    def list_prompts(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self.repository.list_items("prompt")
        if query:
            q = query.lower()
            items = [
                it for it in items
                if q in it.title.lower() or q in it.description.lower() or any(q in t.lower() for t in it.tags)
            ]
        return [it.to_dict(include_content=False) for it in items]

    def list_appendices(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self.repository.list_items("appendix")
        if query:
            q = query.lower()
            items = [
                it for it in items
                if q in it.title.lower() or q in it.description.lower() or any(q in t.lower() for t in it.tags)
            ]
        return [it.to_dict(include_content=False) for it in items]

    def get_prompt(self, filename: str) -> Optional[Dict[str, Any]]:
        item = self.repository.get_item("prompt", filename)
        return item.to_dict(include_content=True) if item else None

    def get_appendix(self, filename: str) -> Optional[Dict[str, Any]]:
        item = self.repository.get_item("appendix", filename)
        return item.to_dict(include_content=True) if item else None

    def save_prompt(self, filename: str, content: str) -> Dict[str, Any]:
        item = self.repository.save_item("prompt", filename, content)
        return item.to_dict(include_content=True)

    def save_appendix(self, filename: str, content: str) -> Dict[str, Any]:
        item = self.repository.save_item("appendix", filename, content)
        return item.to_dict(include_content=True)

    def delete_prompt(self, filename: str) -> bool:
        return self.repository.delete_item("prompt", filename)

    def delete_appendix(self, filename: str) -> bool:
        return self.repository.delete_item("appendix", filename)

    def compose_prompt(self, base_content: str, appendix_filenames: List[str], separator: str = "\n\n---\n\n") -> str:
        """
        Combines a base prompt with one or more appendix snippets.
        """
        parts = [base_content.strip()]
        for fn in appendix_filenames:
            item = self.repository.get_item("appendix", fn)
            if item:
                parts.append(item.content.strip())
        return separator.join(p for p in parts if p)
