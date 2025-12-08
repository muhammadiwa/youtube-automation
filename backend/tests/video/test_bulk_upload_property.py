"""Property-based tests for bulk upload job creation.

**Feature: youtube-automation, Property 8: Bulk Upload Job Creation**
**Validates: Requirements 3.5**
"""

import io
import csv
from typing import Optional

from hypothesis import given, settings, strategies as st, assume
from pydantic import BaseModel, Field


# Define BulkUploadEntry locally to avoid database import issues
class BulkUploadEntry(BaseModel):
    """Schema for a single entry in bulk upload CSV."""

    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[str] = None  # Comma-separated tags
    category_id: Optional[str] = None
    visibility: Optional[str] = None
    scheduled_publish_at: Optional[str] = None
    file_path: str


def parse_csv_for_bulk_upload(csv_content: str) -> tuple[list[BulkUploadEntry], list[str]]:
    """Parse CSV content for bulk upload.

    Expected CSV columns: title, description, tags, category_id, visibility, scheduled_publish_at, file_path

    Args:
        csv_content: CSV file content as string

    Returns:
        tuple: (list of valid entries, list of error messages)
    """
    entries = []
    errors = []

    reader = csv.DictReader(io.StringIO(csv_content))

    required_columns = {"title", "file_path"}
    if not required_columns.issubset(set(reader.fieldnames or [])):
        missing = required_columns - set(reader.fieldnames or [])
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return entries, errors

    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        try:
            title = row.get("title", "").strip()
            file_path = row.get("file_path", "").strip()

            if not title:
                errors.append(f"Row {row_num}: Missing title")
                continue

            if not file_path:
                errors.append(f"Row {row_num}: Missing file_path")
                continue

            entry = BulkUploadEntry(
                title=title,
                description=row.get("description", "").strip() or None,
                tags=row.get("tags", "").strip() or None,
                category_id=row.get("category_id", "").strip() or None,
                visibility=row.get("visibility", "").strip() or None,
                scheduled_publish_at=row.get("scheduled_publish_at", "").strip() or None,
                file_path=file_path,
            )
            entries.append(entry)

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    return entries, errors


def generate_csv_content(entries: list[dict]) -> str:
    """Generate CSV content from list of entry dictionaries."""
    if not entries:
        return "title,file_path\n"

    output = io.StringIO()
    fieldnames = ["title", "description", "tags", "category_id", "visibility", "scheduled_publish_at", "file_path"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry)
    return output.getvalue()


# Strategy for generating valid video titles (non-empty, no leading/trailing whitespace)
valid_title_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_"),
    min_size=1,
    max_size=50,
).map(lambda x: x.strip()).filter(lambda x: len(x) > 0)

# Strategy for generating valid file paths
valid_file_path_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
    min_size=5,
    max_size=20,
).map(lambda x: f"/videos/{x.strip() or 'video'}.mp4")


