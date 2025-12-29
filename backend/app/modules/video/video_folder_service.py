"""Video Folder Service for managing folder hierarchy.

Provides folder management with nested folder support (max 5 levels).
Requirements: 1.2
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.models import VideoFolder, Video


MAX_FOLDER_DEPTH = 5
MAX_FOLDERS_PER_USER = 100


class VideoFolderService:
    """Service for video folder operations.
    
    Handles:
    - Creating folders
    - Updating folders
    - Deleting folders (with validation)
    - Moving videos between folders
    - Getting folder hierarchy
    """

    def __init__(self, db: AsyncSession):
        """Initialize video folder service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def create_folder(
        self,
        user_id: UUID,
        name: str,
        parent_id: Optional[UUID] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None
    ) -> VideoFolder:
        """Create new folder.
        
        Args:
            user_id: Owner of the folder
            name: Folder name
            parent_id: Parent folder ID (None for root)
            description: Folder description
            color: Hex color for UI
            icon: Icon name for UI
            
        Returns:
            VideoFolder: Created folder
            
        Raises:
            HTTPException: If validation fails
        """
        # Check folder limit
        await self._check_folder_limit(user_id)
        
        # Validate parent folder if provided
        if parent_id:
            parent = await self._get_folder(parent_id, user_id)
            # Check depth limit
            depth = await self._get_folder_depth(parent_id)
            if depth >= MAX_FOLDER_DEPTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Maximum folder depth ({MAX_FOLDER_DEPTH}) exceeded"
                )
        
        # Check for duplicate name in same parent
        await self._check_duplicate_name(user_id, name, parent_id)
        
        # Create folder
        folder = VideoFolder(
            user_id=user_id,
            name=name,
            parent_id=parent_id,
            description=description,
            color=color,
            icon=icon
        )
        
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        
        return folder

    async def update_folder(
        self,
        folder_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        position: Optional[int] = None
    ) -> VideoFolder:
        """Update folder.
        
        Args:
            folder_id: Folder identifier
            user_id: User making the update
            name: New name
            description: New description
            color: New color
            icon: New icon
            position: New position for ordering
            
        Returns:
            VideoFolder: Updated folder
        """
        folder = await self._get_folder(folder_id, user_id)
        
        # Check for duplicate name if changing name
        if name and name != folder.name:
            await self._check_duplicate_name(user_id, name, folder.parent_id, folder_id)
            folder.name = name
        
        if description is not None:
            folder.description = description
        if color is not None:
            folder.color = color
        if icon is not None:
            folder.icon = icon
        if position is not None:
            folder.position = position
        
        await self.db.commit()
        await self.db.refresh(folder)
        
        return folder

    async def delete_folder(
        self,
        folder_id: UUID,
        user_id: UUID
    ) -> None:
        """Delete folder.
        
        Args:
            folder_id: Folder identifier
            user_id: User requesting deletion
            
        Raises:
            HTTPException: If folder contains videos or subfolders
        """
        folder = await self._get_folder(folder_id, user_id)
        
        # Check if folder has videos
        video_count = await self._count_videos_in_folder(folder_id)
        if video_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete folder with {video_count} videos. Move videos first."
            )
        
        # Check if folder has subfolders
        subfolder_count = await self._count_subfolders(folder_id)
        if subfolder_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete folder with {subfolder_count} subfolders. Delete subfolders first."
            )
        
        await self.db.delete(folder)
        await self.db.commit()

    async def get_folder_tree(
        self,
        user_id: UUID
    ) -> list[VideoFolder]:
        """Get folder hierarchy for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            list[VideoFolder]: All folders (flat list, use parent_id for tree)
        """
        query = select(VideoFolder).where(
            VideoFolder.user_id == user_id
        ).order_by(VideoFolder.position, VideoFolder.name)
        
        result = await self.db.execute(query)
        folders = result.scalars().all()
        
        return list(folders)

    async def get_folder_with_stats(
        self,
        folder_id: UUID,
        user_id: UUID
    ) -> dict:
        """Get folder with statistics.
        
        Args:
            folder_id: Folder identifier
            user_id: User identifier
            
        Returns:
            dict: Folder with video count and subfolder count
        """
        folder = await self._get_folder(folder_id, user_id)
        
        video_count = await self._count_videos_in_folder(folder_id)
        subfolder_count = await self._count_subfolders(folder_id)
        
        return {
            "folder": folder,
            "video_count": video_count,
            "subfolder_count": subfolder_count
        }

    async def move_folder(
        self,
        folder_id: UUID,
        user_id: UUID,
        new_parent_id: Optional[UUID]
    ) -> VideoFolder:
        """Move folder to new parent.
        
        Args:
            folder_id: Folder to move
            user_id: User making the change
            new_parent_id: New parent folder (None for root)
            
        Returns:
            VideoFolder: Updated folder
            
        Raises:
            HTTPException: If move would create circular reference or exceed depth
        """
        folder = await self._get_folder(folder_id, user_id)
        
        # Can't move folder into itself
        if new_parent_id == folder_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot move folder into itself"
            )
        
        # Validate new parent
        if new_parent_id:
            new_parent = await self._get_folder(new_parent_id, user_id)
            
            # Check if new parent is a descendant of this folder
            if await self._is_descendant(new_parent_id, folder_id):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot move folder into its own descendant"
                )
            
            # Check depth limit
            new_depth = await self._get_folder_depth(new_parent_id)
            folder_tree_depth = await self._get_subtree_depth(folder_id)
            
            if new_depth + folder_tree_depth > MAX_FOLDER_DEPTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Move would exceed maximum folder depth ({MAX_FOLDER_DEPTH})"
                )
        
        # Check for duplicate name in new location
        await self._check_duplicate_name(user_id, folder.name, new_parent_id, folder_id)
        
        folder.parent_id = new_parent_id
        
        await self.db.commit()
        await self.db.refresh(folder)
        
        return folder

    async def _get_folder(
        self,
        folder_id: UUID,
        user_id: UUID
    ) -> VideoFolder:
        """Get folder with access check.
        
        Args:
            folder_id: Folder identifier
            user_id: User identifier
            
        Returns:
            VideoFolder: Folder object
            
        Raises:
            HTTPException: If folder not found or access denied
        """
        query = select(VideoFolder).where(
            VideoFolder.id == folder_id,
            VideoFolder.user_id == user_id
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise HTTPException(
                status_code=404,
                detail="Folder not found"
            )
        
        return folder

    async def _check_folder_limit(self, user_id: UUID) -> None:
        """Check if user has reached folder limit.
        
        Args:
            user_id: User identifier
            
        Raises:
            HTTPException: If limit exceeded
        """
        query = select(func.count()).select_from(VideoFolder).where(
            VideoFolder.user_id == user_id
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        
        if count >= MAX_FOLDERS_PER_USER:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum folder limit ({MAX_FOLDERS_PER_USER}) reached"
            )

    async def _check_duplicate_name(
        self,
        user_id: UUID,
        name: str,
        parent_id: Optional[UUID],
        exclude_id: Optional[UUID] = None
    ) -> None:
        """Check for duplicate folder name in same parent.
        
        Args:
            user_id: User identifier
            name: Folder name to check
            parent_id: Parent folder ID
            exclude_id: Folder ID to exclude from check (for updates)
            
        Raises:
            HTTPException: If duplicate found
        """
        query = select(VideoFolder).where(
            VideoFolder.user_id == user_id,
            VideoFolder.name == name,
            VideoFolder.parent_id == parent_id
        )
        
        if exclude_id:
            query = query.where(VideoFolder.id != exclude_id)
        
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Folder '{name}' already exists in this location"
            )

    async def _get_folder_depth(self, folder_id: UUID) -> int:
        """Get depth of folder in hierarchy.
        
        Args:
            folder_id: Folder identifier
            
        Returns:
            int: Depth (0 for root folders)
        """
        depth = 0
        current_id = folder_id
        
        while current_id and depth < MAX_FOLDER_DEPTH + 1:
            query = select(VideoFolder.parent_id).where(VideoFolder.id == current_id)
            result = await self.db.execute(query)
            parent_id = result.scalar_one_or_none()
            
            if parent_id:
                depth += 1
                current_id = parent_id
            else:
                break
        
        return depth

    async def _get_subtree_depth(self, folder_id: UUID) -> int:
        """Get maximum depth of folder's subtree.
        
        Args:
            folder_id: Root folder identifier
            
        Returns:
            int: Maximum depth of subtree (1 for folder with no children)
        """
        # Get all children
        query = select(VideoFolder).where(VideoFolder.parent_id == folder_id)
        result = await self.db.execute(query)
        children = result.scalars().all()
        
        if not children:
            return 1
        
        # Recursively get max depth of children
        max_child_depth = 0
        for child in children:
            child_depth = await self._get_subtree_depth(child.id)
            max_child_depth = max(max_child_depth, child_depth)
        
        return 1 + max_child_depth

    async def _is_descendant(
        self,
        potential_descendant_id: UUID,
        ancestor_id: UUID
    ) -> bool:
        """Check if folder is a descendant of another folder.
        
        Args:
            potential_descendant_id: Folder to check
            ancestor_id: Potential ancestor folder
            
        Returns:
            bool: True if descendant
        """
        current_id = potential_descendant_id
        
        while current_id:
            if current_id == ancestor_id:
                return True
            
            query = select(VideoFolder.parent_id).where(VideoFolder.id == current_id)
            result = await self.db.execute(query)
            parent_id = result.scalar_one_or_none()
            
            if not parent_id:
                break
            
            current_id = parent_id
        
        return False

    async def _count_videos_in_folder(self, folder_id: UUID) -> int:
        """Count videos in folder.
        
        Args:
            folder_id: Folder identifier
            
        Returns:
            int: Video count
        """
        query = select(func.count()).select_from(Video).where(
            Video.folder_id == folder_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _count_subfolders(self, folder_id: UUID) -> int:
        """Count subfolders.
        
        Args:
            folder_id: Folder identifier
            
        Returns:
            int: Subfolder count
        """
        query = select(func.count()).select_from(VideoFolder).where(
            VideoFolder.parent_id == folder_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
