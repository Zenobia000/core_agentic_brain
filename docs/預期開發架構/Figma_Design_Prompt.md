# Prompt for AI Design Tool (Figma Make) - Manus Hacker UI

## 1. Overall Vision & Style

**Design a desktop application interface for a developer tool called "Manus."**

The core aesthetic is a "**modern hacker terminal**" inspired by "The Matrix." It should feel futuristic, sophisticated, and code-centric. The entire UI is dark-themed with glowing green text.

*   **Theme**: Dark, retro-futuristic, cyberpunk, CRT monitor.
*   **Primary Colors**:
    *   Background: A very dark charcoal, almost black (`#0a0a0a`).
    *   Primary Text & Icons: Bright, glowing "Matrix" green (`#00ff00`).
    *   Accent Color: Cyan for highlights and running processes (`#00ffff`).
*   **Typography**: Use a monospaced font exclusively, like `JetBrains Mono` or `Figa Code`.
*   **Effects**:
    *   The entire background should have a subtle, animated "Matrix code rain" effect.
    *   Apply a faint, horizontal scanline effect over the whole interface to simulate a CRT screen.

---

## 2. Main Layout Structure

Create a three-part layout for the main application window:

1.  **Fixed Top Header**: A single-line bar locked to the top.
2.  **Main Content Grid**: The central area, which fills the space between the header and footer. This grid is split into two columns:
    *   **Left Panel (70% width)**: The primary interaction area.
    *   **Right Sidebar (30% width)**: A narrower column for status dashboards.
3.  **Fixed Bottom Footer**: A single-line input bar locked to the bottom.

The entire layout should have sharp corners and 1px borders using the primary green color.

---

## 3. Component Breakdown

### 3.1. Top Header

*   A simple horizontal bar.
*   It contains three text sections, from left to right:
    1.  `[Task] Implement user authentication`
    2.  `Phase 2/3 Analyzing code`
    3.  `Tool: python_exec ⏳` (The sand-timer icon is important).

### 3.2. Left Main Panel

This panel contains a vertical stack of components:

1.  **Conversation Panel**:
    *   This is the largest component in the left panel.
    *   It looks like a chat log.
    *   Show messages prefixed by role:
        *   `user: Please implement the auth logic.`
        *   `MANUS: ✓ Done: Schema updated, tests passed (12).`
    *   The `✓` icon should be green. The `(12)` should be a dimmer green.

2.  **Collapsible "Thinking" Panel (Default: Collapsed)**:
    *   **Collapsed State**: A single line with a `▶` icon, the title "THINKING", and a summary text like "Phase 2/3 Analyzing core components 67%".
    *   **Expanded State**: The icon changes to `▼`. Below the header, show a nested list of items like:
        *   `├── Understand the problem: User age validation`
        *   `├── Identify key areas: date_of_birth field`
        *   `└── ⏳ Generating validation logic...`

3.  **Collapsible "Tools" Panel (Default: Collapsed)**:
    *   **Collapsed State**: A single line with a `▶` icon, the title "TOOLS", and a summary like "3 calls (all success)".
    *   **Expanded State**: The icon changes to `▼`. Below, show a list of events with timestamps and status icons:
        *   `[12:35:14] ✓ grep_search("validate") → 8 matches`
        *   `[12:35:18] ▼ python_exec("test.py")`
        *   `           │ stdout: Running 12 tests... All passed.`
        *   `           └ exit: 0`

### 3.3. Right Sidebar

This is a vertical stack of dashboard-like blocks. Each block has a title in brackets (e.g., `[CONTEXT]`).

1.  **Context Block**:
    *   Title: `[CONTEXT]`
    *   Content: A list of key-value pairs:
        *   `Tokens: 4.2k/8k (52%)`
        *   `Model: claude-3.5-sonnet`
        *   `Latency: avg 1.2s`

2.  **Connections Block**:
    *   Title: `[CONNECTIONS]`
    *   Content: A list of services with status dots:
        *   `● LLM: connected` (Use a bright green dot for "active").
        *   `● MCP: 3/3 servers` (Bright green dot).
        *   `○ LSP: disabled` (Use a dim green or grey dot for "inactive").

3.  **TODO Block**:
    *   Title: `[TODO]`
    *   Content: A checklist of tasks.
        *   Use `☑` for completed items (`☑ 1. Analyze requirements`).
        *   Use `☐` for pending items (`☐ 2. Generate source code`).
        *   Highlight the current item with an arrow: `☐ 2. Generate source code ←`

### 3.4. Bottom Input Footer

*   A simple horizontal bar.
*   It contains three elements from left to right:
    1.  A prompt symbol: `manus>`
    2.  A text input area with a blinking green block cursor.
    3.  A hint text on the far right: `Ctrl+P for commands`.

---

## 4. Final Polish

*   Ensure all text has a slight glow effect to enhance the "hacker screen" feel.
*   When a panel is "active" or "focused," its border should become brighter than the others.
*   Make sure there is enough padding inside components for text to be readable.
*   The overall mood should be dark, focused, and powerful.
