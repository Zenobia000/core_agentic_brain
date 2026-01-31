# Refactoring Plan: Applying Context Engineering Principles

**Version**: 1.0
**Date**: 2026-01-31
**Author**: Gemini Agent

---

## 1. Overview

This document outlines a refactoring plan for the Core Agentic Brain based on the key findings from the `docs/預期開發架構/Context_Engineering_Analysis_Report.md`.

The primary objective of this refactoring is to evolve the agent's architecture to be more robust, efficient, and capable by systematically addressing core challenges in context management. This plan focuses on two high-impact initiatives that will improve the agent's stability and task-solving intelligence.

## 2. Core Initiatives

### Initiative 1: Implement a Few-Shot Example Manager (High Priority)

*   **Problem Statement**: The agent currently operates in a "Zero-Shot" mode, relying solely on instructions to solve tasks. This leads to inefficiency, inconsistency, and a high rate of trial-and-error for complex, multi-step workflows (e.g., travel planning, code debugging). The agent lacks "expert experience" to draw upon.

*   **Proposed Solution**:
    1.  **Create an Example Library**:
        *   Establish a new directory: `prompts/examples/`.
        *   Populate this directory with YAML or JSON files, each representing a high-quality, end-to-end task execution. For example: `travel_planning_example.yaml`.
        *   Each example file will contain a structured `input -> thought -> tool_calls -> observation` chain.
    2.  **Implement a Dynamic Injection Mechanism**:
        *   In the `Orchestrator` layer, before the `Executor` is called, introduce a `PromptManager` component.
        *   This manager will analyze the initial user prompt to classify the task type.
        *   If the task matches a category with a corresponding example in the library, the manager will load the example and inject it into the message history sent to the LLM. This provides a powerful in-context learning opportunity.

*   **Expected Outcome**:
    *   **Increased Efficiency**: The agent will follow the provided expert pattern, reducing unnecessary steps and errors.
    *   **Improved Reliability**: Task success rate for complex, known workflows will increase significantly.
    *   **Better User Experience**: The agent's behavior will be more predictable and its outputs will be more structured and relevant.

### Initiative 2: Implement a Tool Masking Architecture (Medium Priority)

*   **Problem Statement**: The current architecture may allow for the agent's available toolset to be modified dynamically. As identified in the analysis report, this can lead to "cognitive instability," where the LLM becomes confused by a changing tool environment, impacting the coherence of its long-term planning.

*   **Proposed Solution**:
    1.  **Establish a Central Tool Registry**:
        *   Create a single, authoritative source (`ToolRegistry`) where all possible tools in the system are defined and registered. This registry is static at boot time.
    2.  **Implement Runtime Filtering (Masking)**:
        *   Modify the `Kernel` or `ExecutorAgent`'s logic for preparing a tool list for the LLM.
        *   Instead of using a potentially modified list, this logic will always start with the full list from the `ToolRegistry`.
        *   It will then apply a "mask" based on the current context (e.g., user permissions, active plugins, task requirements) to generate a temporary, filtered list of tools that are "enabled" for the current turn only.

*   **Expected Outcome**:
    *   **Enhanced Stability**: The LLM maintains a stable understanding of its total capabilities, leading to more robust and coherent reasoning over long-running tasks.
    *   **Improved Security & Scalability**: Provides a solid foundation for implementing fine-grained access control, dynamic permissions, and a secure plugin architecture.

## 3. Conclusion

By prioritizing the **Few-Shot Example Manager**, we can deliver the most immediate and noticeable improvements to the agent's performance and user experience. Following up with the **Tool Masking Architecture** will ensure the long-term stability and scalability of the platform as its capabilities grow.
