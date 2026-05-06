# Task 3 Frontend Shell Design

## Scope

This spec covers Foundation Task 3 only: the frontend shell with a persistent observability panel. It does not include backend integration, message submission state, or real trace rendering beyond the empty state required for the shell.

## Goals

- Replace the Vite starter UI with the HexaRAG product shell.
- Keep the app as a single-screen chat surface.
- Keep the observability panel visible beside the chat pane.
- Start with a blank conversation area.
- Build only the structure and styling needed for later chat and trace wiring.

## Non-goals

- No fetch calls or API client work.
- No session state hook.
- No seeded fake assistant response.
- No seeded fake trace payload.
- No responsive mode that stacks the observability panel under the chat pane for ordinary narrow widths.

## Approved UX decisions

- Use the low-fidelity skeleton approach.
- Start with a blank chat area.
- Keep the observability panel side-by-side with the chat pane as long as the layout remains usable.

## Component design

### `frontend/src/features/chat/ChatPage.tsx`

`ChatPage` owns the full two-pane screen layout.

It renders:
- the page heading `HexaRAG`
- a short subtitle `Ask GeekBrain anything.`
- a blank message region
- a composer with a textarea placeholder `Ask GeekBrain anything...`
- a submit button labeled `Send`
- the trace pane containing `TracePanel`

For this task, the composer is inert and the message region stays empty.

### `frontend/src/features/trace/TracePanel.tsx`

`TracePanel` is a presentational component that accepts `trace: TracePayload | null`.

For Task 3:
- when `trace` is `null`, show the heading `Observability` and the empty-state sentence `Send a question to inspect retrieval, tools, memory, and grounding.`
- when `trace` is present, render minimal sections for citations, tool calls, and memory entries using the planned type shape

The non-null rendering exists only to establish the boundary and type contract for Task 5.

### `frontend/src/types/chat.ts`

This file defines the minimal frontend types needed by the shell:
- `ChatRole`
- `Citation`
- `ToolCallTrace`
- `TracePayload`

The type shape should match the foundation plan and preserve `TracePayload.citations` plus the planned observability fields.

### `frontend/src/App.tsx`

`App.tsx` becomes a thin wrapper that renders `ChatPage`.

### `frontend/src/main.tsx`

Keep the React entrypoint simple. No special providers or routing are needed for this task.

### `frontend/src/test/setup.ts`

Keep this file limited to installing the Testing Library matchers.

## Styling design

Replace the Vite starter styles with a simple dark product shell.

### Layout

- Use a two-column grid.
- The chat pane should take the wider column.
- The observability pane should stay visible on the right with a fixed-feeling narrower width.
- The shell should fill the viewport height.

### Visual treatment

- Use a dark background with subtle pane contrast.
- Use borders to separate the two panes.
- Keep spacing generous and readable.
- Use muted supporting text and stronger heading contrast.
- Keep the composer clearly visible even without interaction logic.

### Responsive behavior

- Preserve the side-by-side product shape.
- Avoid stacking the observability panel below the chat pane during this task.
- Only allow layout compression within reason; no alternate mobile layout is introduced here.

## Testing design

Follow TDD strictly.

### First failing tests

Create these tests first:
- `frontend/src/features/chat/ChatPage.test.tsx`
- `frontend/src/features/trace/TracePanel.test.tsx`

The tests should verify:
- `ChatPage` renders the `HexaRAG` heading
- `ChatPage` renders the `Ask GeekBrain anything...` textarea placeholder
- `ChatPage` renders the `Observability` heading
- `TracePanel` shows the empty-state guidance when `trace` is `null`

### Failure condition

Run the targeted frontend tests before implementation and confirm they fail because `ChatPage` and `TracePanel` do not exist yet.

### Verification after implementation

After implementation, run:
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`

## Implementation boundaries

Task 3 should modify only the frontend shell concerns listed in the foundation plan:
- `frontend/src/types/chat.ts`
- `frontend/src/features/chat/ChatPage.tsx`
- `frontend/src/features/chat/ChatPage.test.tsx`
- `frontend/src/features/trace/TracePanel.tsx`
- `frontend/src/features/trace/TracePanel.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/styles.css`
- `frontend/src/test/setup.ts`

The Vite starter files that become obsolete can be removed or replaced if they are no longer used by the shell.

## Acceptance criteria

Task 3 is complete when:
- the Vite starter UI is gone
- the app renders a two-pane HexaRAG shell
- the chat area starts blank
- the observability panel is visible on the right
- the empty trace state shows the approved guidance copy
- the targeted tests pass
- the frontend build passes
- no Task 5 behavior is prematurely implemented
