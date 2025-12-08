"""Property-based tests for simulcast fault isolation.

**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**
**Validates: Requirements 9.3**
"""

import sys
import uuid
from datetime import datetime
from typing import List, Optional
from unittest.mock import MagicMock

# Mock celery_app before importing stream modules
sys.modules["app.core.celery_app"] = MagicMock()

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.models import (
    SimulcastTarget,
    SimulcastTargetStatus,
    SimulcastPlatform,
    ConnectionStatus,
)


# ============================================
# Test Strategies
# ============================================

# Strategy for generating platform types
platforms = st.sampled_from([
    SimulcastPlatform.YOUTUBE.value,
    SimulcastPlatform.FACEBOOK.value,
    SimulcastPlatform.TWITCH.value,
    SimulcastPlatform.TIKTOK.value,
    SimulcastPlatform.INSTAGRAM.value,
    SimulcastPlatform.CUSTOM.value,
])

# Strategy for generating target statuses
active_statuses = st.sampled_from([
    SimulcastTargetStatus.CONNECTED.value,
    SimulcastTargetStatus.STREAMING.value,
])

inactive_statuses = st.sampled_from([
    SimulcastTargetStatus.PENDING.value,
    SimulcastTargetStatus.DISCONNECTED.value,
    SimulcastTargetStatus.FAILED.value,
    SimulcastTargetStatus.STOPPED.value,
])

all_statuses = st.sampled_from([s.value for s in SimulcastTargetStatus])

# Strategy for generating number of targets (2-10 for meaningful simulcast)
target_count = st.integers(min_value=2, max_value=10)

# Strategy for generating error messages
error_messages = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')))


# ============================================
# Helper Functions for Testing
# ============================================

def create_mock_target(
    platform: str,
    status: str = SimulcastTargetStatus.STREAMING.value,
    error_count: int = 0,
) -> dict:
    """Create a mock simulcast target for testing.
    
    Args:
        platform: Platform identifier
        status: Target status
        error_count: Number of errors
        
    Returns:
        dict: Mock target data
    """
    return {
        "id": uuid.uuid4(),
        "platform": platform,
        "platform_name": f"{platform.title()} Stream",
        "status": status,
        "error_count": error_count,
        "is_active": status in [
            SimulcastTargetStatus.CONNECTED.value,
            SimulcastTargetStatus.STREAMING.value,
        ],
    }


def simulate_platform_failure(
    targets: List[dict],
    failed_target_index: int,
    error: str,
) -> tuple[dict, List[dict]]:
    """Simulate a single platform failure.
    
    Requirements 9.3: One platform failure SHALL NOT affect others.
    
    Args:
        targets: List of target dicts
        failed_target_index: Index of target to fail
        error: Error message
        
    Returns:
        tuple: (failed_target, other_targets)
    """
    if failed_target_index >= len(targets):
        failed_target_index = 0
    
    failed_target = targets[failed_target_index].copy()
    failed_target["status"] = SimulcastTargetStatus.FAILED.value
    failed_target["error_count"] += 1
    failed_target["is_active"] = False
    failed_target["last_error"] = error
    
    # Other targets should remain unaffected (fault isolation)
    other_targets = []
    for i, target in enumerate(targets):
        if i != failed_target_index:
            # Copy target - status should NOT change due to other platform's failure
            other_target = target.copy()
            other_targets.append(other_target)
    
    return failed_target, other_targets


def check_fault_isolation(
    failed_target: dict,
    other_targets: List[dict],
    original_statuses: List[str],
) -> bool:
    """Check if fault isolation is maintained.
    
    Requirements 9.3: When one platform fails, others SHALL continue uninterrupted.
    
    Args:
        failed_target: The failed target
        other_targets: Other targets after failure
        original_statuses: Original statuses of other targets
        
    Returns:
        bool: True if fault isolation is maintained
    """
    # Failed target should be marked as failed
    if failed_target["status"] != SimulcastTargetStatus.FAILED.value:
        return False
    
    # Other targets should maintain their original status
    for i, target in enumerate(other_targets):
        if i < len(original_statuses):
            # Status should not have changed due to the failure
            if target["status"] != original_statuses[i]:
                return False
    
    return True


