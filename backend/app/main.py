"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.tracing import setup_tracing
from app.core.alerting import setup_default_thresholds
from app.core.metrics import set_app_info
from app.core.middleware import (
    MetricsMiddleware,
    CorrelationIdMiddleware,
    TracingMiddleware,
    RequestLoggingMiddleware,
    UsageMeteringMiddleware,
)
from app.modules.account import account_router
from app.modules.stream import router as stream_router
from app.modules.ai.router import router as ai_router
from app.modules.competitor.router import router as competitor_router
from app.modules.monitoring import monitoring_router
from app.modules.agent import agent_router
from app.modules.job.router import router as job_router
from app.modules.notification import notification_router
from app.modules.system_monitoring import system_monitoring_router
from app.modules.security.router import router as security_router
from app.modules.backup import backup_router
from app.modules.billing import router as billing_router
from app.modules.payment_gateway.router import router as payment_gateway_router
from app.modules.integration.router import router as integration_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## YouTube Live Streaming Automation & Multi-Account Management API

Platform SaaS untuk mengelola multiple akun YouTube, mengotomatisasi live streaming, 
dan memanfaatkan AI untuk optimasi konten.

### Fitur Utama

* **Authentication** - JWT authentication dengan 2FA support
* **YouTube Account Management** - OAuth2 integration, multi-account support
* **Video Management** - Upload, metadata, scheduling, bulk operations
* **Live Streaming** - Event creation, scheduling, health monitoring
* **AI Services** - Title/description generation, thumbnail creation
* **Analytics** - Dashboard metrics, revenue tracking, competitor analysis
* **Job Queue** - Background task processing dengan retry logic
* **Notifications** - Multi-channel alerts (email, SMS, Slack, Telegram)

### Authentication

Semua endpoint (kecuali `/health` dan `/docs`) memerlukan JWT Bearer token.

```
Authorization: Bearer <access_token>
```
    """,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=None,
    redoc_url=None,
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints",
        },
        {
            "name": "auth",
            "description": "Authentication operations - login, register, 2FA, password reset",
        },
        {
            "name": "accounts",
            "description": "YouTube account management - OAuth, token refresh, quota tracking",
        },
        {
            "name": "videos",
            "description": "Video management - upload, metadata, scheduling, bulk operations",
        },
        {
            "name": "streams",
            "description": "Live streaming - event creation, scheduling, health monitoring",
        },
        {
            "name": "ai",
            "description": "AI services - title/description generation, thumbnails",
        },
        {
            "name": "analytics",
            "description": "Analytics and reporting - metrics, revenue, competitor analysis",
        },
        {
            "name": "competitors",
            "description": "Competitor tracking and analysis - metrics, content, AI recommendations",
        },
        {
            "name": "monitoring",
            "description": "Multi-channel monitoring dashboard - channel grid, filtering, layout preferences",
        },
        {
            "name": "moderation",
            "description": "Chat and comment moderation",
        },
        {
            "name": "jobs",
            "description": "Job queue management",
        },
        {
            "name": "notifications",
            "description": "Notification preferences and delivery",
        },
        {
            "name": "billing",
            "description": "Subscription and billing management",
        },
        {
            "name": "system-monitoring",
            "description": "System monitoring - Prometheus metrics, health checks, alerts, tracing",
        },
        {
            "name": "security",
            "description": "Security features - KMS encryption, TLS configuration, admin auth, security scanning, audit export",
        },
        {
            "name": "payment-gateway",
            "description": "Multi-payment gateway management - Stripe, PayPal, Midtrans, Xendit",
        },
        {
            "name": "integration",
            "description": "API key management, webhooks, and developer integration",
        },
    ],
    contact={
        "name": "API Support",
        "email": "support@youtube-automation.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Set up logging with correlation IDs (Requirements: 24.3)
setup_logging(
    level="INFO" if not settings.DEBUG else "DEBUG",
    json_format=True,
    include_stack_trace=True,
)

# Set up distributed tracing (Requirements: 24.5)
setup_tracing(
    service_name=settings.PROJECT_NAME,
    service_version=settings.VERSION,
    environment="development" if settings.DEBUG else "production",
    enable_console_export=settings.DEBUG,
)

# Set up default alert thresholds (Requirements: 24.4)
setup_default_thresholds()

# Set application info for metrics
set_app_info(
    version=settings.VERSION,
    environment="development" if settings.DEBUG else "production",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware (Requirements: 24.1, 24.3, 24.5)
app.add_middleware(RequestLoggingMiddleware, log_request_body=False)
app.add_middleware(TracingMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(MetricsMiddleware)

# Add usage metering middleware (Requirements: 27.1)
app.add_middleware(UsageMeteringMiddleware)


def custom_openapi() -> dict:
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token",
        },
        "APIKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for external integrations",
        },
    }

    # Add servers
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.youtube-automation.com", "description": "Production server"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc documentation."""
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js",
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns the current health status of the API.

    Returns:
        dict: Health status with "healthy" or "unhealthy" value.
    """
    return {"status": "healthy"}


# Include routers
app.include_router(account_router, prefix=settings.API_V1_PREFIX)
app.include_router(stream_router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_router, prefix=settings.API_V1_PREFIX)
app.include_router(competitor_router, prefix=settings.API_V1_PREFIX)
app.include_router(monitoring_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)
app.include_router(job_router, prefix=settings.API_V1_PREFIX)
app.include_router(notification_router, prefix=settings.API_V1_PREFIX)
app.include_router(system_monitoring_router, prefix=settings.API_V1_PREFIX)
app.include_router(security_router, prefix=settings.API_V1_PREFIX)
app.include_router(backup_router, prefix=settings.API_V1_PREFIX)
app.include_router(billing_router, prefix=settings.API_V1_PREFIX)
app.include_router(payment_gateway_router, prefix=settings.API_V1_PREFIX)
app.include_router(integration_router, prefix=settings.API_V1_PREFIX)
