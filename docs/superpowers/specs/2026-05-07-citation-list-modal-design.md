# Citation List + Modal Refinement Design

## Goal
Improve assistant-message citations in the HexaRAG frontend so they read as a clear document list instead of compact chips, while keeping the current three-column layout, existing backend contract, and transcript behavior intact.

## Constraints
- Preserve the current Vite + React frontend architecture.
- Preserve the existing three-column layout.
- Preserve current chat functionality and backend wiring.
- Keep citation rows visually concise because some answers may reference many documents.
- Do not add extra per-row action buttons or noisy inline controls.
- The citation-detail experience must work in both the live app and the frontend mockup dialog.

## Current Problem
Assistant citations currently render as compact chip-like items under each reply. That makes them feel like tags instead of source documents, and the presentation becomes harder to scan when many citations appear. The current frontend mockup dialog also looks like the real UI but intentionally disables interactions, which limits its usefulness for validating tab switching and source-detail interactions.

## Proposed Experience
### Assistant-message citations
- Keep the existing “Referenced documents” section under assistant replies.
- Replace chip-style citation items with a vertical, row-by-row list.
- Each row shows only the citation title.
- Each row is clickable across the title area.
- Clickability is communicated with subtle underline treatment on hover/focus and a pointer cursor.
- No “View details” button is added.

### Citation detail modal
- Clicking a citation row opens a modal above the current page.
- The modal shows:
  - citation title
  - excerpt
  - version, when present
  - recency note, when present
- Metadata is hidden entirely when absent rather than reserving empty UI.
- The modal is dismissible via close button and normal modal dismissal interactions.

### Frontend mockup dialog
- The mockup remains a visual-testing surface built from the real UI components.
- It becomes interactive enough to validate:
  - right-panel tab switching
  - clicking citation rows
  - opening and closing the citation-detail modal
- The mockup continues to use static demo data rather than live requests.

## Component and State Design
### Live page state
Keep citation-detail state in `frontend/src/features/chat/ChatPage.tsx`:
- selected citation object or `null`
- open/closed behavior derived from that selection

This keeps the feature local to the chat surface and avoids changing the backend response shape or pushing modal behavior into unrelated modules.

### Citation rendering
In assistant replies:
- Render the citation list as a vertical list container.
- Render each citation title as an interactive row.
- Use the existing citation object as the modal data source.

### Modal placement
Render the citation-detail modal from `ChatPage.tsx` so it can sit above the live app shell and the mockup shell without changing routing or the trace-panel contract.

### Mockup interaction state
Add local mockup-only state in `ChatPage.tsx` for:
- active trace tab
- selected mock citation or `null`

This allows the mockup dialog to simulate the intended interaction model without affecting live chat state.

### Trace panel boundary
Prefer keeping `frontend/src/features/trace/TracePanel.tsx` focused on trace rendering and tab switching. Citation modal ownership should remain at the page level unless implementation reveals a narrow reason to lift citation click behavior into a shared helper.

## Visual Design
### Citation rows
- Stack rows vertically with consistent spacing.
- Left-align content for quick scanning.
- Use concise row height so long citation lists remain readable.
- Remove the current chip styling.
- Use a low-noise hover state that reinforces clickability without turning the list into a secondary button group.

### Interaction cues
- Pointer cursor on citation titles.
- Underline appears on hover and keyboard focus.
- Focus state remains clearly visible for keyboard users.

### Citation modal styling
- Match the current warm light HexaRAG theme.
- Strong title hierarchy at the top.
- Excerpt displayed as the primary content block.
- Metadata grouped in a lighter secondary section when present.
- Keep the modal visually clean and readable rather than dense.

## Accessibility
- Citation rows must be keyboard reachable.
- Focus indication must remain visible and distinct.
- Modal must use appropriate dialog semantics.
- Modal close control must be clearly labeled.
- Interaction cannot rely on color alone; underline/focus styling must convey clickability.

## Testing and Verification
### Chat page behavior
Add or update tests to verify:
- assistant citations render as a vertical list rather than compact chips
- clicking a citation row opens the citation-detail modal
- the modal displays the selected title and excerpt
- closing the modal hides the detail view and returns to the transcript unchanged

### Mockup behavior
Add or update tests to verify:
- the frontend mockup dialog supports trace tab switching
- clicking a mock citation opens the mock citation-detail modal
- the mock citation modal can close cleanly

### Regression scope
Run targeted frontend tests for chat and trace behavior plus the frontend build through Docker Compose.

## Files Likely Affected
- `frontend/src/features/chat/ChatPage.tsx`
- `frontend/src/features/chat/ChatPage.test.tsx`
- `frontend/src/styles.css`
- Possibly `frontend/src/features/trace/TracePanel.tsx` only if a minimal prop adjustment is needed for mockup interactivity

## Non-Goals
- No backend contract changes.
- No new citation retrieval fields beyond the existing frontend model.
- No inline accordion expansion inside transcript cards.
- No redesign of the right-panel source list in this refinement unless implementation requires minor visual consistency updates.