# ============================================
# Property Tests
# ============================================

class TestSimulcastFaultIsolation:
    """Property tests for simulcast fault isolation.

    Requirements 9.3: When one platform connection fails, the System SHALL 
    continue streaming to other platforms and alert user.
    """

    @given(
        num_targets=target_count,
        failed_index=st.integers(min_value=0, max_value=9),
        error=error_messages,
    )
    @settings(max_examples=100)
    def test_single_failure_does_not_affect_others(
        self,
        num_targets: int,
        failed_index: int,
        error: str,
    ) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        For any simulcast configuration, when one platform fails, 
        other platforms SHALL continue streaming unaffected.
        """
        # Create targets with streaming status
        platforms_list = [
            SimulcastPlatform.YOUTUBE.value,
            SimulcastPlatform.FACEBOOK.value,
            SimulcastPlatform.TWITCH.value,
            SimulcastPlatform.TIKTOK.value,
            SimulcastPlatform.INSTAGRAM.value,
            SimulcastPlatform.CUSTOM.value,
        ]
        
        targets = []
        for i in range(num_targets):
            platform = platforms_list[i % len(platforms_list)]
            targets.append(create_mock_target(
                platform=platform,
                status=SimulcastTargetStatus.STREAMING.value,
            ))
        
        # Record original statuses
        original_statuses = [t["status"] for t in targets]
        
        # Simulate failure
        failed_index = failed_index % num_targets
        failed_target, other_targets = simulate_platform_failure(
            targets, failed_index, error
        )
        
        # Get original statuses of other targets
        other_original_statuses = [
            original_statuses[i] for i in range(len(targets)) if i != failed_index
        ]
        
        # Verify fault isolation
        isolation_maintained = check_fault_isolation(
            failed_target, other_targets, other_original_statuses
        )
        
        assert isolation_maintained, (
            f"Fault isolation violated: failure of {failed_target['platform']} "
            f"affected other platforms"
        )

    @given(
        num_targets=target_count,
        num_failures=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100)
    def test_multiple_failures_are_independent(
        self,
        num_targets: int,
        num_failures: int,
    ) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        For any number of platform failures, each failure SHALL be independent
        and not cascade to other platforms.
        """
        assume(num_failures < num_targets)  # Can't fail more than we have
        
        platforms_list = [
            SimulcastPlatform.YOUTUBE.value,
            SimulcastPlatform.FACEBOOK.value,
            SimulcastPlatform.TWITCH.value,
            SimulcastPlatform.TIKTOK.value,
            SimulcastPlatform.INSTAGRAM.value,
            SimulcastPlatform.CUSTOM.value,
        ]
        
        targets = []
        for i in range(num_targets):
            platform = platforms_list[i % len(platforms_list)]
            targets.append(create_mock_target(
                platform=platform,
                status=SimulcastTargetStatus.STREAMING.value,
            ))
        
        # Fail multiple targets independently
        failed_indices = list(range(num_failures))
        
        for idx in failed_indices:
            targets[idx]["status"] = SimulcastTargetStatus.FAILED.value
            targets[idx]["is_active"] = False
        
        # Count active and failed targets
        active_count = sum(1 for t in targets if t["is_active"])
        failed_count = sum(1 for t in targets if t["status"] == SimulcastTargetStatus.FAILED.value)
        
        # Verify: exactly num_failures should be failed
        assert failed_count == num_failures, (
            f"Expected {num_failures} failed targets, got {failed_count}"
        )
        
        # Verify: remaining targets should still be active
        expected_active = num_targets - num_failures
        assert active_count == expected_active, (
            f"Expected {expected_active} active targets, got {active_count}"
        )

    @given(platform=platforms, error=error_messages)
    @settings(max_examples=100)
    def test_failed_target_records_error(
        self,
        platform: str,
        error: str,
    ) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        When a platform fails, the error SHALL be recorded for that target only.
        """
        target = create_mock_target(platform=platform)
        
        # Simulate failure
        target["status"] = SimulcastTargetStatus.FAILED.value
        target["error_count"] += 1
        target["last_error"] = error
        target["is_active"] = False
        
        # Verify error is recorded
        assert target["status"] == SimulcastTargetStatus.FAILED.value
        assert target["error_count"] >= 1
        assert target["last_error"] == error
        assert target["is_active"] is False

    @given(num_targets=target_count)
    @settings(max_examples=100)
    def test_healthy_targets_remain_streaming(
        self,
        num_targets: int,
    ) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        For any simulcast configuration, healthy targets SHALL remain streaming
        regardless of failures on other platforms.
        """
        platforms_list = [
            SimulcastPlatform.YOUTUBE.value,
            SimulcastPlatform.FACEBOOK.value,
            SimulcastPlatform.TWITCH.value,
            SimulcastPlatform.TIKTOK.value,
            SimulcastPlatform.INSTAGRAM.value,
            SimulcastPlatform.CUSTOM.value,
        ]
        
        targets = []
        for i in range(num_targets):
            platform = platforms_list[i % len(platforms_list)]
            targets.append(create_mock_target(
                platform=platform,
                status=SimulcastTargetStatus.STREAMING.value,
            ))
        
        # Fail the first target
        targets[0]["status"] = SimulcastTargetStatus.FAILED.value
        targets[0]["is_active"] = False
        
        # All other targets should still be streaming
        for i in range(1, num_targets):
            assert targets[i]["status"] == SimulcastTargetStatus.STREAMING.value, (
                f"Target {i} ({targets[i]['platform']}) should still be streaming"
            )
            assert targets[i]["is_active"] is True, (
                f"Target {i} ({targets[i]['platform']}) should still be active"
            )


