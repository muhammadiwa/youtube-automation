"""YouTube Account API router.

Endpoints for OAuth2 flow and account management.
Requirements: 2.1, 2.2, 2.4, 2.5
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.account.oauth import OAuthError
from app.modules.account.schemas import (
    AccountHealthResponse,
    AccountListResponse,
    OAuthCallbackRequest,
    OAuthInitiateResponse,
    QuotaUsageResponse,
    YouTubeAccountResponse,
)
from app.modules.account.service import (
    AccountExistsError,
    AccountNotFoundError,
    YouTubeAccountService,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


# Dependency for getting current user ID
# In production, this would extract from JWT token
async def get_current_user_id() -> uuid.UUID:
    """Get current authenticated user ID.
    
    This is a placeholder. In production, extract from JWT token.
    """
    # TODO: Implement proper JWT extraction
    # For now, return a placeholder UUID for testing
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/oauth/initiate",
    response_model=OAuthInitiateResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate YouTube OAuth2 flow",
    description="""
    Initiates the OAuth2 flow for connecting a YouTube account.
    
    Returns an authorization URL that the client should redirect the user to.
    The state parameter is used for CSRF protection and must be included
    in the callback.
    
    **Requirements: 2.1**
    """,
)
async def initiate_oauth(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OAuthInitiateResponse:
    """Initiate OAuth2 flow for YouTube account connection."""
    service = YouTubeAccountService(session)
    return await service.initiate_oauth(user_id)


@router.get(
    "/oauth/callback",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND,
    summary="Handle YouTube OAuth2 callback",
    description="""
    Handles the OAuth2 callback from YouTube after user authorization.
    
    Exchanges the authorization code for tokens, fetches channel metadata,
    and creates the YouTube account connection.
    
    On success, redirects to the frontend success page.
    On error, redirects to the frontend error page.
    
    **Requirements: 2.1, 2.2**
    """,
)
async def oauth_callback(
    code: Annotated[str, Query(description="Authorization code from YouTube")],
    state: Annotated[str, Query(description="State parameter for verification")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RedirectResponse:
    """Handle OAuth2 callback from YouTube."""
    service = YouTubeAccountService(session)
    
    try:
        account = await service.handle_oauth_callback(code, state)
        # Redirect to frontend success page
        return RedirectResponse(
            url=f"/accounts/connect/success?channel={account.channel_title}",
            status_code=status.HTTP_302_FOUND,
        )
    except OAuthError as e:
        # Redirect to frontend error page
        return RedirectResponse(
            url=f"/accounts/connect/error?message={str(e)}",
            status_code=status.HTTP_302_FOUND,
        )
    except AccountExistsError as e:
        return RedirectResponse(
            url=f"/accounts/connect/error?message={str(e)}",
            status_code=status.HTTP_302_FOUND,
        )


@router.get(
    "",
    response_model=AccountListResponse,
    status_code=status.HTTP_200_OK,
    summary="List connected YouTube accounts",
    description="""
    Returns all YouTube accounts connected by the current user.
    
    **Requirements: 2.4**
    """,
)
async def list_accounts(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AccountListResponse:
    """List all connected YouTube accounts for the current user."""
    service = YouTubeAccountService(session)
    accounts = await service.get_user_accounts(user_id)
    
    return AccountListResponse(
        accounts=[
            YouTubeAccountResponse.model_validate(account)
            for account in accounts
        ],
        total=len(accounts),
    )


@router.get(
    "/{account_id}",
    response_model=YouTubeAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get YouTube account details",
    description="""
    Returns details for a specific YouTube account.
    
    **Requirements: 2.4**
    """,
)
async def get_account(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> YouTubeAccountResponse:
    """Get details for a specific YouTube account."""
    service = YouTubeAccountService(session)
    account = await service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found",
        )
    
    return YouTubeAccountResponse.model_validate(account)


@router.get(
    "/{account_id}/health",
    response_model=AccountHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get account health status",
    description="""
    Returns health status for a YouTube account including:
    - Token expiration status
    - Quota usage
    - Last sync time
    - Any errors
    
    **Requirements: 2.4**
    """,
)
async def get_account_health(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AccountHealthResponse:
    """Get health status for a YouTube account."""
    service = YouTubeAccountService(session)
    
    try:
        return await service.get_account_health(account_id)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{account_id}/quota",
    response_model=QuotaUsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get quota usage",
    description="""
    Returns quota usage information for a YouTube account.
    
    **Requirements: 2.5**
    """,
)
async def get_quota_usage(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuotaUsageResponse:
    """Get quota usage for a YouTube account."""
    service = YouTubeAccountService(session)
    
    try:
        return await service.get_quota_usage(account_id)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{account_id}/sync",
    response_model=YouTubeAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync channel data",
    description="""
    Syncs channel data from YouTube API.
    
    Updates subscriber count, video count, and other metadata.
    
    **Requirements: 2.4**
    """,
)
async def sync_channel_data(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> YouTubeAccountResponse:
    """Sync channel data from YouTube API."""
    service = YouTubeAccountService(session)
    
    try:
        account = await service.sync_channel_data(account_id)
        return YouTubeAccountResponse.model_validate(account)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/{account_id}/quota/increment",
    response_model=QuotaUsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Increment quota usage",
    description="""
    Increment the quota usage for a YouTube account.
    
    This is called internally when API operations are performed.
    
    **Requirements: 2.5**
    """,
)
async def increment_quota(
    account_id: uuid.UUID,
    amount: int = 1,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> QuotaUsageResponse:
    """Increment quota usage for a YouTube account."""
    service = YouTubeAccountService(session)
    
    try:
        account = await service.increment_quota_usage(account_id, amount)
        return QuotaUsageResponse(
            account_id=account.id,
            daily_quota_used=account.daily_quota_used,
            daily_limit=10000,
            usage_percent=account.get_quota_usage_percent(),
            quota_reset_at=account.quota_reset_at,
            is_approaching_limit=account.get_quota_usage_percent() >= 80.0,
        )
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{account_id}/quota/reset",
    response_model=QuotaUsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset quota usage",
    description="""
    Reset the daily quota usage for a YouTube account.
    
    This is typically called automatically at midnight UTC.
    
    **Requirements: 2.5**
    """,
)
async def reset_quota(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> QuotaUsageResponse:
    """Reset quota usage for a YouTube account."""
    service = YouTubeAccountService(session)
    
    try:
        account = await service.reset_quota(account_id)
        return QuotaUsageResponse(
            account_id=account.id,
            daily_quota_used=account.daily_quota_used,
            daily_limit=10000,
            usage_percent=account.get_quota_usage_percent(),
            quota_reset_at=account.quota_reset_at,
            is_approaching_limit=False,
        )
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{account_id}/refresh-token",
    response_model=YouTubeAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh OAuth token",
    description="""
    Manually refresh the OAuth access token for a YouTube account.
    
    This is useful when the token is about to expire or has expired.
    
    **Requirements: 2.3**
    """,
)
async def refresh_token(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> YouTubeAccountResponse:
    """Refresh OAuth token for a YouTube account."""
    service = YouTubeAccountService(session)
    
    try:
        account = await service.refresh_account_token(account_id)
        return YouTubeAccountResponse.model_validate(account)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disconnect YouTube account",
    description="""
    Disconnects a YouTube account from the system.
    
    This removes the account and all associated tokens.
    
    **Requirements: 2.1**
    """,
)
async def disconnect_account(
    account_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Disconnect a YouTube account."""
    service = YouTubeAccountService(session)
    
    try:
        await service.disconnect_account(account_id)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
