"""Blog API router with image upload support."""

import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.storage import get_storage, get_public_url
from app.modules.admin.middleware import verify_admin_access
from app.modules.admin.models import Admin
from app.modules.auth.models import User
from app.modules.blog.service import ArticleService
from app.modules.blog.schemas import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListResponse,
    ArticlePublicResponse,
)

router = APIRouter(prefix="/blog", tags=["blog"])

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


async def upload_blog_image(file: UploadFile) -> str:
    """Upload blog image to storage and return the URL."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )
    
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE // 1024 // 1024}MB",
        )
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    storage_key = f"blog/{filename}"
    
    # Upload to storage
    storage = get_storage()
    import io
    result = storage.upload_fileobj(
        io.BytesIO(content),
        storage_key,
        content_type=file.content_type,
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {result.error_message}",
        )
    
    return storage_key


# Public endpoints
@router.get("/articles", response_model=ArticleListResponse)
async def list_published_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List published blog articles (public)."""
    service = ArticleService(db)
    return await service.list_published_articles(
        page=page,
        page_size=page_size,
        category=category,
    )


@router.get("/articles/{slug}", response_model=ArticlePublicResponse)
async def get_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a published article by slug (public)."""
    service = ArticleService(db)
    article = await service.get_article_by_slug(slug)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return article


@router.get("/categories", response_model=list[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all article categories."""
    service = ArticleService(db)
    return await service.get_categories()


# Storage endpoint for serving images (local storage only)
@router.get("/images/{filename}")
async def get_blog_image(filename: str):
    """Serve blog image from local storage."""
    from fastapi.responses import FileResponse
    from app.core.config import settings
    import os
    
    # Only serve from local storage - cloud storage uses direct URLs
    if settings.STORAGE_BACKEND.lower() != "local":
        raise HTTPException(
            status_code=404, 
            detail="Direct image serving only available for local storage"
        )
    
    storage_key = f"blog/{filename}"
    file_path = os.path.join(settings.LOCAL_STORAGE_PATH, storage_key)
    
    if os.path.exists(file_path):
        # Determine content type
        ext = filename.split(".")[-1].lower()
        content_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg", 
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        return FileResponse(
            file_path, 
            media_type=content_types.get(ext, "application/octet-stream")
        )
    
    raise HTTPException(status_code=404, detail="Image not found")


# Admin endpoints
@router.get("/admin/articles", response_model=ArticleListResponse)
async def list_all_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    article_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(verify_admin_access),
):
    """List all articles (admin only)."""
    service = ArticleService(db)
    return await service.list_articles(
        page=page,
        page_size=page_size,
        category=category,
        status=article_status,
    )


@router.post("/admin/articles", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    title: str = Form(...),
    slug: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    excerpt: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    featured: bool = Form(False),
    read_time_minutes: int = Form(5),
    featured_image: Optional[UploadFile] = File(None),
    featured_image_key: Optional[str] = Form(None),  # For AI-generated images (storage key)
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(verify_admin_access),
):
    """Create a new article with optional image upload (admin only)."""
    # Get admin user info for author name
    result = await db.execute(select(User).where(User.id == admin.user_id))
    user = result.scalar_one_or_none()
    author_name = user.name if user and user.name else (user.email if user else "Admin")
    
    # Upload image if provided, or use storage key from AI generation
    image_url = None
    if featured_image and featured_image.filename:
        image_url = await upload_blog_image(featured_image)
    elif featured_image_key:
        # Use existing storage key (from AI generation)
        image_url = featured_image_key
    
    # Parse tags
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    data = ArticleCreate(
        title=title,
        slug=slug,
        content=content,
        category=category,
        excerpt=excerpt,
        tags=tags_list,
        meta_title=meta_title,
        meta_description=meta_description,
        featured=featured,
        read_time_minutes=read_time_minutes,
        featured_image=image_url,
    )
    
    service = ArticleService(db)
    return await service.create_article(
        data=data,
        author_id=admin.id,
        author_name=author_name,
    )


