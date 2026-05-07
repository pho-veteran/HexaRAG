from hexarag_api.models.chat import Citation, TracePayload


def build_trace_payload(raw: dict, memory_window: list[str]) -> TracePayload:
    citations = [
        Citation(
            source_id=item.get('source_id') or item.get('sourceId', ''),
            title=item['title'],
            excerpt=item['excerpt'],
            version=item.get('version'),
            recency_note=item.get('recency_note') or item.get('recencyNote'),
        )
        for item in raw.get('citations', [])
    ]

    return TracePayload(
        citations=citations,
        tool_calls=raw.get('tool_calls', []),
        memory_window=memory_window,
        grounding_notes=raw.get('grounding_notes', []),
        uncertainty=raw.get('uncertainty'),
        conflict_resolution=raw.get('conflict_resolution'),
    )