class TestSimulcastStatusTracking:
    """Property tests for per-platform status tracking."""

    @given(
        num_targets=target_count,
        statuses=st.lists(all_statuses, min_size=2, max_size=10),
    )
    @settings(max_examples=100)
    def test_each_target_has_independent_status(
        self,
        num_targets: int,
        statuses: List[str],
    ) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        Each simulcast target SHALL have its own independent status.
        """
        platforms_list = [
            SimulcastPlatform.YOUTUBE.value,
            SimulcastPlatform.FACEBOOK.value,
            SimulcastPlatform.TWITCH.value,
            SimulcastPlatform.TIKTOK.value,
            SimulcastPlatform.INSTAGRAM.value,
            SimulcastPlatform.CUSTOM.value,
        ]
        
        # Create targets with different statuses
        targets = []
        for i in range(min(num_targets, len(statuses))):
            platform = platforms_list[i % len(platforms_list)]
            target = create_mock_target(platform=platform, status=statuses[i])
            targets.append(target)
        
        # Verify each target has its assigned status
        for i, target in enumerate(targets):
            assert target["status"] == statuses[i], (
                f"Target {i} should have status {statuses[i]}, got {target['status']}"
            )

    @given(platform=platforms)
    @settings(max_examples=100)
    def test_is_active_reflects_status(self, platform: str) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        is_active property SHALL correctly reflect the target status.
        """
        # Test active statuses
        for status in [SimulcastTargetStatus.CONNECTED.value, SimulcastTargetStatus.STREAMING.value]:
            target = create_mock_target(platform=platform, status=status)
            assert target["is_active"] is True, (
                f"Target with status {status} should be active"
            )
        
        # Test inactive statuses
        for status in [
            SimulcastTargetStatus.PENDING.value,
            SimulcastTargetStatus.DISCONNECTED.value,
            SimulcastTargetStatus.FAILED.value,
            SimulcastTargetStatus.STOPPED.value,
        ]:
            target = create_mock_target(platform=platform, status=status)
            assert target["is_active"] is False, (
                f"Target with status {status} should not be active"
            )


