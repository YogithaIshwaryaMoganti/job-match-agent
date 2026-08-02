"""Lightweight OpenTelemetry tracing — same vendor-neutral pattern as the other
two portfolio projects, reimplemented fresh here (no cross-repo code sharing).
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

_lock = threading.Lock()
_traces: dict[str, list[dict[str, Any]]] = defaultdict(list)
_MAX_TRACES = 500


class InMemorySpanExporter(SpanExporter):
    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        with _lock:
            for span in spans:
                trace_id = format(span.context.trace_id, "032x")
                _traces[trace_id].append(
                    {
                        "name": span.name,
                        "duration_ms": round((span.end_time - span.start_time) / 1_000_000, 2),
                        "attributes": dict(span.attributes or {}),
                        "parent_span_id": format(span.parent.span_id, "016x") if span.parent else None,
                        "span_id": format(span.context.span_id, "016x"),
                    }
                )
            if len(_traces) > _MAX_TRACES:
                del _traces[next(iter(_traces))]
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None


_tracer_provider: TracerProvider | None = None


def setup_tracing() -> trace.Tracer:
    global _tracer_provider
    if _tracer_provider is None:
        _tracer_provider = TracerProvider(resource=Resource.create({"service.name": "job-match-agent"}))
        _tracer_provider.add_span_processor(SimpleSpanProcessor(InMemorySpanExporter()))
        trace.set_tracer_provider(_tracer_provider)
    return trace.get_tracer("job_match_agent")


def get_trace(trace_id: str) -> list[dict[str, Any]] | None:
    with _lock:
        spans = _traces.get(trace_id)
        return list(spans) if spans else None


def current_trace_id() -> str:
    span = trace.get_current_span()
    return format(span.get_span_context().trace_id, "032x")
