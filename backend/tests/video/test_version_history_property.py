"""Property-based tests for metadata version history.

**Feature: youtube-automation, Property 9: Metadata Version History**
**Validates: Requirements 4.5**
"""

import uuid
from datetime import datetime
from typing import Optional

from hypothesis import given, settings, strategies as st, assume
from pydantic import BaseModel


# Simulated Video and MetadataVersion for testing without database
class MockVideo:
    """Mock video for testing version history logic."""

    def __init__(
        self,
        video_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: str = "private",
    ):
        self.id = video_id
        self.title = title
        self.description = description
        self.tags = tags
        self.category_id = category_id
        self.visibility = visibility
        self.thumbnail_url = None


class MockMetadataVersion:
    """Mock metadata version for testing."""

    def __init__(
        self,
        video_id: uuid.UUID,
        version_number: int,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: str = "private",
        thumbnail_url: Optional[str] = None,
        changed_by: Optional[uuid.UUID] = None,
        change_reason: Optional[str] = None,
    ):
        self.id = uuid.uuid4()
        self.video_id = video_id
        self.version_number = version_number
        self.title = title
        self.description = description
        self.tags = tags
        self.category_id = category_id
        self.visibility = visibility
        self.thumbnail_url = thumbnail_url
        self.changed_by = changed_by
        self.change_reason = change_reason
        self.created_at = datetime.utcnow()


class MockVideoRepository:
    """Mock repository for testing version history logic."""

    def __init__(self):
        self.videos: dict[uuid.UUID, MockVideo] = {}
        self.versions: dict[uuid.UUID, list[MockMetadataVersion]] = {}

    def create_video(
        self,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: str = "private",
    ) -> MockVideo:
        """Create a video and its initial version."""
        video_id = uuid.uuid4()
        video = MockVideo(
            video_id=video_id,
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            visibility=visibility,
        )
        self.videos[video_id] = video
        self.versions[video_id] = []

        # Create initial version
        self._create_version(video)

        return video

    def _create_version(
        self,
        video: MockVideo,
        changed_by: Optional[uuid.UUID] = None,
        change_reason: Optional[str] = None,
    ) -> MockMetadataVersion:
        """Create a new metadata version for a video."""
        versions = self.versions.get(video.id, [])
        next_version = len(versions) + 1

        version = MockMetadataVersion(
            video_id=video.id,
            version_number=next_version,
            title=video.title,
            description=video.description,
            tags=video.tags,
            category_id=video.category_id,
            visibility=video.visibility,
            thumbnail_url=video.thumbnail_url,
            changed_by=changed_by,
            change_reason=change_reason,
        )

        self.versions[video.id].append(version)
        return version

    def update_metadata(
        self,
        video: MockVideo,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: Optional[str] = None,
        changed_by: Optional[uuid.UUID] = None,
        change_reason: Optional[str] = None,
    ) -> MockVideo:
        """Update video metadata and create a new version."""
        if title is not None:
            video.title = title
        if description is not None:
            video.description = description
        if tags is not None:
            video.tags = tags
        if category_id is not None:
            video.category_id = category_id
        if visibility is not None:
            video.visibility = visibility

        # Create new version
        self._create_version(video, changed_by, change_reason)

        return video

    def get_version_count(self, video_id: uuid.UUID) -> int:
        """Get the count of versions for a video."""
        return len(self.versions.get(video_id, []))

    def get_versions(self, video_id: uuid.UUID) -> list[MockMetadataVersion]:
        """Get all versions for a video."""
        return self.versions.get(video_id, [])


# Strategies for generating test data
valid_title_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_"),
    min_size=1,
    max_size=50,
).map(lambda x: x.strip()).filter(lambda x: len(x) > 0)

valid_description_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 .,!?"),
    max_size=200,
)

valid_tags_strategy = st.lists(
    st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
        min_size=1,
        max_size=20,
    ),
    max_size=10,
)


