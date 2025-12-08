"""Property-based tests for playlist loop behavior.

**Feature: youtube-automation, Property 12: Playlist Loop Behavior**
**Validates: Requirements 7.2**
"""

import sys
from datetime import datetime
from unittest.mock import MagicMock

# Mock celery_app before importing stream modules
sys.modules["app.core.celery_app"] = MagicMock()

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.models import (
    StreamPlaylist,
    PlaylistItem,
    PlaylistLoopMode,
    PlaylistItemStatus,
    TransitionType,
)


# Strategy for generating loop counts (1 to 100)
loop_count_strategy = st.integers(min_value=1, max_value=100)

# Strategy for generating number of playlist items (1 to 50)
item_count_strategy = st.integers(min_value=1, max_value=50)

# Strategy for generating current loop iteration
current_loop_strategy = st.integers(min_value=0, max_value=100)


def create_mock_playlist(
    loop_mode: str,
    loop_count: int | None,
    item_count: int,
    current_loop: int = 0,
    current_item_index: int = 0,
) -> StreamPlaylist:
    """Create a mock playlist for testing.
    
    Args:
        loop_mode: Loop mode (none, count, infinite)
        loop_count: Number of loops for COUNT mode
        item_count: Number of items in playlist
        current_loop: Current loop iteration
        current_item_index: Current item index
        
    Returns:
        StreamPlaylist: Mock playlist instance
    """
    playlist = StreamPlaylist()
    playlist.loop_mode = loop_mode
    playlist.loop_count = loop_count
    playlist.current_loop = current_loop
    playlist.current_item_index = current_item_index
    playlist.is_active = True
    
    # Create mock items
    items = []
    for i in range(item_count):
        item = PlaylistItem()
        item.position = i
        item.video_title = f"Video {i + 1}"
        item.status = PlaylistItemStatus.PENDING.value
        items.append(item)
    
    playlist.items = items
    return playlist


