
import pytest
from pathlib import Path

from src.file_organizer import (
    calculate_hash,
    format_size,
    get_category
)


# Test 1: File hashing
def test_calculate_hash(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    result = calculate_hash(test_file)

    assert isinstance(result, str)
    assert len(result) == 64


# Test 2: Same content should produce same hash
def test_duplicate_hash(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Same content")
    file2.write_text("Same content")

    assert calculate_hash(file1) == calculate_hash(file2)


# Test 3: Different content should produce different hash
def test_different_hash(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("First file")
    file2.write_text("Second file")

    assert calculate_hash(file1) != calculate_hash(file2)


# Test 4: File category detection
def test_get_category():
    assert get_category(Path("photo.jpg")) == "Images"
    assert get_category(Path("resume.pdf")) == "Documents"
    assert get_category(Path("unknown.zip")) == "Others"


# Test 5: File size formatting
def test_format_size():
    assert format_size(500) == "500 Bytes"
    assert format_size(2048) == "2.00 KB"
    assert format_size(1048576) == "1.00 MB"