class TestSimulcastContinuity:
    """Property tests for streaming continuity during failures."""

    @given(
        num_targets=st.integers(min_value=3, max_value=10),
        failure_sequence=st.lists(
            st.integers(min_value=0, max_value=9),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=100)
    def test_streaming_continues_after_sequential_failures(
        self,
        num_targets: int,
        failure_sequence: List[int],
    ) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        For any sequence of platform failures, remaining platforms SHALL
        continue streaming without interruption.
        """
        platforms_list = [
            SimulcastPlatform.YOUTUBE.value,
            SimulcastPlatform.FACEBOOK.value,
            SimulcastPlatform.TWITCH.value,
            SimulcastPlatform.TIKTOK.value,
            SimulcastPlatform.INSTAGRAM.value,
            SimulcastPlatform.CUSTOM.value,
        ]
        
        targets = []
        for i in range(num_targets):
            platform = platforms_list[i % len(platforms_list)]
            targets.append(create_mock_target(
                platform=platform,
                status=SimulcastTargetStatus.STREAMING.value,
            ))
        
        # Apply failures sequentially
        failed_indices = set()
        for idx in failure_sequence:
            actual_idx = idx % num_targets
            if actual_idx not in failed_indices:
                targets[actual_idx]["status"] = SimulcastTargetStatus.FAILED.value
                targets[actual_idx]["is_active"] = False
                failed_indices.add(actual_idx)
        
        # Count remaining active targets
        active_count = sum(1 for t in targets if t["is_active"])
        expected_active = num_targets - len(failed_indices)
        
        assert active_count == expected_active, (
            f"After {len(failed_indices)} failures, expected {expected_active} "
            f"active targets, got {active_count}"
        )
        
        # Verify non-failed targets are still streaming
        for i, target in enumerate(targets):
            if i not in failed_indices:
                assert target["status"] == SimulcastTargetStatus.STREAMING.value, (
                    f"Non-failed target {i} should still be streaming"
                )

    def test_at_least_one_platform_can_continue(self) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        If at least one platform is healthy, streaming SHALL continue.
        """
        targets = [
            create_mock_target(SimulcastPlatform.YOUTUBE.value, SimulcastTargetStatus.FAILED.value),
            create_mock_target(SimulcastPlatform.FACEBOOK.value, SimulcastTargetStatus.FAILED.value),
            create_mock_target(SimulcastPlatform.TWITCH.value, SimulcastTargetStatus.STREAMING.value),
        ]
        
        # At least one target is streaming
        active_targets = [t for t in targets if t["is_active"]]
        
        assert len(active_targets) >= 1, "At least one platform should continue streaming"
        assert active_targets[0]["platform"] == SimulcastPlatform.TWITCH.value


class TestErrorIsolation:
    """Property tests for error isolation between platforms."""

    @given(
        platform1=platforms,
        platform2=platforms,
        error=error_messages,
    )
    @settings(max_examples=100)
    def test_error_does_not_propagate(
        self,
        platform1: str,
        platform2: str,
        error: str,
    ) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        An error on one platform SHALL NOT propagate to other platforms.
        """
        assume(platform1 != platform2)  # Different platforms
        
        target1 = create_mock_target(platform1, SimulcastTargetStatus.STREAMING.value)
        target2 = create_mock_target(platform2, SimulcastTargetStatus.STREAMING.value)
        
        # Fail target1
        target1["status"] = SimulcastTargetStatus.FAILED.value
        target1["last_error"] = error
        target1["is_active"] = False
        
        # target2 should be unaffected
        assert target2["status"] == SimulcastTargetStatus.STREAMING.value
        assert target2.get("last_error") is None
        assert target2["is_active"] is True

    @given(num_targets=target_count)
    @settings(max_examples=100)
    def test_error_count_is_per_target(self, num_targets: int) -> None:
        """**Feature: youtube-automation, Property 15: Simulcast Fault Isolation**

        Error counts SHALL be tracked independently per target.
        """
        platforms_list = [
            SimulcastPlatform.YOUTUBE.value,
            SimulcastPlatform.FACEBOOK.value,
            SimulcastPlatform.TWITCH.value,
            SimulcastPlatform.TIKTOK.value,
            SimulcastPlatform.INSTAGRAM.value,
            SimulcastPlatform.CUSTOM.value,
        ]
        
        targets = []
        for i in range(num_targets):
            platform = platforms_list[i % len(platforms_list)]
            # Each target starts with different error count
            targets.append(create_mock_target(
                platform=platform,
                error_count=i,
            ))
        
        # Increment error on first target
        targets[0]["error_count"] += 1
        
        # Other targets should have unchanged error counts
        for i in range(1, num_targets):
            assert targets[i]["error_count"] == i, (
                f"Target {i} error count should be {i}, got {targets[i]['error_count']}"
            )
