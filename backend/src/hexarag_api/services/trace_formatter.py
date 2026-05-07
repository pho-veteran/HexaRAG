from hexarag_api.models.chat import Citation, InlineCitationAnchor, TracePayload


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
    )
