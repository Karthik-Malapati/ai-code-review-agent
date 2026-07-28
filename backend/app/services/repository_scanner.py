import subprocess
from pathlib import Path
from urllib.parse import urlparse


class RepositoryCloneError(Exception):
    """Raised when a GitHub repository cannot be cloned."""


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
}


IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "target",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
}


def validate_github_url(repository_url: str) -> None:
    """
    Ensure that the supplied URL points to github.com and uses HTTPS.
    """

    parsed_url = urlparse(repository_url)

    if parsed_url.scheme != "https":
        raise ValueError("Only HTTPS GitHub repository URLs are supported.")

    if parsed_url.hostname not in {"github.com", "www.github.com"}:
        raise ValueError("Only GitHub repository URLs are supported.")

    path_parts = [part for part in parsed_url.path.strip("/").split("/") if part]

    if len(path_parts) != 2:
        raise ValueError(
            "The URL must follow this format: https://github.com/owner/repository"
        )


def get_repository_name(repository_url: str) -> str:
    """
    Extract the repository name from a GitHub URL.
    """

    parsed_url = urlparse(repository_url)
    repository_name = Path(parsed_url.path).name

    repository_name = repository_name.removesuffix(".git")

    if not repository_name:
        raise ValueError("The repository name could not be determined.")

    return repository_name


def clone_repository(
    repository_url: str,
    destination: Path,
) -> Path:
    """
    Clone a public GitHub repository into the supplied destination.
    """

    validate_github_url(repository_url)

    repository_name = get_repository_name(repository_url)
    repository_path = destination / repository_name

    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repository_url,
                str(repository_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    except FileNotFoundError as error:
        raise RepositoryCloneError(
            "Git is not installed or cannot be found."
        ) from error

    except subprocess.TimeoutExpired as error:
        raise RepositoryCloneError(
            "Repository cloning timed out after 60 seconds."
        ) from error

    except subprocess.CalledProcessError as error:
        git_error = error.stderr.strip()

        raise RepositoryCloneError(
            git_error or "The repository could not be cloned."
        ) from error

    return repository_path


def should_ignore_file(
    file_path: Path,
    repository_path: Path,
) -> bool:
    """
    Return True when a file is inside an ignored directory.
    """

    relative_path = file_path.relative_to(repository_path)

    return any(
        directory_name in IGNORED_DIRECTORIES
        for directory_name in relative_path.parts[:-1]
    )


def scan_repository(
    repository_path: Path,
) -> list[tuple[Path, str]]:
    """
    Find supported source-code files inside a repository.

    Returns a list containing:
    - The complete file path
    - The detected programming language
    """

    source_files: list[tuple[Path, str]] = []

    for file_path in repository_path.rglob("*"):
        if not file_path.is_file():
            continue

        if should_ignore_file(
            file_path=file_path,
            repository_path=repository_path,
        ):
            continue

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        language = SUPPORTED_EXTENSIONS[extension]

        source_files.append(
            (
                file_path,
                language,
            )
        )

    return sorted(
        source_files,
        key=lambda item: str(item[0]),
    )