class TestMetadataVersionHistory:
    """Property tests for metadata version history.

    Requirements 4.5: For any metadata save operation, a new version entry SHALL be created.
    """

    @given(title=valid_title_strategy)
    @settings(max_examples=100)
    def test_initial_video_has_one_version(self, title: str) -> None:
        """**Feature: youtube-automation, Property 9: Metadata Version History**

        When a video is created, it SHALL have exactly one initial version.
        """
        repo = MockVideoRepository()
        video = repo.create_video(title=title)

        version_count = repo.get_version_count(video.id)
        assert version_count == 1, f"Expected 1 version, got {version_count}"

    @given(
        title=valid_title_strategy,
        num_updates=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_each_update_creates_new_version(
        self, title: str, num_updates: int
    ) -> None:
        """**Feature: youtube-automation, Property 9: Metadata Version History**

        For any N metadata updates, version count SHALL be N + 1 (initial + updates).
        """
        repo = MockVideoRepository()
        video = repo.create_video(title=title)

        # Perform N updates
        for i in range(num_updates):
            repo.update_metadata(video, title=f"Updated Title {i}")

        version_count = repo.get_version_count(video.id)
        expected_count = 1 + num_updates  # Initial + updates

        assert version_count == expected_count, (
            f"Expected {expected_count} versions after {num_updates} updates, got {version_count}"
        )

    @given(
        title=valid_title_strategy,
        new_title=valid_title_strategy,
    )
    @settings(max_examples=100)
    def test_version_preserves_metadata_snapshot(
        self, title: str, new_title: str
    ) -> None:
        """**Feature: youtube-automation, Property 9: Metadata Version History**

        Each version SHALL preserve the metadata snapshot at that point in time.
        """
        assume(title != new_title)

        repo = MockVideoRepository()
        video = repo.create_video(title=title)

        # Update title
        repo.update_metadata(video, title=new_title)

        versions = repo.get_versions(video.id)
        assert len(versions) == 2

        # First version should have original title
        assert versions[0].title == title
        # Second version should have new title
        assert versions[1].title == new_title

    @given(
        title=valid_title_strategy,
        description=valid_description_strategy,
        tags=valid_tags_strategy,
    )
    @settings(max_examples=100)
    def test_version_captures_all_metadata_fields(
        self, title: str, description: str, tags: list[str]
    ) -> None:
        """**Feature: youtube-automation, Property 9: Metadata Version History**

        Version SHALL capture all metadata fields (title, description, tags, etc.).
        """
        repo = MockVideoRepository()
        video = repo.create_video(
            title=title,
            description=description,
            tags=tags,
            category_id="22",
            visibility="public",
        )

        versions = repo.get_versions(video.id)
        assert len(versions) == 1

        version = versions[0]
        assert version.title == title
        assert version.description == description
        assert version.tags == tags
        assert version.category_id == "22"
        assert version.visibility == "public"

    @given(
        title=valid_title_strategy,
        num_updates=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_versions_have_sequential_numbers(
        self, title: str, num_updates: int
    ) -> None:
        """**Feature: youtube-automation, Property 9: Metadata Version History**

        Version numbers SHALL be sequential starting from 1.
        """
        repo = MockVideoRepository()
        video = repo.create_video(title=title)

        for i in range(num_updates):
            repo.update_metadata(video, title=f"Title {i}")

        versions = repo.get_versions(video.id)

        for i, version in enumerate(versions):
            expected_number = i + 1
            assert version.version_number == expected_number, (
                f"Expected version {expected_number}, got {version.version_number}"
            )

    @given(title=valid_title_strategy)
    @settings(max_examples=100)
    def test_version_count_never_decreases(self, title: str) -> None:
        """**Feature: youtube-automation, Property 9: Metadata Version History**

        Version count SHALL never decrease (versions are append-only).
        """
        repo = MockVideoRepository()
        video = repo.create_video(title=title)

        previous_count = repo.get_version_count(video.id)

        # Perform multiple updates
        for i in range(5):
            repo.update_metadata(video, title=f"Title {i}")
            current_count = repo.get_version_count(video.id)
            assert current_count >= previous_count, (
                f"Version count decreased from {previous_count} to {current_count}"
            )
            previous_count = current_count


class TestVersionHistoryInvariants:
    """Tests for version history invariants."""

    def test_version_has_required_fields(self) -> None:
        """Version SHALL have all required fields."""
        repo = MockVideoRepository()
        video = repo.create_video(title="Test Video")

        versions = repo.get_versions(video.id)
        version = versions[0]

        assert hasattr(version, "id")
        assert hasattr(version, "video_id")
        assert hasattr(version, "version_number")
        assert hasattr(version, "title")
        assert hasattr(version, "description")
        assert hasattr(version, "tags")
        assert hasattr(version, "visibility")
        assert hasattr(version, "created_at")

    def test_version_linked_to_correct_video(self) -> None:
        """Version SHALL be linked to the correct video."""
        repo = MockVideoRepository()
        video1 = repo.create_video(title="Video 1")
        video2 = repo.create_video(title="Video 2")

        versions1 = repo.get_versions(video1.id)
        versions2 = repo.get_versions(video2.id)

        for v in versions1:
            assert v.video_id == video1.id

        for v in versions2:
            assert v.video_id == video2.id
