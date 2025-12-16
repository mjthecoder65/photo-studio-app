import logging

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.resourcedetector.gcp_resource_detector import (
    GoogleCloudResourceDetector,
)
from opentelemetry.sdk.resources import Resource, get_aggregated_resources
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_tracing(app, project_id: str, enable_tracing: bool = True):
    """
    Set up OpenTelemetry tracing with Google Cloud Trace exporter.

    Args:
        app: FastAPI application instance
        project_id: Google Cloud project ID
        enable_tracing: Whether to enable tracing (default: True)
    """

    if not enable_tracing:
        logger.info("tracing is disabled")
        return

    try:
        # Detect GCP resources (Cloud Run, GCE, GKE, etc.)
        gcp_resource_detector = GoogleCloudResourceDetector()
        detected_resources = gcp_resource_detector.detect()

        # Create resource with service information
        resource = get_aggregated_resources(
            [
                Resource.create(
                    {
                        "service.name": "photo-studio-app",
                        "service.version": "1.0.0",
                    }
                ),
                detected_resources,
            ]
        )

        # Set up the tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Create Cloud Trace exporter
        cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)

        # Add span processor with batch export
        tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))

        # Set the global tracer provider
        trace.set_tracer_provider(tracer_provider)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        # Instrument HTTP clients (for external API calls)
        HTTPXClientInstrumentor().instrument()

        # Instrument SQLAlchemy (for database queries)
        SQLAlchemyInstrumentor().instrument()

        logger.info(
            f"tracing enabled - exporting to Google Cloud Trace (Project: {project_id})"
        )

    except Exception as e:
        logger.error(f"failed to set up tracing: {e}")
        logger.error("Application will continue without tracing")


def get_tracer(name: str = __name__):
    return trace.get_tracer(name)
