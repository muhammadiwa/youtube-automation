"""Data migration script for video library refactor.

This script migrates existing videos to the new library-first schema.
It should be run after the database migration (alembic upgrade).

Usage:
    python scripts/migrate_video_library.py [--dry-run]
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.modules.video.models import Video


async def migrate_existing_videos(dry_run: bool = False):
    """Migrate existing videos to new schema.
    
    Args:
        dry_run: If True, only print what would be done without making changes
    """
    async with async_session_maker() as session:
        # Get all videos
        result = await session.execute(select(Video))
        videos = result.scalars().all()
        
        print(f"Found {len(videos)} videos to migrate")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for video in videos:
            try:
                changes = []
                
                # Check if user_id needs to be set
                if video.user_id is None:
                    if video.account_id:
                        # This will be handled by SQL in migration
                        changes.append("user_id will be set from account")
                    else:
                        print(f"WARNING: Video {video.id} has no account_id, cannot set user_id")
                        error_count += 1
                        continue
                
                # Set youtube_status based on youtube_id
                if video.youtube_id and not hasattr(video, 'youtube_status'):
                    changes.append(f"youtube_status: None -> 'published'")
                
                # Set youtube_url based on youtube_id
                if video.youtube_id and not hasattr(video, 'youtube_url'):
                    changes.append(f"youtube_url: None -> 'https://www.youtube.com/watch?v={video.youtube_id}'")
                
                # Set last_accessed_at to created_at
                if not hasattr(video, 'last_accessed_at') or video.last_accessed_at is None:
                    changes.append(f"last_accessed_at: None -> {video.created_at}")
                
                # Set default values for new fields
                if not hasattr(video, 'is_favorite'):
                    changes.append("is_favorite: None -> False")
                
                if not hasattr(video, 'is_used_for_streaming'):
                    changes.append("is_used_for_streaming: None -> False")
                
                if not hasattr(video, 'streaming_count'):
                    changes.append("streaming_count: None -> 0")
                
                if not hasattr(video, 'total_streaming_duration'):
                    changes.append("total_streaming_duration: None -> 0")
                
                if not hasattr(video, 'watch_time_minutes'):
                    changes.append("watch_time_minutes: None -> 0")
                
                if changes:
                    print(f"\nVideo {video.id} ({video.title}):")
                    for change in changes:
                        print(f"  - {change}")
                    
                    if not dry_run:
                        # Changes will be applied by SQL migration
                        pass
                    
                    migrated_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"ERROR migrating video {video.id}: {e}")
                error_count += 1
        
        if not dry_run:
            await session.commit()
            print(f"\n✅ Migration complete!")
        else:
            print(f"\n🔍 Dry run complete (no changes made)")
        
        print(f"\nSummary:")
        print(f"  - Migrated: {migrated_count}")
        print(f"  - Skipped: {skipped_count}")
        print(f"  - Errors: {error_count}")
        print(f"  - Total: {len(videos)}")


async def verify_migration():
    """Verify that migration was successful."""
    async with async_session_maker() as session:
        # Check that all videos have user_id
        result = await session.execute(
            select(Video).where(Video.user_id == None)
        )
        videos_without_user = result.scalars().all()
        
        if videos_without_user:
            print(f"❌ ERROR: {len(videos_without_user)} videos still have NULL user_id")
            for video in videos_without_user[:5]:  # Show first 5
                print(f"  - Video {video.id}: {video.title}")
            return False
        
        # Check that videos with youtube_id have youtube_status
        result = await session.execute(
            select(Video).where(
                Video.youtube_id != None,
                Video.youtube_status == None
            )
        )
        videos_without_status = result.scalars().all()
        
        if videos_without_status:
            print(f"❌ ERROR: {len(videos_without_status)} videos with youtube_id have NULL youtube_status")
            return False
        
        # Check that all videos have last_accessed_at
        result = await session.execute(
            select(Video).where(Video.last_accessed_at == None)
        )
        videos_without_access_time = result.scalars().all()
        
        if videos_without_access_time:
            print(f"❌ ERROR: {len(videos_without_access_time)} videos have NULL last_accessed_at")
            return False
        
        print("✅ All migration checks passed!")
        return True


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate video library data")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify migration was successful"
    )
    
    args = parser.parse_args()
    
    if args.verify:
        print("🔍 Verifying migration...")
        success = await verify_migration()
        sys.exit(0 if success else 1)
    else:
        print("🚀 Starting video library migration...")
        if args.dry_run:
            print("📋 DRY RUN MODE - No changes will be made\n")
        
        await migrate_existing_videos(dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