class TestPlaylistLoopBehavior:
    """Property tests for playlist loop behavior.

    Requirements 7.2: Playlist SHALL loop based on configured loop count or infinite setting.
    """

    @given(
        item_count=item_count_strategy,
    )
    @settings(max_examples=100)
    def test_none_mode_plays_once(self, item_count: int) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any playlist with loop_mode=NONE, the playlist SHALL play exactly once
        (total plays = item_count).
        """
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.NONE.value,
            loop_count=None,
            item_count=item_count,
        )
        
        # After playing all items, should_loop should be False
        playlist.current_item_index = item_count - 1  # At last item
        
        assert playlist.should_loop() is False, "NONE mode should not loop"
        
        # Next item should be None (playlist complete)
        next_index = playlist.get_next_item_index()
        assert next_index is None, "NONE mode should return None after last item"

    @given(
        loop_count=loop_count_strategy,
        item_count=item_count_strategy,
    )
    @settings(max_examples=100)
    def test_count_mode_loops_n_times(
        self, loop_count: int, item_count: int
    ) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any playlist with loop_mode=COUNT and loop_count=N, the playlist
        SHALL loop N times (meaning it plays N times through the playlist).
        When current_loop < loop_count, should_loop returns True.
        When current_loop >= loop_count, should_loop returns False.
        """
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.COUNT.value,
            loop_count=loop_count,
            item_count=item_count,
        )
        
        # Test that should_loop is True while current_loop < loop_count
        for loop_iteration in range(loop_count):
            playlist.current_loop = loop_iteration
            assert playlist.should_loop() is True, f"Should loop at iteration {loop_iteration} (< {loop_count})"
        
        # Test that should_loop is False when current_loop >= loop_count
        playlist.current_loop = loop_count
        assert playlist.should_loop() is False, f"Should not loop when current_loop ({loop_count}) >= loop_count ({loop_count})"

    @given(
        item_count=item_count_strategy,
        current_loop=current_loop_strategy,
    )
    @settings(max_examples=100)
    def test_infinite_mode_always_loops(
        self, item_count: int, current_loop: int
    ) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any playlist with loop_mode=INFINITE, the playlist SHALL always
        loop regardless of current_loop value.
        """
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.INFINITE.value,
            loop_count=None,
            item_count=item_count,
            current_loop=current_loop,
        )
        
        # At any loop iteration, should_loop should be True
        assert playlist.should_loop() is True, f"INFINITE mode should always loop (iteration {current_loop})"
        
        # At last item, next_index should wrap to 0
        playlist.current_item_index = item_count - 1
        next_index = playlist.get_next_item_index()
        assert next_index == 0, "INFINITE mode should wrap to index 0"

    @given(
        loop_count=loop_count_strategy,
        item_count=item_count_strategy,
        current_loop=current_loop_strategy,
    )
    @settings(max_examples=100)
    def test_count_mode_stops_after_n_loops(
        self, loop_count: int, item_count: int, current_loop: int
    ) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any playlist with loop_mode=COUNT, should_loop SHALL return False
        when current_loop >= loop_count.
        """
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.COUNT.value,
            loop_count=loop_count,
            item_count=item_count,
            current_loop=current_loop,
        )
        
        should_loop = playlist.should_loop()
        
        if current_loop < loop_count:
            assert should_loop is True, f"Should loop when current_loop ({current_loop}) < loop_count ({loop_count})"
        else:
            assert should_loop is False, f"Should not loop when current_loop ({current_loop}) >= loop_count ({loop_count})"

    @given(
        item_count=item_count_strategy,
        current_index=st.integers(min_value=0, max_value=49),
    )
    @settings(max_examples=100)
    def test_next_item_index_increments_correctly(
        self, item_count: int, current_index: int
    ) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any playlist, get_next_item_index SHALL return current_index + 1
        when not at the last item.
        """
        assume(current_index < item_count - 1)  # Not at last item
        
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.NONE.value,
            loop_count=None,
            item_count=item_count,
            current_item_index=current_index,
        )
        
        next_index = playlist.get_next_item_index()
        expected = current_index + 1
        
        assert next_index == expected, f"Expected next index {expected}, got {next_index}"

    @given(
        loop_count=loop_count_strategy,
        item_count=item_count_strategy,
    )
    @settings(max_examples=100)
    def test_loop_wraps_to_beginning(
        self, loop_count: int, item_count: int
    ) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any playlist configured to loop, when at the last item,
        get_next_item_index SHALL return 0 (wrap to beginning).
        """
        assume(loop_count > 1)  # Need at least 2 loops to test wrapping
        
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.COUNT.value,
            loop_count=loop_count,
            item_count=item_count,
            current_loop=0,  # First loop
            current_item_index=item_count - 1,  # At last item
        )
        
        next_index = playlist.get_next_item_index()
        
        assert next_index == 0, "Should wrap to index 0 when looping"

    @given(
        item_count=item_count_strategy,
    )
    @settings(max_examples=100)
    def test_empty_playlist_returns_none(self, item_count: int) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any empty playlist, get_next_item_index SHALL return None.
        """
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.INFINITE.value,
            loop_count=None,
            item_count=0,  # Empty playlist
        )
        
        next_index = playlist.get_next_item_index()
        
        assert next_index is None, "Empty playlist should return None"

    @given(
        loop_count=loop_count_strategy,
        item_count=item_count_strategy,
    )
    @settings(max_examples=100)
    def test_total_items_count_accurate(
        self, loop_count: int, item_count: int
    ) -> None:
        """**Feature: youtube-automation, Property 12: Playlist Loop Behavior**

        For any playlist, get_total_items SHALL return the exact number of items.
        """
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.COUNT.value,
            loop_count=loop_count,
            item_count=item_count,
        )
        
        total = playlist.get_total_items()
        
        assert total == item_count, f"Expected {item_count} items, got {total}"


class TestPlaylistLoopEdgeCases:
    """Edge case tests for playlist loop behavior."""

    def test_single_item_playlist_loops(self) -> None:
        """Single item playlist with INFINITE mode SHALL loop."""
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.INFINITE.value,
            loop_count=None,
            item_count=1,
            current_item_index=0,
        )
        
        assert playlist.should_loop() is True
        next_index = playlist.get_next_item_index()
        assert next_index == 0, "Single item should wrap to itself"

    def test_loop_count_one_loops_once(self) -> None:
        """Playlist with loop_count=1 SHALL loop once (play through once).
        
        When loop_count=1 and current_loop=0, should_loop returns True.
        After incrementing current_loop to 1, should_loop returns False.
        """
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.COUNT.value,
            loop_count=1,
            item_count=3,
            current_loop=0,
            current_item_index=2,  # At last item
        )
        
        # First loop (current_loop=0), should loop since 0 < 1
        assert playlist.should_loop() is True, "Should loop when current_loop (0) < loop_count (1)"
        
        # After completing first loop, current_loop becomes 1
        playlist.current_loop = 1
        assert playlist.should_loop() is False, "Should not loop when current_loop (1) >= loop_count (1)"
        
        # At last item with no more loops, next_index should be None
        next_index = playlist.get_next_item_index()
        assert next_index is None, "Should not continue after completing all loops"

    def test_loop_count_zero_handled(self) -> None:
        """Playlist with loop_count=0 SHALL not loop (edge case)."""
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.COUNT.value,
            loop_count=0,
            item_count=3,
            current_loop=0,
        )
        
        # With loop_count=0, should not loop
        assert playlist.should_loop() is False

    def test_current_loop_exceeds_count(self) -> None:
        """When current_loop exceeds loop_count, SHALL not loop."""
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.COUNT.value,
            loop_count=5,
            item_count=3,
            current_loop=10,  # Exceeds loop_count
        )
        
        assert playlist.should_loop() is False

    def test_none_mode_with_loop_count_ignored(self) -> None:
        """In NONE mode, loop_count SHALL be ignored."""
        playlist = create_mock_playlist(
            loop_mode=PlaylistLoopMode.NONE.value,
            loop_count=100,  # Should be ignored
            item_count=3,
            current_item_index=2,  # At last item
        )
        
        assert playlist.should_loop() is False
        next_index = playlist.get_next_item_index()
        assert next_index is None, "NONE mode should ignore loop_count"
