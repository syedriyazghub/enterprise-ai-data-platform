"""OpenTelemetry setup for distributed tracing."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from app.core.config import settings


def setup_telemetry(service_name: str):
    """Initialize OpenTelemetry tracing."""
    resource = Resource.create({"service.name": service_name, "service.version": settings.APP_VERSION})
    provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()


def get_tracer(name: str = __name__):
    return trace.get_tracer(name)
