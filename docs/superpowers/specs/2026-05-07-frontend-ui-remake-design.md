# Frontend UI Remake Design

Date: 2026-05-07
Status: Draft for review

## Goal

Remake the HexaRAG frontend so it feels like a polished, premium chatbot product instead of a generic scaffold, while preserving the current functionality, the existing three-column layout, and the current backend wiring.

The redesign should make the product feel trustworthy, analytical, and calm. It should improve the visual identity, message hierarchy, inspection workflow, and perceived quality of the experience without changing the product's core behaviors.

## Non-negotiable constraints

- Keep the current three-column layout.
- Preserve current frontend-to-backend functionality and contract wiring.
- Keep the left column focused on the existing L1-L5 sample question progression.
- Keep the center chat area as the primary product surface.
- Upgrade the right column into a tabbed inspection console.
- The right column must support two tabs:
  - Observability
  - Thinking process
- The Thinking process tab must present a user-friendly trace narrative, not raw internal reasoning.
- Theme direction is dark-first.
- Overall tone is calm professional.
- Density should feel medium, not overly sparse and not overly compressed.
- Motion should stay subtle.

## Chosen direction

The chosen visual direction is **Executive Console**.

This direction keeps the product grounded and professional while making the observability capabilities feel first-class. It avoids both extremes:
- it is less flat and generic than the current UI
- it is less visually aggressive than a mission-control or neon-heavy concept

The result should feel like a premium analytical workspace for grounded AI answers.

## Product personality

The interface should communicate these traits:

- calm
- trustworthy
- technical but readable
- modern without looking flashy
- analytical without becoming developer-only

The product should feel like an operational knowledge assistant rather than a consumer chat toy.

## Layout hierarchy

### Left column

The left rail remains the most supportive column. Its job is quick onboarding and guided prompting through the L1-L5 progression.

It should not compete with the main transcript or the right-side console.

### Center column

The center chat workspace is the dominant surface. It should visually anchor the screen and carry the strongest typography, spacing, and surface hierarchy.

### Right column

The right panel becomes a high-value inspection console. It should feel important and well-structured, but still remain visually secondary to the answer itself.

## Column-by-column design

### Left column: L1-L5 guided prompt rail

Purpose:
- provide a guided entry path into the product
- preserve the W4 progression concept
- help users start quickly without changing current functionality

Structure:
- compact column header that explains the purpose of the rail
- five stacked prompt cards, one for each L-level
- each card contains:
  - level badge
  - short capability label
  - preview of the sample question

Behavior:
- clicking a prompt fills the composer only
- prompts do not auto-send
- the currently selected prompt may remain visually active until the user edits or submits

Visual treatment:
- understated compared with the other two columns
- stronger hover and active states than the current version
- compact but still touch-friendly and accessible

### Center column: premium transcript workspace

Purpose:
- become the clearest and strongest visual surface in the app
- make the assistant response feel trustworthy and readable
- preserve transcript behavior while improving hierarchy and polish

Structure:
- slim top header with product identity and compact system status
- vertically scrolling transcript area
- docked composer at the bottom

Message hierarchy:
- user messages should be visually subordinate
- assistant messages should have stronger elevation, more breathing room, and higher trust signals
- selected assistant replies should visibly connect to the right inspection console

Assistant reply content:
- referenced documents remain directly under each assistant reply
- the trace-inspection action should be clearer than a generic "View trace" label
- selection state should look refined and intentional rather than just outlined

Composer:
- anchored at the bottom
- visually elevated from the transcript
- clearer submit hierarchy
- stronger sending and disabled states
- enough room for helper text or hints without clutter

### Right column: tabbed inspection console

Purpose:
- make system evidence and explanation feel productized
- support both evidence-seeking and explanation-seeking users
- preserve current trace content while making it easier to inspect

Structure:
- sticky header
- tab bar with two tabs:
  - Observability
  - Thinking process
- scrollable tab content area

#### Observability tab

This tab presents the structured trace material.

Sections:
- Sources
- Tool calls
- Memory used
- Grounding notes
- Uncertainty or degraded-mode notes
- Error details when a request fails

This tab is the factual inspection surface.

#### Thinking process tab

This tab presents a trace narrative.

It should explain, in product language:
- what information the system checked first
- whether it used retrieval, live monitoring, or structured data
- whether contradictions existed and how they were resolved
- whether prior-turn context mattered
- why the final answer is trustworthy

This tab must not attempt to expose raw hidden chain-of-thought. It is a curated explanation layer built from the trace.

## Cross-column coordination

The redesign should make the three columns feel like one workspace.

