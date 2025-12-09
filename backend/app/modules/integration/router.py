"""API routes for Integration Service.

Requirements: 29.1, 29.2, 29.3, 29.4, 29.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.integration.service import APIKeyService, WebhookService
from app.modules.integration.schemas import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyRevokeRequest,
    RateLimitStatus,
    RateLimitExceededResponse,
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookCreateResponse,
    WebhookListResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookDeliveryInfo,
    WebhookDeliveryListResponse,
    WebhookDeliveryStatus,
    APIDocumentationResponse,
    APIEndpointInfo,
    APIKeyScope,
    WebhookEventType,
)

router = APIRouter(prefix="/integration", tags=["integration"])


# ==================== API Key Management (29.1) ====================

@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    user_id: uuid.UUID,
    data: APIKeyCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new API key with scoped permissions.
    
    Requirements: 29.1 - Generate scoped keys with configurable permissions
    
    The full API key is only returned once at creation time.
    Store it securely as it cannot be retrieved again.
    """
    service = APIKeyService(session)
    api_key, full_key = await service.create_api_key(user_id, data)
    
    response = APIKeyCreateResponse(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_hour=api_key.rate_limit_per_hour,
        rate_limit_per_day=api_key.rate_limit_per_day,
        total_requests=api_key.total_requests,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        revoked_at=api_key.revoked_at,
        expires_at=api_key.expires_at,
        allowed_ips=api_key.allowed_ips,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
        key=full_key,
    )
    return response


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    user_id: uuid.UUID,
    include_revoked: bool = Query(False, description="Include revoked keys"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    session: AsyncSession = Depends(get_session),
):
    """List all API keys for a user.
    
    Requirements: 29.1 - API key management
    """
    service = APIKeyService(session)
    keys, total = await service.list_api_keys(
        user_id=user_id,
        include_revoked=include_revoked,
        page=page,
        page_size=page_size,
    )
    
    return APIKeyListResponse(
        keys=[APIKeyResponse.model_validate(k) for k in keys],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get an API key by ID.
    
    Requirements: 29.1 - API key management
    """
    service = APIKeyService(session)
    api_key = await service.get_api_key(key_id, user_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyResponse.model_validate(api_key)


@router.patch("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: uuid.UUID,
    user_id: uuid.UUID,
    data: APIKeyUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update an API key.
    
    Requirements: 29.1 - API key management
    """
    service = APIKeyService(session)
    api_key = await service.update_api_key(key_id, user_id, data)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyResponse.model_validate(api_key)


@router.post("/api-keys/{key_id}/revoke", response_model=APIKeyResponse)
async def revoke_api_key(
    key_id: uuid.UUID,
    user_id: uuid.UUID,
    data: APIKeyRevokeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Revoke an API key.
    
    Requirements: 29.1 - Revocation support
    """
    service = APIKeyService(session)
    api_key = await service.revoke_api_key(key_id, user_id, data.reason)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyResponse.model_validate(api_key)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete an API key.
    
    Requirements: 29.1 - API key management
    """
    service = APIKeyService(session)
    deleted = await service.delete_api_key(key_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )



# ==================== Rate Limiting (29.2) ====================

@router.get("/api-keys/{key_id}/rate-limit", response_model=RateLimitStatus)
async def get_rate_limit_status(
    key_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get current rate limit status for an API key.
    
    Requirements: 29.2 - Rate limiting per key
    """
    service = APIKeyService(session)
    api_key = await service.get_api_key(key_id, user_id)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return await service.get_rate_limit_status(api_key)


@router.post("/api-keys/validate")
async def validate_api_key(
    api_key: str = Header(..., alias="X-API-Key", description="API key to validate"),
    required_scope: Optional[str] = Query(None, description="Required scope to check"),
    request: Request = None,
    session: AsyncSession = Depends(get_session),
):
    """Validate an API key and check rate limits.
    
    Requirements: 29.1 - Authenticate API requests
    Requirements: 29.2 - Rate limiting per key, reject exceeded requests
    """
    service = APIKeyService(session)
    
    # Get client IP
    client_ip = None
    if request:
        client_ip = request.client.host if request.client else None
    
    # Validate key
    is_valid, key_obj, error = await service.validate_api_key(
        api_key, required_scope, client_ip
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid API key"
        )
    
    # Check rate limit
    is_allowed, limit_type, retry_after = await service.check_rate_limit(key_obj)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RateLimitExceededResponse(
                message=f"Rate limit exceeded for {limit_type}",
                retry_after_seconds=retry_after,
                limit_type=limit_type,
            ).model_dump(),
            headers={"Retry-After": str(retry_after)},
        )
    
    # Record the request
    await service.record_request(key_obj)
    
    return {
        "valid": True,
        "key_id": str(key_obj.id),
        "user_id": str(key_obj.user_id),
        "scopes": key_obj.scopes,
    }


# ==================== Webhook Management (29.3) ====================

@router.post("/webhooks", response_model=WebhookCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    user_id: uuid.UUID,
    data: WebhookCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new webhook.
    
    Requirements: 29.3 - Configure webhook with event subscriptions
    
    The webhook secret is only returned once at creation time.
    Store it securely for signature verification.
    """
    service = WebhookService(session)
    webhook, secret = await service.create_webhook(user_id, data)
    
    response = WebhookCreateResponse(
        id=webhook.id,
        user_id=webhook.user_id,
        name=webhook.name,
        description=webhook.description,
        url=webhook.url,
        events=webhook.events,
        custom_headers=webhook.custom_headers,
        is_active=webhook.is_active,
        max_retries=webhook.max_retries,
        retry_delay_seconds=webhook.retry_delay_seconds,
        total_deliveries=webhook.total_deliveries,
        successful_deliveries=webhook.successful_deliveries,
        failed_deliveries=webhook.failed_deliveries,
        last_delivery_at=webhook.last_delivery_at,
        last_delivery_status=webhook.last_delivery_status,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        secret=secret,
    )
    return response


@router.get("/webhooks", response_model=WebhookListResponse)
async def list_webhooks(
    user_id: uuid.UUID,
    include_inactive: bool = Query(False, description="Include inactive webhooks"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    session: AsyncSession = Depends(get_session),
):
    """List all webhooks for a user.
    
    Requirements: 29.3 - Webhook management
    """
    service = WebhookService(session)
    webhooks, total = await service.list_webhooks(
        user_id=user_id,
        include_inactive=include_inactive,
        page=page,
        page_size=page_size,
    )
    
    return WebhookListResponse(
        webhooks=[WebhookResponse.model_validate(w) for w in webhooks],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a webhook by ID.
    
    Requirements: 29.3 - Webhook management
    """
    service = WebhookService(session)
    webhook = await service.get_webhook(webhook_id, user_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return WebhookResponse.model_validate(webhook)


@router.patch("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: uuid.UUID,
    user_id: uuid.UUID,
    data: WebhookUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a webhook.
    
    Requirements: 29.3 - Webhook management
    """
    service = WebhookService(session)
    webhook = await service.update_webhook(webhook_id, user_id, data)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return WebhookResponse.model_validate(webhook)


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a webhook.
    
    Requirements: 29.3 - Webhook management
    """
    service = WebhookService(session)
    deleted = await service.delete_webhook(webhook_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: uuid.UUID,
    user_id: uuid.UUID,
    data: WebhookTestRequest,
    session: AsyncSession = Depends(get_session),
):
    """Test a webhook by sending a test event.
    
    Requirements: 29.3 - Webhook testing
    """
    import httpx
    import time
    
    service = WebhookService(session)
    webhook = await service.get_webhook(webhook_id, user_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    # Create test payload
    test_payload = {
        "id": str(uuid.uuid4()),
        "type": data.event_type,
        "created_at": time.time(),
        "data": {"test": True, "message": "This is a test webhook delivery"},
        "user_id": str(user_id),
        "account_id": None,
    }
    
    # Generate signature
    signature = service.generate_signature(webhook.secret, test_payload)
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": data.event_type,
    }
    if webhook.custom_headers:
        headers.update(webhook.custom_headers)
    
    # Send test request
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook.url,
                json=test_payload,
                headers=headers,
            )
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return WebhookTestResponse(
            success=200 <= response.status_code < 300,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            error=None if 200 <= response.status_code < 300 else response.text[:500],
        )
    except httpx.TimeoutException:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_time_ms=None,
            error="Request timed out",
        )
    except httpx.RequestError as e:
        return WebhookTestResponse(
            success=False,
            status_code=None,
            response_time_ms=None,
            error=str(e),
        )



# ==================== Webhook Deliveries (29.3, 29.4) ====================

@router.get("/webhooks/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    webhook_id: uuid.UUID,
    user_id: uuid.UUID,
    status_filter: Optional[WebhookDeliveryStatus] = Query(None, alias="status", description="Filter by status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    session: AsyncSession = Depends(get_session),
):
    """List webhook delivery history.
    
    Requirements: 29.3 - Delivery tracking
    Requirements: 29.4 - Retry tracking
    """
    service = WebhookService(session)
    
    deliveries, total = await service.list_deliveries(
        webhook_id=webhook_id,
        user_id=user_id,
        status=status_filter.value if status_filter else None,
        event_type=event_type,
        page=page,
        page_size=page_size,
    )
    
    return WebhookDeliveryListResponse(
        deliveries=[WebhookDeliveryInfo.model_validate(d) for d in deliveries],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/webhooks/{webhook_id}/deliveries/{delivery_id}/retry")
async def retry_webhook_delivery(
    webhook_id: uuid.UUID,
    delivery_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Manually retry a failed webhook delivery.
    
    Requirements: 29.4 - Manual retry support
    """
    service = WebhookService(session)
    
    # Verify ownership
    webhook = await service.get_webhook(webhook_id, user_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    # Get delivery
    delivery = await service.delivery_repo.get_by_id(delivery_id)
    if not delivery or delivery.webhook_id != webhook_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    
    # Reset for retry
    delivery.status = "pending"
    delivery.attempts = 0
    delivery.next_retry_at = None
    await service.session.commit()
    
    return {"message": "Delivery queued for retry", "delivery_id": str(delivery_id)}


# ==================== API Documentation (29.5) ====================

@router.get("/docs", response_model=APIDocumentationResponse)
async def get_api_documentation(
    request: Request,
):
    """Get API documentation overview.
    
    Requirements: 29.5 - OpenAPI specification with examples
    """
    base_url = str(request.base_url).rstrip("/")
    
    # Define available scopes
    available_scopes = [
        {"scope": scope.value, "description": f"Permission for {scope.value.replace(':', ' ').replace('_', ' ')}"}
        for scope in APIKeyScope
    ]
    
    # Define available events
    available_events = [
        {"event": event.value, "description": f"Triggered when {event.value.replace('.', ' ').replace('_', ' ')}"}
        for event in WebhookEventType
    ]
    
    # Define key endpoints
    endpoints = [
        APIEndpointInfo(
            path="/integration/api-keys",
            method="POST",
            summary="Create API Key",
            description="Create a new API key with scoped permissions",
            required_scopes=[],
            rate_limited=False,
        ),
        APIEndpointInfo(
            path="/integration/api-keys",
            method="GET",
            summary="List API Keys",
            description="List all API keys for a user",
            required_scopes=[],
            rate_limited=True,
        ),
        APIEndpointInfo(
            path="/integration/api-keys/{key_id}",
            method="GET",
            summary="Get API Key",
            description="Get details of a specific API key",
            required_scopes=[],
            rate_limited=True,
        ),
        APIEndpointInfo(
            path="/integration/api-keys/{key_id}/revoke",
            method="POST",
            summary="Revoke API Key",
            description="Revoke an API key",
            required_scopes=[],
            rate_limited=False,
        ),
        APIEndpointInfo(
            path="/integration/webhooks",
            method="POST",
            summary="Create Webhook",
            description="Create a new webhook subscription",
            required_scopes=["admin:webhooks"],
            rate_limited=False,
        ),
        APIEndpointInfo(
            path="/integration/webhooks",
            method="GET",
            summary="List Webhooks",
            description="List all webhooks for a user",
            required_scopes=["admin:webhooks"],
            rate_limited=True,
        ),
        APIEndpointInfo(
            path="/integration/webhooks/{webhook_id}/test",
            method="POST",
            summary="Test Webhook",
            description="Send a test event to a webhook",
            required_scopes=["admin:webhooks"],
            rate_limited=True,
        ),
    ]
    
    return APIDocumentationResponse(
        version="1.0.0",
        title="YouTube Automation API",
        description="API for YouTube Live Streaming Automation & Multi-Account Management",
        base_url=base_url,
        endpoints=endpoints,
        available_scopes=available_scopes,
        available_events=available_events,
    )


@router.get("/docs/openapi")
async def get_openapi_spec(
    request: Request,
):
    """Get OpenAPI specification.
    
    Requirements: 29.5 - OpenAPI specification
    """
    from fastapi.openapi.utils import get_openapi
    
    # Return the OpenAPI spec from the main app
    # This endpoint provides a reference to the full OpenAPI spec
    return {
        "openapi_url": "/openapi.json",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "message": "Access the full OpenAPI specification at /openapi.json",
    }