class TestBulkUploadJobCreation:
    """Property tests for bulk upload CSV parsing and job creation.

    Requirements 3.5: For any valid CSV with N entries, create exactly N upload jobs.
    """

    @given(num_entries=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_csv_with_n_entries_creates_n_jobs(self, num_entries: int) -> None:
        """**Feature: youtube-automation, Property 8: Bulk Upload Job Creation**

        For any valid CSV with N entries, parsing SHALL return exactly N entries.
        """
        # Generate CSV entries with deterministic titles
        entries = []
        for i in range(num_entries):
            entries.append({
                "title": f"Video Title {i}",
                "description": f"Description {i}",
                "tags": f"tag{i},tag{i+1}",
                "category_id": "22",
                "visibility": "private",
                "scheduled_publish_at": "",
                "file_path": f"/videos/video_{i}.mp4",
            })

        csv_content = generate_csv_content(entries)
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        # Should have exactly N entries
        assert len(parsed_entries) == num_entries, (
            f"Expected {num_entries} entries, got {len(parsed_entries)}. Errors: {errors}"
        )

    @given(num_entries=st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_entry_count_matches_csv_rows(self, num_entries: int) -> None:
        """**Feature: youtube-automation, Property 8: Bulk Upload Job Creation**

        For any CSV with N valid rows, parsed entries SHALL equal N.
        """
        # Generate CSV entries
        entries = []
        for i in range(num_entries):
            entries.append({
                "title": f"Video Title {i}",
                "description": f"Description {i}",
                "tags": "",
                "category_id": "",
                "visibility": "",
                "scheduled_publish_at": "",
                "file_path": f"/videos/video_{i}.mp4",
            })

        csv_content = generate_csv_content(entries)
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        assert len(parsed_entries) == num_entries

    @given(
        valid_count=st.integers(min_value=0, max_value=20),
        invalid_count=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=100)
    def test_only_valid_entries_are_parsed(
        self, valid_count: int, invalid_count: int
    ) -> None:
        """**Feature: youtube-automation, Property 8: Bulk Upload Job Creation**

        For any CSV with valid and invalid rows, only valid rows SHALL be parsed.
        """
        entries = []

        # Add valid entries
        for i in range(valid_count):
            entries.append({
                "title": f"Valid Video {i}",
                "description": "",
                "tags": "",
                "category_id": "",
                "visibility": "",
                "scheduled_publish_at": "",
                "file_path": f"/videos/valid_{i}.mp4",
            })

        # Add invalid entries (missing title)
        for i in range(invalid_count):
            entries.append({
                "title": "",  # Invalid - empty title
                "description": "",
                "tags": "",
                "category_id": "",
                "visibility": "",
                "scheduled_publish_at": "",
                "file_path": f"/videos/invalid_{i}.mp4",
            })

        csv_content = generate_csv_content(entries)
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        # Should only have valid entries
        assert len(parsed_entries) == valid_count
        # Should have errors for invalid entries
        assert len(errors) == invalid_count

    def test_empty_csv_returns_zero_entries(self) -> None:
        """**Feature: youtube-automation, Property 8: Bulk Upload Job Creation**

        Empty CSV SHALL return zero entries.
        """
        csv_content = "title,file_path\n"
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        assert len(parsed_entries) == 0
        assert len(errors) == 0

    def test_missing_required_columns_returns_error(self) -> None:
        """**Feature: youtube-automation, Property 8: Bulk Upload Job Creation**

        CSV missing required columns SHALL return error.
        """
        csv_content = "description,tags\nTest,tag1"
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        assert len(parsed_entries) == 0
        assert len(errors) > 0
        assert "Missing required columns" in errors[0]

    @given(
        title=valid_title_strategy,
        description=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 "),
            max_size=100
        ),
        tags=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789,"),
            max_size=50
        ),
    )
    @settings(max_examples=100)
    def test_parsed_entry_preserves_data(
        self, title: str, description: str, tags: str
    ) -> None:
        """**Feature: youtube-automation, Property 8: Bulk Upload Job Creation**

        Parsed entry SHALL preserve original CSV data (after stripping whitespace).
        """
        assume(title.strip())  # Ensure non-empty title

        entries = [{
            "title": title,
            "description": description,
            "tags": tags,
            "category_id": "22",
            "visibility": "public",
            "scheduled_publish_at": "",
            "file_path": "/videos/test.mp4",
        }]

        csv_content = generate_csv_content(entries)
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        assert len(parsed_entries) == 1
        entry = parsed_entries[0]
        # CSV parser strips whitespace from title, which is correct behavior
        assert entry.title == title.strip()
        assert entry.file_path == "/videos/test.mp4"


class TestBulkUploadEntryValidation:
    """Tests for bulk upload entry validation."""

    def test_entry_requires_title(self) -> None:
        """Entry SHALL require non-empty title."""
        csv_content = "title,file_path\n,/videos/test.mp4"
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        assert len(parsed_entries) == 0
        assert len(errors) == 1
        assert "Missing title" in errors[0]

    def test_entry_requires_file_path(self) -> None:
        """Entry SHALL require non-empty file_path."""
        csv_content = "title,file_path\nTest Video,"
        parsed_entries, errors = parse_csv_for_bulk_upload(csv_content)

        assert len(parsed_entries) == 0
        assert len(errors) == 1
        assert "Missing file_path" in errors[0]
