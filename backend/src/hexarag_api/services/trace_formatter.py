from hexarag_api.models.chat import Citation, InlineCitationAnchor, ReasoningTrace, RuntimeTrace, TracePayload


def _build_citation_lookup(raw: dict) -> dict[str, Citation]:
    citations: dict[str, Citation] = {}

    for item in raw.get('citations', []):
        source_id = item.get('source_id') or item.get('sourceId', '')
        if not source_id:
            continue

        citations[source_id] = Citation(
            source_id=source_id,
            title=item['title'],
            excerpt=item['excerpt'],
            version=item.get('version'),
            recency_note=item.get('recency_note') or item.get('recencyNote'),
        )

    return citations


def _normalize_inline_citations(
    raw: dict, citation_lookup: dict[str, Citation]
) -> tuple[list[Citation], list[InlineCitationAnchor]]:
    normalized_anchors: list[InlineCitationAnchor] = []
    ordered_source_ids: list[str] = []

    raw_anchors = sorted(raw.get('inline_citations', []), key=lambda item: (item.get('start', 0), item.get('end', 0)))

    for item in raw_anchors:
        start = item.get('start')
        end = item.get('end')
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
            continue

        source_ids = [source_id for source_id in item.get('source_ids', []) if source_id in citation_lookup]
        if not source_ids:
            continue

        deduped_source_ids: list[str] = []
        for source_id in source_ids:
            if source_id not in deduped_source_ids:
                deduped_source_ids.append(source_id)
            if source_id not in ordered_source_ids:
                ordered_source_ids.append(source_id)

        normalized_anchors.append(
            InlineCitationAnchor(
                start=start,
                end=end,
                source_ids=deduped_source_ids,
            )
        )

    ordered_citations = [citation_lookup[source_id] for source_id in ordered_source_ids]
    return ordered_citations, normalized_anchors


def _build_runtime_trace(raw: dict) -> RuntimeTrace:
    runtime = raw.get('runtime') or {}
    return RuntimeTrace(
        mode=runtime.get('mode') or 'unknown',
        provider=runtime.get('provider') or 'unavailable',
        region=runtime.get('region'),
        agent_id=runtime.get('agent_id'),
        agent_alias_id=runtime.get('agent_alias_id'),
        model=runtime.get('model'),
    )


def _summarize_runtime(runtime: RuntimeTrace) -> str:
    if runtime.model and runtime.provider:
        return f'{runtime.model} via {runtime.provider}'
    if runtime.model:
        return runtime.model
    if runtime.provider == 'unavailable':
        return 'Runtime unavailable'
    return runtime.provider


def _format_count(noun: str, count: int) -> str:
    suffix = '' if count == 1 else 's'
    return f'{count} {noun}{suffix}'


def _join_with_and(parts: list[str]) -> str:
    if not parts:
        return ''
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f'{parts[0]} and {parts[1]}'
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def _build_reasoning_trace(raw: dict, citations: list[Citation], memory_window: list[str]) -> ReasoningTrace:
    reasoning = raw.get('reasoning') or {}
    uncertainty = raw.get('uncertainty')
    tool_calls = raw.get('tool_calls', [])
    conflict_resolution = raw.get('conflict_resolution') or {}
    runtime = _build_runtime_trace(raw)

    evidence_types = list(reasoning.get('evidence_types') or [])
    if not evidence_types:
        if citations:
            evidence_types.append('retrieval')
        if tool_calls:
            evidence_types.append('tool')
        if memory_window:
            evidence_types.append('memory')

    selected_sources = list(reasoning.get('selected_sources') or [])
    tool_basis = list(reasoning.get('tool_basis') or [])
    if not tool_basis:
        tool_basis = [tool.get('name') for tool in tool_calls if tool.get('name')]

    memory_applied = bool(reasoning.get('memory_applied'))
    memory_summary = reasoning.get('memory_summary')
    if not memory_summary and memory_window:
        memory_summary = (
            f"Used {_format_count('recent conversation item', len(memory_window))} to keep the answer on topic."
        )
        memory_applied = True

    caveat = reasoning.get('caveat') or uncertainty
    answer_strategy = reasoning.get('answer_strategy') or (
        'fallback' if runtime.provider == 'unavailable' else 'grounded-answer'
    )
    narrative_focus = reasoning.get('narrative_focus') or (
        'degraded-mode' if answer_strategy == 'fallback' else 'evidence-synthesis'
    )

    source_summary = reasoning.get('source_summary')
    if source_summary is None:
        source_count = len(selected_sources) if selected_sources else len(citations)
        source_summary = (
            f'Selected {_format_count("source", source_count)} that directly shaped the answer.'
            if source_count > 0
            else 'No citations were available for this answer.'
        )

    tool_summary = reasoning.get('tool_summary')
    if tool_summary is None:
        if answer_strategy == 'fallback' and tool_basis:
            tool_summary = f'Attempted {tool_basis[0]} before returning the fallback.'
        elif tool_basis:
            tool_summary = f'Used {_format_count("tool result", len(tool_basis))} in the final answer.'
        else:
            tool_summary = 'No tool calls were needed for this answer.'

    explanation_summary = reasoning.get('explanation_summary')
    if explanation_summary is None:
        if answer_strategy == 'fallback':
            explanation_summary = 'The answer stayed in degraded mode because the live monitoring step failed.'
        else:
            evidence_parts: list[str] = []
            if citations:
                evidence_parts.append('retrieved evidence')
            if tool_calls:
                evidence_parts.append('live tool data')
            if memory_window:
                evidence_parts.append('recent conversation context')
            explanation_summary = (
                f'The answer combined {_join_with_and(evidence_parts)}.'
                if evidence_parts
                else 'The answer was formed from the evidence available in this turn.'
            )

    conflict_summary = reasoning.get('conflict_summary')
    if conflict_summary is None and conflict_resolution:
        chosen_source = conflict_resolution.get('chosen_source')
        rationale = conflict_resolution.get('rationale')
        if chosen_source and rationale:
            conflict_summary = f'Preferred {chosen_source} because {rationale}.'

    next_step = reasoning.get('next_step')
    if next_step is None and answer_strategy == 'fallback':
        next_step = 'Retry when live monitoring is available again.'

    return ReasoningTrace(
        evidence_types=evidence_types,
        selected_sources=selected_sources,
        tool_basis=tool_basis,
        memory_applied=memory_applied,
        memory_summary=memory_summary,
        uncertainty_reason=reasoning.get('uncertainty_reason') or uncertainty,
        answer_strategy=answer_strategy,
        runtime_label=reasoning.get('runtime_label') or _summarize_runtime(runtime),
        caveat=caveat,
        source_summary=source_summary,
        tool_summary=tool_summary,
        explanation_summary=explanation_summary,
        narrative_focus=narrative_focus,
        next_step=next_step,
        conflict_summary=conflict_summary,
    )


def build_trace_payload(raw: dict, memory_window: list[str]) -> TracePayload:
    citation_lookup = _build_citation_lookup(raw)
    citations, inline_citations = _normalize_inline_citations(raw, citation_lookup)

    if not inline_citations:
        citations = list(citation_lookup.values())

    return TracePayload(
        citations=citations,
        inline_citations=inline_citations,
        tool_calls=raw.get('tool_calls', []),
        memory_window=memory_window,
        grounding_notes=raw.get('grounding_notes', []),
        uncertainty=raw.get('uncertainty'),
        conflict_resolution=raw.get('conflict_resolution'),
        runtime=_build_runtime_trace(raw),
        reasoning=_build_reasoning_trace(raw, citations, memory_window),
    )
