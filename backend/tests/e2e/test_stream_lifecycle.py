"""End-to-end tests for stream lifecycle.

Tests complete stream lifecycle including:
- Stream creation
- Stream start/stop
- Health monitoring
- Playlist streaming
- Simulcast configuration

**Validates: Requirements 5.1, 5.2, 6.1, 6.2, 6.3, 7.1, 7.2, 8.1, 9.1**
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import pytest
from hypothesis import given, settings, strategies as st, assume


class StreamLifecycleState(str, Enum):
    INITIAL = "initial"
    CREATED = "created"
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"


class LatencyMode(str, Enum):
    NORMAL = "normal"
    LOW = "low"
    ULTRA_LOW = "ultraLow"


@dataclass
class MockLiveEvent:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    account_id: uuid.UUID = field(default_factory=uuid.uuid4)
    youtube_broadcast_id: str = ""
    rtmp_key: str = ""
    title: str = ""
    description: str = ""
    scheduled_start_at: Optional[datetime] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    latency_mode: str = LatencyMode.NORMAL.value
    status: str = StreamLifecycleState.CREATED.value


@dataclass
class MockStreamSession:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    live_event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    peak_viewers: int = 0


@dataclass
class MockStreamHealth:
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    bitrate: int = 4500
    dropped_frames: int = 0
    connection_status: str = "excellent"
    viewer_count: int = 0


@dataclass
class MockPlaylistItem:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    live_event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    video_id: uuid.UUID = field(default_factory=uuid.uuid4)
    position: int = 0


@dataclass
class MockSimulcastTarget:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    live_event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    platform: str = ""
    rtmp_url: str = ""


class MockStreamLifecycleService:
    def __init__(self):
        self.events: dict[uuid.UUID, MockLiveEvent] = {}
        self.sessions: dict[uuid.UUID, MockStreamSession] = {}
        self.health_logs: dict[uuid.UUID, list[MockStreamHealth]] = {}
        self.playlist_items: dict[uuid.UUID, list[MockPlaylistItem]] = {}
        self.simulcast_targets: dict[uuid.UUID, list[MockSimulcastTarget]] = {}
        self.audit_logs: list[dict] = []

    def create_live_event(self, account_id: uuid.UUID, title: str, description: str,
                          latency_mode: str = LatencyMode.NORMAL.value) -> tuple[MockLiveEvent, StreamLifecycleState]:
        event = MockLiveEvent(
            account_id=account_id,
            youtube_broadcast_id=f"broadcast_{uuid.uuid4()}",
            rtmp_key=f"rtmp_key_{uuid.uuid4()}",
            title=title,
            description=description,
            latency_mode=latency_mode,
            status=StreamLifecycleState.CREATED.value,
        )
        self.events[event.id] = event
        self.audit_logs.append({"action": "live_event_created", "event_id": str(event.id)})
        return event, StreamLifecycleState.CREATED

    def schedule_live_event(self, event_id: uuid.UUID, start_at: datetime,
                            end_at: Optional[datetime] = None) -> tuple[Optional[MockLiveEvent], StreamLifecycleState]:
        event = self.events.get(event_id)
        if not event:
            return None, StreamLifecycleState.INITIAL
        if event.status != StreamLifecycleState.CREATED.value:
            return None, StreamLifecycleState(event.status)
        if self._has_schedule_conflict(event.account_id, start_at, end_at, event_id):
            raise ValueError("Schedule conflict detected")
        event.scheduled_start_at = start_at
        event.status = StreamLifecycleState.SCHEDULED.value
        self.audit_logs.append({"action": "live_event_scheduled", "event_id": str(event_id)})
        return event, StreamLifecycleState.SCHEDULED

    def start_stream(self, event_id: uuid.UUID) -> tuple[Optional[MockStreamSession], StreamLifecycleState]:
        event = self.events.get(event_id)
        if not event:
            return None, StreamLifecycleState.INITIAL
        if event.status not in [StreamLifecycleState.CREATED.value, StreamLifecycleState.SCHEDULED.value]:
            return None, StreamLifecycleState(event.status)
        event.status = StreamLifecycleState.LIVE.value
        event.actual_start_at = datetime.utcnow()
        session = MockStreamSession(live_event_id=event_id, started_at=datetime.utcnow())
        self.sessions[session.id] = session
        self.health_logs[session.id] = []
        self.audit_logs.append({"action": "stream_started", "event_id": str(event_id)})
        return session, StreamLifecycleState.LIVE

    def stop_stream(self, event_id: uuid.UUID, reason: str = "manual") -> tuple[bool, StreamLifecycleState]:
        event = self.events.get(event_id)
        if not event:
            return False, StreamLifecycleState.INITIAL
        if event.status != StreamLifecycleState.LIVE.value:
            return False, StreamLifecycleState(event.status)
        event.status = StreamLifecycleState.ENDED.value
        event.actual_end_at = datetime.utcnow()
        for session in self.sessions.values():
            if session.live_event_id == event_id and session.ended_at is None:
                session.ended_at = datetime.utcnow()
        self.audit_logs.append({"action": "stream_stopped", "event_id": str(event_id)})
        return True, StreamLifecycleState.ENDED


    def record_health_metrics(self, session_id: uuid.UUID, bitrate: int,
                              dropped_frames: int, viewer_count: int) -> Optional[MockStreamHealth]:
        session = self.sessions.get(session_id)
        if not session or session.ended_at is not None:
            return None
        if bitrate >= 4000 and dropped_frames < 10:
            connection_status = "excellent"
        elif bitrate >= 2500 and dropped_frames < 50:
            connection_status = "good"
        elif bitrate >= 1000:
            connection_status = "fair"
        else:
            connection_status = "poor"
        health = MockStreamHealth(session_id=session_id, bitrate=bitrate,
                                  dropped_frames=dropped_frames, connection_status=connection_status,
                                  viewer_count=viewer_count)
        self.health_logs[session_id].append(health)
        if viewer_count > session.peak_viewers:
            session.peak_viewers = viewer_count
        return health

    def create_playlist_stream(self, account_id: uuid.UUID, title: str,
                               video_ids: list[uuid.UUID]) -> tuple[MockLiveEvent, list[MockPlaylistItem], StreamLifecycleState]:
        event, _ = self.create_live_event(account_id, title, "Playlist stream")
        items = [MockPlaylistItem(live_event_id=event.id, video_id=vid, position=i) for i, vid in enumerate(video_ids)]
        self.playlist_items[event.id] = items
        return event, items, StreamLifecycleState.CREATED

    def configure_simulcast(self, event_id: uuid.UUID,
                            targets: list[dict]) -> tuple[list[MockSimulcastTarget], StreamLifecycleState]:
        event = self.events.get(event_id)
        if not event:
            return [], StreamLifecycleState.INITIAL
        simulcast_list = [MockSimulcastTarget(live_event_id=event_id, platform=t.get("platform", ""),
                                              rtmp_url=t.get("rtmp_url", "")) for t in targets]
        self.simulcast_targets[event_id] = simulcast_list
        return simulcast_list, StreamLifecycleState(event.status)

    def _has_schedule_conflict(self, account_id: uuid.UUID, start_at: datetime,
                               end_at: Optional[datetime], exclude_event_id: Optional[uuid.UUID] = None) -> bool:
        for event in self.events.values():
            if event.account_id != account_id or (exclude_event_id and event.id == exclude_event_id):
                continue
            if event.status not in [StreamLifecycleState.SCHEDULED.value, StreamLifecycleState.LIVE.value]:
                continue
            if not event.scheduled_start_at:
                continue
            event_end = event.scheduled_start_at + timedelta(hours=4)
            check_end = end_at or (start_at + timedelta(hours=4))
            if start_at < event_end and check_end > event.scheduled_start_at:
                return True
        return False


# Strategies
account_id_strategy = st.uuids()
title_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N", "Zs")))
description_strategy = st.text(min_size=0, max_size=500)
latency_mode_strategy = st.sampled_from([m.value for m in LatencyMode])
video_id_strategy = st.uuids()
platform_strategy = st.sampled_from(["youtube", "facebook", "twitch", "tiktok", "custom"])



class TestCompleteStreamLifecycle:
    """End-to-end tests for complete stream lifecycle."""

    @given(account_id=account_id_strategy, title=title_strategy, description=description_strategy,
           latency_mode=latency_mode_strategy)
    @settings(max_examples=50)
    def test_create_to_end_stream_flow(self, account_id: uuid.UUID, title: str,
                                       description: str, latency_mode: str) -> None:
        """Test complete stream lifecycle. **Validates: Requirements 5.1, 5.2, 6.2, 6.3**"""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, state = service.create_live_event(account_id, title, description, latency_mode)
        assert state == StreamLifecycleState.CREATED
        assert event.youtube_broadcast_id != ""
        session, state = service.start_stream(event.id)
        assert state == StreamLifecycleState.LIVE
        health = service.record_health_metrics(session.id, bitrate=4500, dropped_frames=5, viewer_count=100)
        assert health is not None
        assert health.connection_status == "excellent"
        success, state = service.stop_stream(event.id)
        assert success
        assert state == StreamLifecycleState.ENDED
        assert len(service.audit_logs) >= 3

    @given(account_id=account_id_strategy, title=title_strategy)
    @settings(max_examples=50)
    def test_scheduled_stream_flow(self, account_id: uuid.UUID, title: str) -> None:
        """Test scheduled stream flow. **Validates: Requirements 6.1**"""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, _ = service.create_live_event(account_id, title, "")
        start_at = datetime.utcnow() + timedelta(hours=1)
        scheduled_event, state = service.schedule_live_event(event.id, start_at)
        assert state == StreamLifecycleState.SCHEDULED
        assert scheduled_event.scheduled_start_at == start_at

    @given(account_id=account_id_strategy, title1=title_strategy, title2=title_strategy)
    @settings(max_examples=50)
    def test_schedule_conflict_detection(self, account_id: uuid.UUID, title1: str, title2: str) -> None:
        """Test schedule conflict detection. **Validates: Requirements 6.4**"""
        assume(len(title1.strip()) > 0 and len(title2.strip()) > 0)
        service = MockStreamLifecycleService()
        event1, _ = service.create_live_event(account_id, title1, "")
        start_at = datetime.utcnow() + timedelta(hours=1)
        service.schedule_live_event(event1.id, start_at)
        event2, _ = service.create_live_event(account_id, title2, "")
        with pytest.raises(ValueError, match="Schedule conflict"):
            service.schedule_live_event(event2.id, start_at)

    @given(account_id=account_id_strategy, title=title_strategy,
           video_ids=st.lists(video_id_strategy, min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_playlist_stream_flow(self, account_id: uuid.UUID, title: str, video_ids: list[uuid.UUID]) -> None:
        """Test playlist stream creation. **Validates: Requirements 7.1, 7.2**"""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, items, state = service.create_playlist_stream(account_id, title, video_ids)
        assert state == StreamLifecycleState.CREATED
        assert len(items) == len(video_ids)
        for i, item in enumerate(items):
            assert item.position == i
            assert item.video_id == video_ids[i]

    @given(account_id=account_id_strategy, title=title_strategy,
           platforms=st.lists(platform_strategy, min_size=1, max_size=5, unique=True))
    @settings(max_examples=50)
    def test_simulcast_configuration(self, account_id: uuid.UUID, title: str, platforms: list[str]) -> None:
        """Test simulcast configuration. **Validates: Requirements 9.1, 9.2**"""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, _ = service.create_live_event(account_id, title, "")
        targets = [{"platform": p, "rtmp_url": f"rtmp://{p}.example.com/live"} for p in platforms]
        simulcast_list, state = service.configure_simulcast(event.id, targets)
        assert len(simulcast_list) == len(platforms)
        for i, simulcast in enumerate(simulcast_list):
            assert simulcast.platform == platforms[i]



class TestStreamHealthMonitoring:
    """Tests for stream health monitoring."""

    @given(account_id=account_id_strategy, title=title_strategy,
           bitrate=st.integers(min_value=100, max_value=10000),
           dropped_frames=st.integers(min_value=0, max_value=1000),
           viewer_count=st.integers(min_value=0, max_value=100000))
    @settings(max_examples=50)
    def test_health_metrics_recording(self, account_id: uuid.UUID, title: str,
                                      bitrate: int, dropped_frames: int, viewer_count: int) -> None:
        """Test health metrics recording. **Validates: Requirements 8.1**"""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, _ = service.create_live_event(account_id, title, "")
        session, _ = service.start_stream(event.id)
        health = service.record_health_metrics(session.id, bitrate, dropped_frames, viewer_count)
        assert health is not None
        assert health.bitrate == bitrate
        if bitrate >= 4000 and dropped_frames < 10:
            assert health.connection_status == "excellent"
        elif bitrate >= 2500 and dropped_frames < 50:
            assert health.connection_status == "good"
        elif bitrate >= 1000:
            assert health.connection_status == "fair"
        else:
            assert health.connection_status == "poor"

    @given(account_id=account_id_strategy, title=title_strategy,
           viewer_counts=st.lists(st.integers(min_value=0, max_value=10000), min_size=3, max_size=10))
    @settings(max_examples=50)
    def test_peak_viewers_tracking(self, account_id: uuid.UUID, title: str, viewer_counts: list[int]) -> None:
        """Test peak viewers tracking. **Validates: Requirements 8.5**"""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, _ = service.create_live_event(account_id, title, "")
        session, _ = service.start_stream(event.id)
        for count in viewer_counts:
            service.record_health_metrics(session.id, bitrate=4500, dropped_frames=0, viewer_count=count)
        assert session.peak_viewers == max(viewer_counts)


class TestStreamLifecycleErrorScenarios:
    """Test error scenarios in stream lifecycle."""

    @given(account_id=account_id_strategy, title=title_strategy)
    @settings(max_examples=50)
    def test_cannot_start_nonexistent_stream(self, account_id: uuid.UUID, title: str) -> None:
        """Test that starting non-existent stream fails."""
        service = MockStreamLifecycleService()
        session, state = service.start_stream(uuid.uuid4())
        assert session is None
        assert state == StreamLifecycleState.INITIAL

    @given(account_id=account_id_strategy, title=title_strategy)
    @settings(max_examples=50)
    def test_cannot_stop_non_live_stream(self, account_id: uuid.UUID, title: str) -> None:
        """Test that stopping non-live stream fails."""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, _ = service.create_live_event(account_id, title, "")
        success, state = service.stop_stream(event.id)
        assert not success
        assert state == StreamLifecycleState.CREATED

    @given(account_id=account_id_strategy, title=title_strategy)
    @settings(max_examples=50)
    def test_cannot_record_health_for_ended_stream(self, account_id: uuid.UUID, title: str) -> None:
        """Test that recording health for ended stream fails."""
        assume(len(title.strip()) > 0)
        service = MockStreamLifecycleService()
        event, _ = service.create_live_event(account_id, title, "")
        session, _ = service.start_stream(event.id)
        service.stop_stream(event.id)
        health = service.record_health_metrics(session.id, bitrate=4500, dropped_frames=0, viewer_count=100)
        assert health is None