@router.get("/admin/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(verify_admin_access),
):
    """Get an article by ID (admin only)."""
    service = ArticleService(db)
    article = await service.get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return article


@router.put("/admin/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    title: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    excerpt: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    featured: Optional[bool] = Form(None),
    read_time_minutes: Optional[int] = Form(None),
    featured_image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(verify_admin_access),
):
    """Update an article with optional image upload (admin only)."""
    # Upload new image if provided
    image_url = None
    if featured_image and featured_image.filename:
        image_url = await upload_blog_image(featured_image)
    
    # Parse tags
    tags_list = None
    if tags is not None:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    
    # Build update data
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if slug is not None:
        update_data["slug"] = slug
    if content is not None:
        update_data["content"] = content
    if category is not None:
        update_data["category"] = category
    if excerpt is not None:
        update_data["excerpt"] = excerpt
    if tags_list is not None:
        update_data["tags"] = tags_list
    if meta_title is not None:
        update_data["meta_title"] = meta_title
    if meta_description is not None:
        update_data["meta_description"] = meta_description
    if featured is not None:
        update_data["featured"] = featured
    if read_time_minutes is not None:
        update_data["read_time_minutes"] = read_time_minutes
    if image_url:
        update_data["featured_image"] = image_url
    
    data = ArticleUpdate(**update_data)
    
    service = ArticleService(db)
    article = await service.update_article(article_id, data)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return article


@router.post("/admin/articles/{article_id}/publish", response_model=ArticleResponse)
async def publish_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(verify_admin_access),
):
    """Publish an article (admin only)."""
    service = ArticleService(db)
    article = await service.publish_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return article


@router.post("/admin/articles/{article_id}/unpublish", response_model=ArticleResponse)
async def unpublish_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(verify_admin_access),
):
    """Unpublish an article (admin only)."""
    service = ArticleService(db)
    article = await service.unpublish_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return article


@router.delete("/admin/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(verify_admin_access),
):
    """Delete an article (admin only)."""
    service = ArticleService(db)
    deleted = await service.delete_article(article_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )


@router.post("/admin/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    admin: Admin = Depends(verify_admin_access),
):
    """Upload an image for blog content (admin only)."""
    storage_key = await upload_blog_image(file)
    return {
        "success": True,
        "url": f"/api/v1/blog/images/{storage_key.split('/')[-1]}",
        "storage_key": storage_key,
    }


# AI Generation endpoints
@router.post("/admin/generate")
async def generate_blog_with_ai(
    topic: str = Form(...),
    category: str = Form(...),
    language: str = Form("en"),
    generate_thumbnail: bool = Form(True),
    admin: Admin = Depends(verify_admin_access),
):
    """
    Generate blog content using AI (admin only).
    
    Uses OpenRouter API with free models for text generation
    and Pollinations.ai for free thumbnail generation.
    
    - topic: The topic/subject for the blog post
    - category: Blog category (Growth, Tutorial, Analytics, SEO, Monetization, Community, News, Updates)
    - language: Language code (en, id, etc.)
    - generate_thumbnail: Whether to generate a thumbnail image
    
    Returns generated blog data that can be used to create an article.
    """
    from app.modules.blog.ai_service import ai_blog_service
    from app.modules.blog.service import get_image_url
    
    try:
        result = await ai_blog_service.generate_blog_with_thumbnail(
            topic=topic,
            category=category,
            language=language,
            generate_image=generate_thumbnail,
        )
        
        # Convert storage key to URL for frontend preview
        # But also keep the storage_key for saving to database
        featured_image_key = result.get("featured_image")
        featured_image_url = None
        if featured_image_key:
            featured_image_url = get_image_url(featured_image_key)
        
        return {
            "success": True,
            "data": {
                **result,
                "featured_image": featured_image_key,  # Storage key for saving
                "featured_image_url": featured_image_url,  # URL for preview
            },
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate blog content: {str(e)}",
        )
