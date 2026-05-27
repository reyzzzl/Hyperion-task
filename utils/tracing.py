import os
from contextvars import ContextVar
from typing import Optional

_tracer = None
_current_span: ContextVar[Optional[object]] = ContextVar("current_span", default=None)

def setup_tracing(service_name: str = "hyperion-task"):
    global _tracer
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        provider = TracerProvider()
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        HTTPXClientInstrumentor().instrument()
        _tracer = trace.get_tracer(service_name)
        return _tracer
    except Exception:
        return None

def get_tracer():
    return _tracer