from pathlib import Path

import pytest

from app.services.repository_scanner import (
    get_repository_name,
    scan_repository,
    validate_github_url,
)


def test_validate_github_url_accepts_valid_url():
    validate_github_url("https://github.com/Karthik-Malapati/ai-code-review-agent")


def test_validate_github_url_rejects_non_github_url():
    with pytest.raises(ValueError):
        validate_github_url("https://example.com/user/project")


def test_validate_github_url_rejects_http():
    with pytest.raises(ValueError):
        validate_github_url("http://github.com/user/project")


def test_get_repository_name():
    repository_name = get_repository_name("https://github.com/user/my-project")

    assert repository_name == "my-project"


def test_get_repository_name_removes_git_suffix():
    repository_name = get_repository_name("https://github.com/user/my-project.git")

    assert repository_name == "my-project"


def test_scan_repository_finds_supported_files(
    tmp_path: Path,
):
    python_file = tmp_path / "main.py"
    javascript_file = tmp_path / "app.js"
    text_file = tmp_path / "notes.txt"

    python_file.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    javascript_file.write_text(
        "console.log('hello')",
        encoding="utf-8",
    )

    text_file.write_text(
        "ignore me",
        encoding="utf-8",
    )

    files = scan_repository(tmp_path)

    discovered = {file_path.name: language for file_path, language in files}

    assert "main.py" in discovered
    assert discovered["main.py"] == "python"

    assert "app.js" in discovered
    assert discovered["app.js"] == "javascript"

    assert "notes.txt" not in discovered


def test_scan_repository_ignores_venv(
    tmp_path: Path,
):
    ignored_directory = tmp_path / ".venv"
    ignored_directory.mkdir()

    ignored_file = ignored_directory / "hidden.py"
    ignored_file.write_text(
        "print('ignore me')",
        encoding="utf-8",
    )

    files = scan_repository(tmp_path)

    paths = [file_path for file_path, _language in files]

    assert ignored_file not in paths