Required coordination rules:
- selecting an assistant reply updates the right panel
- the right panel header identifies which reply is currently selected
- switching right-panel tabs must not lose the selected reply
- new assistant replies auto-select themselves by default
- failed requests must preserve transcript history and show request diagnostics in the right-side inspection console

The most important UX outcome is that the product feels coordinated, not like three disconnected panes.

## Visual system

## Theme

Dark-first.

The UI should use layered dark navy and charcoal surfaces rather than pure black or flat gray. The goal is readability, depth, and trust.

### Locked theme tokens

- Background: `#0B1020`
- Primary surface: `#12192B`
- Elevated surface: `#17233A`
- Border: `#26324A`
- Primary text: `#F8FAFC`
- Secondary text: `#94A3B8`
- Primary accent: `#6366F1`
- Observability accent: `#0891B2`
- Success: `#10B981`
- Warning: `#D97706`
- Error: `#DC2626`

### Accent logic

Use color semantically and sparingly:
- indigo/violet for primary selection, product identity, and active UI states
- cyan for live or observability-oriented status and evidence emphasis
- success, warning, and error only where functionally needed

Avoid broad neon treatment or decorative glow.

## Typography

The product should use a highly legible, software-native type system.

### Locked typography

- Primary font: `Inter`
- Optional technical font: `JetBrains Mono`

Usage guidance:
- `Inter` should be used for headings, labels, body copy, and chat content
- `JetBrains Mono` should be limited to metrics, timestamps, tool names, or structured technical values where tabular or machine-like clarity helps

Do not use the previously suggested serif-led or wellness-oriented pairing.

## Density and spacing

The interface should feel medium density.

Rules:
- enough whitespace to feel premium and readable
- enough compactness to support analytical use
- consistent spacing scale throughout the three columns
- no overcrowded trace cards
- no oversized empty surfaces that waste useful space

## Motion and interaction

Motion should be subtle and functional.

Rules:
- standard transitions should live in the 150ms-220ms range
- only animate opacity, transform, border emphasis, and shadow
- avoid width/height layout animation
- no decorative continuous animation except loading indicators
- loading behavior should feel alive but restrained

Recommended motion moments:
- hover and focus state refinement
- prompt-card emphasis
- selected reply emphasis
- tab switching
- loading and typing states
- trace-panel update transitions

## Accessibility rules

These are non-negotiable acceptance criteria for the redesign:

- maintain visible keyboard focus states
- preserve logical tab order across the three columns
- maintain WCAG-safe contrast in dark mode
- never rely on color alone to communicate meaning
- all compact actions must still have adequate hit areas
- support reduced motion
- preserve clear labels for controls and tabs
- maintain readable text sizing and spacing across the experience

## Error and loading behavior

### Loading

The UI must not feel frozen while requests are in progress.

Preferred treatments:
- subtle sending state in the composer
- lightweight response loading feedback in the transcript
- skeleton or structured loading feedback in the right panel when needed

### Errors

Errors should remain inside the product workspace rather than breaking the flow.

Rules:
- transcript history remains visible after failure
- the right panel should show error diagnostics in the Observability tab
- errors should feel informative and integrated, not like disconnected banners
- recovery should remain obvious from the composer

## Naming and content guidance

The redesign can refine wording where it improves clarity, but should preserve the user's mental model.

Examples:
- replace weak action labels such as "View trace" with clearer action copy like "Inspect response" if it tests better visually and semantically
- keep "Observability" as a strong product term
- keep "Thinking process" as the explanation-oriented tab name

## Out of scope

This redesign does not change:
- backend contracts
- left-column purpose
- the overall three-column information architecture
- authentication scope
- product scope beyond UI and UX improvements
- hidden reasoning exposure beyond approved trace narrative

## UX verification pass summary

The design was validated against the UI/UX Pro Max guidance and refined accordingly.

Validated decisions:
- AI-native minimal chrome is the correct style family
- dark-first is appropriate for this product
- Inter is the correct typography direction
- subtle motion is preferable to expressive motion
- the right-panel tab model is a strong UX improvement
- chat must remain the dominant visual surface

Adjustments made after verification:
- reduced reliance on purple-heavy styling in favor of a more navy-led professional palette
- locked Thinking process to a curated narrative rather than raw trace output
- reinforced loading, contrast, and focus-state requirements
- confirmed a single primary font system with limited mono usage

## Acceptance criteria

The redesign is successful when:
- the app still preserves all current functionality and wiring
- the left rail still serves the L1-L5 sample prompt workflow
- the center transcript clearly feels like the main surface
- the right panel clearly supports both evidence and explanation through tabs
- the UI feels premium, calm, and trustworthy instead of generic
- the selected-reply to right-panel relationship is obvious
- dark mode readability is consistently strong
- the product feels like one coordinated analytical workspace
