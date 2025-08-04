#!/usr/bin/env python3
"""
Project-Wide Codebase Analysis Module

This module provides comprehensive analysis of entire codebases using pipeline pattern
with parallel processing. Designed for:
- File discovery & filtering
- Content aggregation & truncation
- Project structure inspection
- Tech stack analysis
- Architecture review

Author: Dr Muhammad Aizat Hawari
Date: 2025-01-20
Architecture: Pipeline Pattern with Parallel Execution
"""

import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import polyglot code analyzer for individual file analysis
try:
    from ..analyze_code import (
        AnalysisResult,
        AnalysisType,
        analyze_code,
        get_supported_languages,
        detect_language
    )

    CODE_ANALYZER_AVAILABLE = True
except ImportError:
    CODE_ANALYZER_AVAILABLE = False

# Import configuration management
try:
    from claude_gemini_mcp.config import get_config

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


# Analysis scope types for codebase analysis
class AnalysisScope(Enum):
    """Analysis scope types for codebase analysis"""

    STRUCTURE = "structure"
    SECURITY = "security"
    PERFORMANCE = "performance"
    PATTERNS = "patterns"
    ALL = "all"


# Technology stack categories
class TechStackCategory(Enum):
    """Technology stack categories"""

    FRAMEWORK = "framework"
    DATABASE = "database"
    TESTING = "testing"
    BUILD_TOOL = "build_tool"
    DEPLOYMENT = "deployment"
    LANGUAGE = "language"
    UTILITY = "utility"


# Information about a discovered file
@dataclass
class FileInfo:
    """Information about a discovered file"""

    path: Path
    relative_path: str
    size: int
    extension: str
    language: str
    is_test: bool = False
    is_config: bool = False
    is_documentation: bool = False
    line_count: int = 0
    hash: Optional[str] = None


# Project structure analysis results
@dataclass
class ProjectStructure:
    """Project structure analysis results"""

    root_path: Optional[Path] = None
    total_files: int = 0
    total_lines: int = 0
    total_size: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    directories: List[str] = field(default_factory=list)
    file_extensions: Dict[str, int] = field(default_factory=dict)
    package_structure: Dict[str, Any] = field(default_factory=dict)
    circular_imports: List[Tuple[str, str]] = field(default_factory=list)
    missing_inits: List[str] = field(default_factory=list)


# Technology stack analysis results
@dataclass
class TechStackInfo:
    """Technology stack analysis results"""

    frameworks: Dict[str, str] = field(default_factory=dict)  # name -> version
    databases: Set[str] = field(default_factory=set)
    testing_frameworks: Set[str] = field(default_factory=set)
    build_tools: Set[str] = field(default_factory=set)
    deployment_tools: Set[str] = field(default_factory=set)
    languages: Dict[str, str] = field(default_factory=dict)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)


# Architecture pattern analysis results
@dataclass
class ArchitectureInfo:
    """Architecture pattern analysis results"""

    patterns: List[str] = field(default_factory=list)
    layers: Dict[str, List[str]] = field(default_factory=dict)
    design_principles: List[str] = field(default_factory=list)
    architectural_issues: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    coupling_score: float = 0.0
    cohesion_score: float = 0.0


# Overall codebase statistics
@dataclass
class CodebaseStats:
    """Overall codebase statistics"""

    discovery_time: float = 0.0
    analysis_time: float = 0.0
    total_time: float = 0.0
    files_analyzed: int = 0
    files_skipped: int = 0
    errors_encountered: int = 0
    cache_hits: int = 0
    payload_size: int = 0
    truncated_files: int = 0


# Complete codebase analysis results
@dataclass
class CodebaseAnalysisResult:
    """Complete codebase analysis results"""

    project_report: Dict[str, Any] = field(default_factory=dict)
    prompt_payload: str = ""
    stats: CodebaseStats = field(default_factory=CodebaseStats)
    structure: ProjectStructure = field(default_factory=ProjectStructure)
    tech_stack: TechStackInfo = field(default_factory=TechStackInfo)
    architecture: ArchitectureInfo = field(default_factory=ArchitectureInfo)
    file_analyses: List[AnalysisResult] = field(default_factory=list)
    error: Optional[str] = None


# Base exception for codebase analysis errors
class CodebaseAnalysisError(Exception):
    """Base exception for codebase analysis errors"""


# Raised when file discovery fails
class FileDiscoveryError(CodebaseAnalysisError):
    """Raised when file discovery fails"""


# Raised when content aggregation fails
class ContentAggregationError(CodebaseAnalysisError):
    """Raised when content aggregation fails"""


# Raised when project structure analysis fails
class ProjectStructureError(CodebaseAnalysisError):
    """Raised when project structure analysis fails"""


# File filtering and discovery utilities
class FileFilter:
    """File filtering and discovery utilities"""

    # Default file extensions to analyze
    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".cs": "csharp",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".md": "markdown",
        ".rst": "restructuredtext",
        ".txt": "text",
    }

    # Directories to skip by default
    DEFAULT_SKIP_DIRS = {
        "__pycache__",
        ".pytest_cache",
        ".tox",
        ".coverage",
        "node_modules",
        ".git",
        ".svn",
        ".hg",
        ".bzr",
        "venv",
        ".venv",
        "env",
        ".env",
        "virtualenv",
        "build",
        "dist",
        ".build",
        ".dist",
        ".idea",
        ".vscode",
        ".vs",
        ".settings",
        "target",
        "bin",
        "obj",
        "out",
        "logs",
        "log",
        "tmp",
        "temp",
        ".tmp",
        ".temp",
    }

    # Files to skip
    DEFAULT_SKIP_FILES = {
        ".gitignore",
        ".gitkeep",
        ".DS_Store",
        "Thumbs.db",
        "package-lock.json",
        "yarn.lock",
        "Pipfile.lock",
        "poetry.lock",
        "Cargo.lock",
        "go.sum",
    }

    # Check if a file should be analyzed
    @classmethod
    def should_analyze_file(cls, file_path: Path, config: Dict[str, Any]) -> bool:
        """Check if a file should be analyzed"""
        # Check file extension
        if file_path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            return False

        # Check if file should be skipped
        if file_path.name in cls.DEFAULT_SKIP_FILES:
            return False

        # Check custom skip patterns
        skip_patterns = config.get("skip_patterns", [])
        for pattern in skip_patterns:
            if re.search(pattern, str(file_path)):
                return False

        # Check file size limits
        max_file_size = config.get("max_file_size", 1024 * 1024)  # 1MB default
        try:
            if file_path.stat().st_size > max_file_size:
                return False
        except OSError:
            return False

        return True

    # Check if a directory should be skipped
    @classmethod
    def should_skip_directory(cls, dir_path: Path, config: Dict[str, Any]) -> bool:
        """Check if a directory should be skipped"""
        dir_name = dir_path.name.lower()

        # Check default skip directories
        if dir_name in cls.DEFAULT_SKIP_DIRS:
            return True

        # Check custom skip directories
        skip_dirs = config.get("skip_directories", [])
        if dir_name in skip_dirs:
            return True

        # Check if it's a hidden directory (starts with .)
        if dir_name.startswith(".") and dir_name not in config.get(
            "include_hidden", []
        ):
            return True

        return False


# File discovery and filtering pipeline stage
class FileDiscoverer:
    """File discovery and filtering pipeline stage"""

    # Initialize file discoverer
    def __init__(self, root_path: Path, config: Dict[str, Any]):
        self.root_path = root_path.resolve()
        self.config = config
        self.filter = FileFilter()

    # Discover and filter files in the project
    def discover_files(self) -> List[FileInfo]:
        """Discover and filter files in the project"""
        start_time = time.time()
        files = []

        try:
            for file_path in self._scan_directory(self.root_path):
                if self.filter.should_analyze_file(file_path, self.config):
                    file_info = self._create_file_info(file_path)
                    files.append(file_info)

            logger.info(
                f"Discovered {len(files)} files in {time.time() - start_time:.2f}s"
            )
            return files

        except Exception as e:
            raise FileDiscoveryError(f"File discovery failed: {str(e)}") from e

    # Efficiently scan directory using os.scandir()
    def _scan_directory(self, path: Path):
        """Efficiently scan directory using os.scandir()"""
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)

                    if entry.is_dir():
                        if not self.filter.should_skip_directory(
                            entry_path, self.config
                        ):
                            yield from self._scan_directory(entry_path)
                    elif entry.is_file():
                        yield entry_path
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot access {path}: {e}")

    # Create FileInfo object for a file
    def _create_file_info(self, file_path: Path) -> FileInfo:
        """Create FileInfo object for a file"""
        try:
            stat = file_path.stat()
            extension = file_path.suffix.lower()
            relative_path = str(file_path.relative_to(self.root_path))

            # Detect language
            language = FileFilter.SUPPORTED_EXTENSIONS.get(extension, "unknown")

            # Detect file type
            is_test = self._is_test_file(file_path)
            is_config = self._is_config_file(file_path)
            is_doc = self._is_documentation_file(file_path)

            # Count lines
            line_count = self._count_lines(file_path)

            return FileInfo(
                path=file_path,
                relative_path=relative_path,
                size=stat.st_size,
                extension=extension,
                language=language,
                is_test=is_test,
                is_config=is_config,
                is_documentation=is_doc,
                line_count=line_count,
            )
        except Exception as e:
            logger.warning(f"Error processing file {file_path}: {e}")
            return FileInfo(
                path=file_path,
                relative_path=str(file_path.relative_to(self.root_path)),
                size=0,
                extension=file_path.suffix.lower(),
                language="unknown",
            )

    # Check if file is a test file
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file"""
        name = file_path.name.lower()
        parent = file_path.parent.name.lower()

        test_patterns = ["test_", "_test", "test.", ".test"]
        test_dirs = ["test", "tests", "spec", "specs", "__tests__"]

        return (
            any(pattern in name for pattern in test_patterns)
            or parent in test_dirs
            or "test" in str(file_path).lower()
        )

    # Check if file is a configuration file
    def _is_config_file(self, file_path: Path) -> bool:
        """Check if file is a configuration file"""
        config_files = {
            "setup.py",
            "setup.cfg",
            "pyproject.toml",
            "requirements.txt",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
            "Makefile",
            "CMakeLists.txt",
            "build.gradle",
            ".gitignore",
            ".gitattributes",
            "LICENSE",
            "README.md",
        }
        config_extensions = {
            ".ini",
            ".cfg",
            ".conf",
            ".config",
            ".yaml",
            ".yml",
            ".toml",
            ".json",
        }

        return (
            file_path.name in config_files
            or file_path.suffix.lower() in config_extensions
        )

    # Check if file is documentation
    def _is_documentation_file(self, file_path: Path) -> bool:
        """Check if file is documentation"""
        doc_extensions = {".md", ".rst", ".txt", ".adoc", ".org"}
        doc_names = {"readme", "changelog", "license", "contributing", "authors"}

        return (
            file_path.suffix.lower() in doc_extensions
            or file_path.stem.lower() in doc_names
            or "doc" in str(file_path).lower()
        )

    # Count lines in a file efficiently
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file efficiently"""
        try:
            with open(file_path, "rb") as f:
                count = sum(1 for _ in f)
            return count
        except (OSError, UnicodeDecodeError):
            return 0


# Content aggregation and truncation pipeline stage
class ContentAggregator:
    """Content aggregation and truncation pipeline stage"""

    # Initialize content aggregator
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Get global config instance for limits if available
        if CONFIG_AVAILABLE:
            _cfg = get_config()
            self.max_total_size = config.get(
                "max_total_size", _cfg.get_limit("max_codebase_size", 200_000)
            )
            self.max_file_size = config.get(
                "max_file_size", _cfg.get_limit("max_file_size", 50_000)
            )
        else:
            # Fallback to original behavior if config not available
            self.max_total_size = config.get("max_total_size", 200_000)  # 200KB default
            self.max_file_size = config.get("max_file_size", 50_000)  # 50KB per file
        self.encoding = config.get("encoding", "utf-8")

    # Aggregate file contents with intelligent truncation
    def aggregate_contents(self, files: List[FileInfo]) -> Dict[str, Any]:
        """Aggregate file contents with intelligent truncation"""
        start_time = time.time()

        try:
            # Sort files by priority for truncation decisions
            prioritized_files = self._prioritize_files(files)

            aggregated = {
                "files": {},
                "truncated_files": [],
                "skipped_files": [],
                "total_size": 0,
                "stats": {
                    "files_included": 0,
                    "files_truncated": 0,
                    "files_skipped": 0,
                },
            }

            current_size = 0

            # Process files in priority order
            for file_info in prioritized_files:
                try:
                    content = self._read_file_content(file_info.path)
                    if content is None:
                        aggregated["skipped_files"].append(file_info.relative_path)
                        aggregated["stats"]["files_skipped"] += 1
                        continue

                    # Check if adding this file would exceed limits
                    content_size = len(content)
                    if current_size + content_size > self.max_total_size:
                        # Try to truncate the file to fit
                        remaining_space = self.max_total_size - current_size
                        if (
                            remaining_space > 1000
                        ):  # Only truncate if we have reasonable space
                            content = self._truncate_content(content, remaining_space)
                            content_size = len(content)
                            aggregated["truncated_files"].append(
                                file_info.relative_path
                            )
                            aggregated["stats"]["files_truncated"] += 1
                        else:
                            aggregated["skipped_files"].append(file_info.relative_path)
                            aggregated["stats"]["files_skipped"] += 1
                            continue

                    # Add file content
                    aggregated["files"][file_info.relative_path] = {
                        "content": content,
                        "language": file_info.language,
                        "size": content_size,
                        "lines": content.count("\n") + 1,
                        "is_test": file_info.is_test,
                        "is_config": file_info.is_config,
                        "is_documentation": file_info.is_documentation,
                    }
                    # Update current size
                    current_size += content_size
                    aggregated["stats"]["files_included"] += 1

                    # Stop if we're close to the limit
                    if current_size >= self.max_total_size * 0.95:
                        break
                # Exception handling
                except Exception as e:
                    logger.warning(f"Error processing file {file_info.path}: {e}")
                    aggregated["skipped_files"].append(file_info.relative_path)
                    aggregated["stats"]["files_skipped"] += 1

            aggregated["total_size"] = current_size

            logger.info(
                f"Aggregated {aggregated['stats']['files_included']} files "
                f"({current_size:,} bytes) in {time.time() - start_time:.2f}s"
            )

            return aggregated

        except Exception as e:
            raise ContentAggregationError(
                f"Content aggregation failed: {str(e)}"
            ) from e

    # Prioritize files for inclusion based on importance
    def _prioritize_files(self, files: List[FileInfo]) -> List[FileInfo]:
        """Prioritize files for inclusion based on importance"""

        def priority_score(file_info: FileInfo) -> int:
            score = 0

            # Configuration files are high priority
            if file_info.is_config:
                score += 100

            # Main source files over tests
            if not file_info.is_test:
                score += 50

            # Python files get priority in Python projects
            if file_info.language == "python":
                score += 30

            # Smaller files are easier to include
            if file_info.size < 10000:  # < 10KB
                score += 20
            elif file_info.size < 50000:  # < 50KB
                score += 10

            # Files in root or important directories
            path_parts = Path(file_info.relative_path).parts
            if len(path_parts) <= 2:  # Root or one level deep
                score += 15

            # Important file names
            name = file_info.path.name.lower()
            if name in ["main.py", "app.py", "server.py", "index.js", "main.js"]:
                score += 25

            return score

        return sorted(files, key=priority_score, reverse=True)

    # Read file content with encoding detection
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding detection"""
        try:
            # Try UTF-8 first
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try other common encodings
            for encoding in ["latin-1", "cp1252", "utf-16"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
        except (OSError, PermissionError):
            pass

        return None

    # Intelligently truncate content to fit size limit
    def _truncate_content(self, content: str, max_size: int) -> str:
        """Intelligently truncate content to fit size limit"""
        if len(content) <= max_size:
            return content

        # Try to truncate at natural boundaries
        lines = content.split("\n")
        truncated_lines = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            if current_size + line_size > max_size - 100:  # Leave some margin
                break
            truncated_lines.append(line)
            current_size += line_size

        truncated_content = "\n".join(truncated_lines)
        truncated_content += "\n\n# ... [Content truncated due to size limits] ..."

        return truncated_content


# Project structure analysis pipeline stage
class ProjectStructureAnalyzer:
    """Project structure analysis pipeline stage"""

    # Initialize project structure analyzer
    def __init__(self, root_path: Path, config: Dict[str, Any]):
        self.root_path = root_path
        self.config = config

    # Build comprehensive project structure report
    def build_project_report(
        self, files: List[FileInfo], aggregated_content: Dict[str, Any]
    ) -> ProjectStructure:
        """Build comprehensive project structure report"""
        start_time = time.time()

        structure = ProjectStructure(root_path=self.root_path)

        try:
            # Basic statistics
            structure.total_files = len(files)
            structure.total_lines = sum(f.line_count for f in files)
            structure.total_size = sum(f.size for f in files)

            # Language distribution
            language_counter = Counter(f.language for f in files)
            structure.languages = dict(language_counter)

            # File extension distribution
            ext_counter = Counter(f.extension for f in files)
            structure.file_extensions = dict(ext_counter)

            # Directory structure
            directories = set()
            for file_info in files:
                path_parts = Path(file_info.relative_path).parts[
                    :-1
                ]  # Exclude filename
                for i in range(len(path_parts)):
                    directories.add("/".join(path_parts[: i + 1]))

            structure.directories = sorted(directories)

            # Analyze Python package structure if it's a Python project
            if "python" in structure.languages:
                structure.package_structure = self._analyze_python_packages(files)
                structure.circular_imports = self._detect_circular_imports(
                    files, aggregated_content
                )
                structure.missing_inits = self._find_missing_init_files(files)

            logger.info(f"Built project structure in {time.time() - start_time:.2f}s")
            return structure

        except Exception as e:
            logger.error(f"Project structure analysis failed: {e}")
            return structure

    # Analyze Python package structure
    def _analyze_python_packages(self, files: List[FileInfo]) -> Dict[str, Any]:
        """Analyze Python package structure"""
        packages = defaultdict(list)
        modules = []

        for file_info in files:
            if file_info.language == "python" and not file_info.is_test:
                path_parts = Path(file_info.relative_path).parts

                if len(path_parts) == 1:  # Root module
                    modules.append(file_info.relative_path)
                else:
                    package_path = "/".join(path_parts[:-1])
                    packages[package_path].append(path_parts[-1])

        return {
            "packages": dict(packages),
            "root_modules": modules,
            "total_packages": len(packages),
            "total_modules": len(modules)
            + sum(len(modules) for modules in packages.values()),
        }

    # Detect potential circular imports
    def _detect_circular_imports(
        self, files: List[FileInfo], aggregated_content: Dict[str, Any]
    ) -> List[Tuple[str, str]]:
        """Detect potential circular imports"""
        # This is a simplified implementation
        # A full implementation would use AST parsing and graph analysis
        imports = defaultdict(set)

        for file_path, file_data in aggregated_content.get("files", {}).items():
            if file_data["language"] == "python":
                content = file_data["content"]
                # Simple regex-based import detection
                import_lines = re.findall(
                    r"^(?:from|import)\s+([^\s#]+)", content, re.MULTILINE
                )
                for imp in import_lines:
                    if "." in imp:  # Relative import
                        imports[file_path].add(imp.split(".")[0])
                    else:
                        imports[file_path].add(imp)

        # Simple circular detection (would need graph algorithm for full detection)
        circular = []
        for file_a, imports_a in imports.items():
            for file_b, imports_b in imports.items():
                if file_a != file_b:
                    module_a = Path(file_a).stem
                    module_b = Path(file_b).stem
                    if module_b in imports_a and module_a in imports_b:
                        circular.append((file_a, file_b))

        return circular

    # Find directories that should have __init__.py files
    def _find_missing_init_files(self, files: List[FileInfo]) -> List[str]:
        """Find directories that should have __init__.py files"""
        python_dirs = set()
        init_files = set()

        for file_info in files:
            if file_info.language == "python":
                dir_path = str(Path(file_info.relative_path).parent)
                if dir_path != ".":
                    python_dirs.add(dir_path)

                if file_info.path.name == "__init__.py":
                    init_files.add(str(Path(file_info.relative_path).parent))

        return sorted(python_dirs - init_files)


# Technology stack detection pipeline stage
class TechStackDetector:
    """Technology stack detection pipeline stage"""

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Python frameworks
        "django": [r"django", r"Django", r"manage\.py"],
        "flask": [r"from flask", r"import flask", r"Flask\("],
        "fastapi": [r"from fastapi", r"import fastapi", r"FastAPI\("],
        "pyramid": [r"from pyramid", r"import pyramid"],
        "tornado": [r"from tornado", r"import tornado"],
        "bottle": [r"from bottle", r"import bottle"],
        # JavaScript frameworks
        "react": [r'"react"', r'from ["\']react["\']', r"React\."],
        "vue": [r'"vue"', r'from ["\']vue["\']', r"Vue\."],
        "angular": [r'"@angular', r'from ["\']@angular'],
        "express": [r'"express"', r'require\(["\']express["\']'],
        "next": [r'"next"', r'from ["\']next["\']'],
        "nuxt": [r'"nuxt"', r'from ["\']nuxt["\']'],
        # Other frameworks
        "spring": [r"import org\.springframework", r"@SpringBootApplication"],
        "rails": [r'gem ["\']rails["\']', r"Rails\.application"],
    }

    DATABASE_PATTERNS = {
        "postgresql": [r"psycopg2", r"postgresql://", r"postgres://"],
        "mysql": [r"mysql", r"pymysql", r"MySQLdb"],
        "sqlite": [r"sqlite3", r"\.db$", r"\.sqlite$"],
        "mongodb": [r"pymongo", r"mongodb://", r"mongoose"],
        "redis": [r"redis", r"redis://"],
        "elasticsearch": [r"elasticsearch", r"elastic"],
    }

    # Initialize technology stack detector
    def __init__(self, root_path: Path, config: Dict[str, Any]):
        self.root_path = root_path
        self.config = config

    # Analyze technology stack from files and content
    def analyze_tech_stack(
        self, files: List[FileInfo], aggregated_content: Dict[str, Any]
    ) -> TechStackInfo:
        """Analyze technology stack from files and content"""
        start_time = time.time()

        tech_stack = TechStackInfo()

        try:
            # Analyze dependency files
            self._analyze_dependency_files(files, tech_stack)

            # Analyze source code patterns
            self._analyze_code_patterns(aggregated_content, tech_stack)

            # Analyze configuration files
            self._analyze_config_files(files, aggregated_content, tech_stack)

            logger.info(f"Analyzed tech stack in {time.time() - start_time:.2f}s")
            return tech_stack

        except Exception as e:
            logger.error(f"Tech stack analysis failed: {e}")
            return tech_stack

    # Analyze dependency files for technology information
    def _analyze_dependency_files(
        self, files: List[FileInfo], tech_stack: TechStackInfo
    ):
        """Analyze dependency files for technology information"""
        for file_info in files:
            file_name = file_info.path.name.lower()

            if file_name == "requirements.txt":
                self._parse_requirements_txt(file_info.path, tech_stack)
            elif file_name == "pyproject.toml":
                self._parse_pyproject_toml(file_info.path, tech_stack)
            elif file_name == "package.json":
                self._parse_package_json(file_info.path, tech_stack)
            elif file_name == "pom.xml":
                self._parse_pom_xml(file_info.path, tech_stack)
            elif file_name == "build.gradle":
                self._parse_build_gradle(file_info.path, tech_stack)

    # Analyze source code for framework patterns
    def _analyze_code_patterns(
        self, aggregated_content: Dict[str, Any], tech_stack: TechStackInfo
    ):
        """Analyze source code for framework patterns"""
        all_content = "\n".join(
            file_data["content"]
            for file_data in aggregated_content.get("files", {}).values()
        )

        # Detect frameworks
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, all_content, re.IGNORECASE):
                    tech_stack.frameworks[framework] = "detected"
                    break

        # Detect databases
        for db, patterns in self.DATABASE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, all_content, re.IGNORECASE):
                    tech_stack.databases.add(db)
                    break

    # Analyze configuration files for deployment and build tools
    def _analyze_config_files(
        self,
        files: List[FileInfo],
        aggregated_content: Dict[str, Any],
        tech_stack: TechStackInfo,
    ):
        """Analyze configuration files for deployment and build tools"""
        for file_info in files:
            file_name = file_info.path.name.lower()

            if file_name == "dockerfile":
                tech_stack.deployment_tools.add("docker")
            elif file_name == "docker-compose.yml":
                tech_stack.deployment_tools.add("docker-compose")
            elif file_name == "makefile":
                tech_stack.build_tools.add("make")
            elif file_name.endswith(".jenkinsfile"):
                tech_stack.deployment_tools.add("jenkins")
            elif file_name == ".github":
                tech_stack.deployment_tools.add("github-actions")

    # Parse Python requirements.txt file
    def _parse_requirements_txt(self, file_path: Path, tech_stack: TechStackInfo):
        """Parse Python requirements.txt file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse package==version or package>=version format
                        match = re.match(r"([a-zA-Z0-9_-]+)([>=<!=]+)([0-9.]+)", line)
                        if match:
                            package, op, version = match.groups()
                            tech_stack.dependencies[package.lower()] = version
                        else:
                            # Simple package name
                            package = line.split()[0]
                            tech_stack.dependencies[package.lower()] = "unknown"
        except Exception as e:
            logger.warning(f"Error parsing requirements.txt: {e}")

    # Parse Node.js package.json file
    def _parse_package_json(self, file_path: Path, tech_stack: TechStackInfo):
        """Parse Node.js package.json file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Dependencies
                for dep, version in data.get("dependencies", {}).items():
                    tech_stack.dependencies[dep] = version

                # Dev dependencies
                for dep, version in data.get("devDependencies", {}).items():
                    tech_stack.dev_dependencies[dep] = version

                # Scripts might indicate build tools
                scripts = data.get("scripts", {})
                if "webpack" in str(scripts):
                    tech_stack.build_tools.add("webpack")
                if "rollup" in str(scripts):
                    tech_stack.build_tools.add("rollup")
                if "vite" in str(scripts):
                    tech_stack.build_tools.add("vite")

        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")

    # Parse Python pyproject.toml file
    def _parse_pyproject_toml(self, file_path: Path, tech_stack: TechStackInfo):
        """Parse Python pyproject.toml file"""
        try:
            import tomllib

            with open(file_path, "rb") as f:
                data = tomllib.load(f)

                # Dependencies from various sections
                deps = data.get("project", {}).get("dependencies", [])
                for dep in deps:
                    # Parse dependency specification
                    match = re.match(r"([a-zA-Z0-9_-]+)", dep)
                    if match:
                        package = match.group(1)
                        tech_stack.dependencies[package.lower()] = "pyproject"

        except ImportError:
            logger.warning("tomllib not available for parsing pyproject.toml")
        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {e}")

    # Parse Java Maven pom.xml file (basic implementation)
    def _parse_pom_xml(self, file_path: Path, tech_stack: TechStackInfo):
        """Parse Java Maven pom.xml file (basic implementation)"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Extract dependencies using regex (basic approach)
                deps = re.findall(r"<artifactId>([^<]+)</artifactId>", content)
                for dep in deps:
                    tech_stack.dependencies[dep.lower()] = "maven"

                tech_stack.build_tools.add("maven")

        except Exception as e:
            logger.warning(f"Error parsing pom.xml: {e}")

    # Parse Gradle build.gradle file (basic implementation)
    def _parse_build_gradle(self, file_path: Path, tech_stack: TechStackInfo):
        """Parse Gradle build.gradle file (basic implementation)"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Extract dependencies using regex (basic approach)
                deps = re.findall(r'implementation ["\']([^:"]+)', content)
                for dep in deps:
                    tech_stack.dependencies[dep.lower()] = "gradle"

                tech_stack.build_tools.add("gradle")

        except Exception as e:
            logger.warning(f"Error parsing build.gradle: {e}")


# Main codebase analyzer orchestrating the analysis pipeline
class CodebaseAnalyzer:
    """Main codebase analyzer orchestrating the analysis pipeline"""

    def __init__(
        self, root_path: Union[str, Path], config: Optional[Dict[str, Any]] = None
    ):
        """Initialize codebase analyzer"""
        self.root_path = Path(root_path).resolve()
        self.config = config or {}

        # Set default configuration
        self.config.setdefault("max_total_size", 200_000)
        self.config.setdefault("max_file_size", 50_000)
        self.config.setdefault("skip_directories", [])
        self.config.setdefault("skip_patterns", [])
        self.config.setdefault("include_hidden", [])

        # Initialize pipeline stages
        self.file_discoverer = FileDiscoverer(self.root_path, self.config)
        self.content_aggregator = ContentAggregator(self.config)
        self.structure_analyzer = ProjectStructureAnalyzer(self.root_path, self.config)
        self.tech_stack_detector = TechStackDetector(self.root_path, self.config)

    # Perform comprehensive codebase analysis
    def analyze_codebase(
        self,
        max_total_size: int = 200_000,
        analysis_scope: AnalysisScope = AnalysisScope.ALL,
    ) -> CodebaseAnalysisResult:
        """
        Perform comprehensive codebase analysis

        Args:
            max_total_size: Maximum total size of aggregated content
            analysis_scope: Scope of analysis to perform

        Returns:
            CodebaseAnalysisResult with complete analysis
        """
        start_time = time.time()
        result = CodebaseAnalysisResult()

        try:
            # Update configuration
            self.config["max_total_size"] = max_total_size

            # Stage 1: File Discovery
            logger.info(f"Starting codebase analysis for: {self.root_path}")
            discovery_start = time.time()
            files = self.file_discoverer.discover_files()
            result.stats.discovery_time = time.time() - discovery_start
            result.stats.files_analyzed = len(files)

            if not files:
                result.error = "No analyzable files found"
                return result

            # Stage 2: Content Aggregation
            analysis_start = time.time()
            aggregated_content = self.content_aggregator.aggregate_contents(files)
            result.stats.payload_size = aggregated_content["total_size"]
            result.stats.truncated_files = len(aggregated_content["truncated_files"])
            result.stats.files_skipped = aggregated_content["stats"]["files_skipped"]

            # Stage 3: Project Structure Analysis
            if analysis_scope in [AnalysisScope.STRUCTURE, AnalysisScope.ALL]:
                result.structure = self.structure_analyzer.build_project_report(
                    files, aggregated_content
                )

            # Stage 4: Tech Stack Detection
            if analysis_scope in [AnalysisScope.PATTERNS, AnalysisScope.ALL]:
                result.tech_stack = self.tech_stack_detector.analyze_tech_stack(
                    files, aggregated_content
                )

            # Stage 5: Individual File Analysis (if code analyzer available)
            if CODE_ANALYZER_AVAILABLE and analysis_scope == AnalysisScope.ALL:
                result.file_analyses = self._analyze_individual_files(
                    aggregated_content, analysis_scope
                )

                # Stage 6: Enhance tech stack with polyglot analysis insights
                if result.file_analyses:
                    self._enhance_tech_stack_with_analysis(result.tech_stack, result.file_analyses)

            result.stats.analysis_time = time.time() - analysis_start

            # Build project report
            result.project_report = self._build_project_report(result)

            # Build prompt payload
            result.prompt_payload = self._build_prompt_payload(
                result, aggregated_content
            )

            result.stats.total_time = time.time() - start_time

            logger.info(
                f"Codebase analysis completed in {result.stats.total_time:.2f}s"
            )
            return result

        except Exception as e:
            result.error = str(e)
            result.stats.total_time = time.time() - start_time
            logger.error(f"Codebase analysis failed: {e}")
            return result

    def _analyze_individual_files(
        self, aggregated_content: Dict[str, Any], analysis_scope: AnalysisScope
    ) -> List[AnalysisResult]:
        """Analyze individual files using the polyglot analyzer"""
        file_analyses = []

        # Convert analysis scope to individual analysis type
        if analysis_scope == AnalysisScope.SECURITY:
            analysis_type = AnalysisType.SECURITY
        elif analysis_scope == AnalysisScope.PERFORMANCE:
            analysis_type = AnalysisType.PERFORMANCE
        else:
            analysis_type = AnalysisType.COMPREHENSIVE

        # Get supported languages from polyglot system
        if CODE_ANALYZER_AVAILABLE:
            try:
                supported_languages = set(get_supported_languages())
            except Exception:
                # Fallback to known languages if function fails
                supported_languages = {"python", "typescript", "javascript"}
        else:
            supported_languages = {"python", "typescript", "javascript"}

        # Analyze a subset of important files to avoid overwhelming the results
        # Prioritize non-test files in supported languages
        files_to_analyze = []

        for file_path, file_data in aggregated_content.get("files", {}).items():
            if (file_data["language"] in supported_languages and
                not file_data.get("is_test", False) and
                not file_data.get("is_config", False)):
                files_to_analyze.append((file_path, file_data))

        # Limit to top 15 files to avoid overwhelming results
        files_to_analyze = files_to_analyze[:15]

        for file_path, file_data in files_to_analyze:
            try:
                # Use polyglot analyzer with automatic language detection
                result = analyze_code(
                    code=file_data["content"],
                    analysis_type=analysis_type,
                    file_path=file_path
                )

                # Add additional metadata from file discovery
                if hasattr(result, 'language_specific'):
                    if result.language_specific is None:
                        result.language_specific = {}
                    result.language_specific.update({
                        'file_size': file_data.get('size', 0),
                        'line_count': file_data.get('lines', 0),
                        'detected_from_codebase': True
                    })

                file_analyses.append(result)
                logger.debug(f"Successfully analyzed {file_path} ({result.language})")

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        logger.info(f"Analyzed {len(file_analyses)} individual files using polyglot system")
        return file_analyses

    def _enhance_tech_stack_with_analysis(
        self, tech_stack: TechStackInfo, file_analyses: List[AnalysisResult]
    ) -> None:
        """Enhance tech stack information using polyglot analysis insights"""
        try:
            # Track language usage from actual analysis results
            languages_analyzed = set()
            framework_indicators = set()

            for analysis in file_analyses:
                if not analysis.error:
                    # Track confirmed languages
                    languages_analyzed.add(analysis.language)

                    # Extract framework information from language-specific metadata
                    if hasattr(analysis, 'language_specific') and analysis.language_specific:
                        lang_specific = analysis.language_specific

                        # JavaScript/TypeScript framework detection
                        if analysis.language in ['javascript', 'typescript']:
                            frameworks_detected = lang_specific.get('frameworks_detected', [])
                            for framework in frameworks_detected:
                                tech_stack.frameworks[framework.lower()] = 'detected_via_analysis'
                                framework_indicators.add(framework.lower())

                        # Python framework detection from imports and patterns
                        elif analysis.language == 'python':
                            # Look for framework-specific issues or patterns in analysis results
                            for issue in analysis.issues:
                                if 'django' in issue.message.lower():
                                    tech_stack.frameworks['django'] = 'detected_via_analysis'
                                elif 'flask' in issue.message.lower():
                                    tech_stack.frameworks['flask'] = 'detected_via_analysis'
                                elif 'fastapi' in issue.message.lower():
                                    tech_stack.frameworks['fastapi'] = 'detected_via_analysis'

                    # Analyze issues for additional tech insights
                    for issue in analysis.issues:
                        issue_msg = issue.message.lower()

                        # Database-related issues
                        if any(db in issue_msg for db in ['sql', 'database', 'query']):
                            if 'postgresql' in issue_msg or 'psycopg' in issue_msg:
                                tech_stack.databases.add('postgresql')
                            elif 'mysql' in issue_msg:
                                tech_stack.databases.add('mysql')
                            elif 'sqlite' in issue_msg:
                                tech_stack.databases.add('sqlite')

                        # Security-related patterns might indicate specific technologies
                        if issue.type == 'security':
                            if 'cors' in issue_msg:
                                framework_indicators.add('web_framework')
                            elif 'jwt' in issue_msg or 'token' in issue_msg:
                                framework_indicators.add('authentication')

            # Update language information with confirmed analysis results
            for lang in languages_analyzed:
                if lang not in tech_stack.languages:
                    tech_stack.languages[lang] = 'confirmed_via_analysis'

            # Add testing frameworks based on analysis patterns
            testing_indicators = []
            for analysis in file_analyses:
                if not analysis.error:
                    for issue in analysis.issues:
                        if 'test' in issue.message.lower():
                            if analysis.language == 'python':
                                testing_indicators.extend(['pytest', 'unittest'])
                            elif analysis.language == 'javascript':
                                testing_indicators.extend(['jest', 'mocha'])
                            elif analysis.language == 'typescript':
                                testing_indicators.extend(['jest', 'vitest'])

            for test_framework in set(testing_indicators):
                tech_stack.testing_frameworks.add(test_framework)

            logger.debug(f"Enhanced tech stack with insights from {len(file_analyses)} analyzed files")
            logger.debug(f"Confirmed languages: {', '.join(languages_analyzed)}")
            logger.debug(f"Detected frameworks: {', '.join(framework_indicators)}")

        except Exception as e:
            logger.warning(f"Failed to enhance tech stack with analysis insights: {e}")

    def _build_project_report(self, result: CodebaseAnalysisResult) -> Dict[str, Any]:
        """Build comprehensive project report"""
        report = {
            "summary": {
                "total_files": result.structure.total_files,
                "total_lines": result.structure.total_lines,
                "total_size": result.structure.total_size,
                "primary_language": (
                    max(result.structure.languages.items(), key=lambda x: x[1])[0]
                    if result.structure.languages
                    else "unknown"
                ),
                "analysis_time": f"{result.stats.total_time:.2f}s",
            },
            "structure": {
                "languages": result.structure.languages,
                "directories": len(result.structure.directories),
                "file_extensions": result.structure.file_extensions,
                "package_info": result.structure.package_structure,
            },
            "tech_stack": {
                "frameworks": dict(result.tech_stack.frameworks),
                "databases": list(result.tech_stack.databases),
                "build_tools": list(result.tech_stack.build_tools),
                "deployment_tools": list(result.tech_stack.deployment_tools),
                "testing_frameworks": list(result.tech_stack.testing_frameworks),
                "dependency_count": len(result.tech_stack.dependencies),
            },
            "quality_insights": self._generate_quality_insights(result),
            "recommendations": self._generate_recommendations(result),
        }

        # Add polyglot analysis insights if available
        if result.file_analyses:
            polyglot_insights = self._generate_polyglot_insights(result.file_analyses)
            report["polyglot_analysis"] = polyglot_insights

        return report

    def _generate_polyglot_insights(self, file_analyses: List[AnalysisResult]) -> Dict[str, Any]:
        """Generate insights from polyglot code analysis results"""
        insights = {
            "languages_analyzed": {},
            "overall_scores": {
                "security": 0.0,
                "quality": 0.0,
                "performance": 0.0
            },
            "issues_by_language": {},
            "issues_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "issues_by_type": {},
            "top_issues": [],
            "analysis_summary": {
                "total_files_analyzed": len(file_analyses),
                "files_with_errors": 0,
                "total_issues_found": 0
            }
        }

        try:
            valid_analyses = [a for a in file_analyses if not a.error]
            insights["analysis_summary"]["files_with_errors"] = len(file_analyses) - len(valid_analyses)

            if not valid_analyses:
                return insights

            # Aggregate scores by language
            language_scores = {}
            language_counts = {}

            for analysis in valid_analyses:
                lang = analysis.language

                # Initialize language tracking
                if lang not in language_scores:
                    language_scores[lang] = {"security": 0, "quality": 0, "performance": 0}
                    language_counts[lang] = 0
                    insights["issues_by_language"][lang] = []

                language_counts[lang] += 1

                # Aggregate scores
                language_scores[lang]["security"] += analysis.security_score
                language_scores[lang]["quality"] += analysis.quality_score
                language_scores[lang]["performance"] += analysis.performance_score

                # Collect issues
                for issue in analysis.issues:
                    insights["issues_by_language"][lang].append({
                        "message": issue.message,
                        "severity": issue.severity.value,
                        "line": issue.line,
                        "type": issue.type,
                        "file": analysis.file_path
                    })

                    # Count by severity
                    severity = issue.severity.value
                    if severity in insights["issues_by_severity"]:
                        insights["issues_by_severity"][severity] += 1

                    # Count by type
                    issue_type = issue.type
                    if issue_type not in insights["issues_by_type"]:
                        insights["issues_by_type"][issue_type] = 0
                    insights["issues_by_type"][issue_type] += 1

            # Calculate average scores by language
            for lang in language_scores:
                count = language_counts[lang]
                insights["languages_analyzed"][lang] = {
                    "files_analyzed": count,
                    "average_security_score": round(language_scores[lang]["security"] / count, 1),
                    "average_quality_score": round(language_scores[lang]["quality"] / count, 1),
                    "average_performance_score": round(language_scores[lang]["performance"] / count, 1),
                    "total_issues": len(insights["issues_by_language"][lang])
                }

            # Calculate overall scores
            total_files = len(valid_analyses)
            insights["overall_scores"]["security"] = round(
                sum(a.security_score for a in valid_analyses) / total_files, 1
            )
            insights["overall_scores"]["quality"] = round(
                sum(a.quality_score for a in valid_analyses) / total_files, 1
            )
            insights["overall_scores"]["performance"] = round(
                sum(a.performance_score for a in valid_analyses) / total_files, 1
            )

            # Get top issues (highest severity, most common)
            all_issues = []
            for analysis in valid_analyses:
                for issue in analysis.issues:
                    all_issues.append({
                        "message": issue.message,
                        "severity": issue.severity.value,
                        "type": issue.type,
                        "file": analysis.file_path,
                        "language": analysis.language,
                        "line": issue.line
                    })

            # Sort by severity priority and take top 10
            severity_priority = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            insights["top_issues"] = sorted(
                all_issues,
                key=lambda x: severity_priority.get(x["severity"], 0),
                reverse=True
            )[:10]

            insights["analysis_summary"]["total_issues_found"] = len(all_issues)

            return insights

        except Exception as e:
            logger.warning(f"Failed to generate polyglot insights: {e}")
            return insights

    def _build_prompt_payload(
        self, result: CodebaseAnalysisResult, aggregated_content: Dict[str, Any]
    ) -> str:
        """Build payload for AI prompt injection"""
        payload_parts = []

        # Project overview
        payload_parts.append(f"# Codebase Analysis: {self.root_path.name}")
        payload_parts.append("## Project Overview")
        payload_parts.append(f"- Total Files: {result.structure.total_files}")
        payload_parts.append(f"- Total Lines: {result.structure.total_lines:,}")
        payload_parts.append(
            f"- Primary Language: {max(result.structure.languages.items(), key=lambda x: x[1])[0] if result.structure.languages else 'unknown'}"
        )
        payload_parts.append("")

        # Tech stack
        if result.tech_stack.frameworks:
            payload_parts.append("## Technology Stack")
            payload_parts.append(
                f"- Frameworks: {', '.join(result.tech_stack.frameworks.keys())}"
            )
            if result.tech_stack.databases:
                payload_parts.append(
                    f"- Databases: {', '.join(result.tech_stack.databases)}"
                )
            if result.tech_stack.build_tools:
                payload_parts.append(
                    f"- Build Tools: {', '.join(result.tech_stack.build_tools)}"
                )
            payload_parts.append("")

        # File contents
        payload_parts.append("## File Contents")
        for file_path, file_data in aggregated_content.get("files", {}).items():
            payload_parts.append(f"### {file_path}")
            payload_parts.append(f"```{file_data['language']}")
            payload_parts.append(file_data["content"])
            payload_parts.append("```")
            payload_parts.append("")

        return "\n".join(payload_parts)

    def _generate_quality_insights(self, result: CodebaseAnalysisResult) -> List[str]:
        """Generate quality insights from analysis"""
        insights = []

        # Language diversity
        if len(result.structure.languages) > 5:
            insights.append("High language diversity - consider consolidation")

        # Missing __init__.py files
        if result.structure.missing_inits:
            insights.append(
                f"{len(result.structure.missing_inits)} directories missing __init__.py files"
            )

        # Circular imports
        if result.structure.circular_imports:
            insights.append(
                f"{len(result.structure.circular_imports)} potential circular imports detected"
            )

        # Large codebase indicators
        if result.structure.total_lines > 100000:
            insights.append("Large codebase - consider modularization strategies")

        return insights

    def _generate_recommendations(self, result: CodebaseAnalysisResult) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Documentation
        doc_files = sum(
            1 for f in [result.stats.files_analyzed] if "readme" in str(f).lower()
        )
        if doc_files == 0:
            recommendations.append("Add README.md and documentation files")

        # Testing
        if (
            result.tech_stack.frameworks
            and "pytest" not in result.tech_stack.dependencies
        ):
            recommendations.append("Consider adding automated testing with pytest")

        # CI/CD
        if not result.tech_stack.deployment_tools:
            recommendations.append("Consider adding CI/CD pipeline configuration")

        # Code quality recommendations based on polyglot analysis
        if result.file_analyses:
            self._add_polyglot_recommendations(recommendations, result)

        # Language-specific recommendations
        if "python" in result.structure.languages:
            quality_tools = ["black", "flake8", "mypy", "pre-commit"]
            missing_tools = [
                tool
                for tool in quality_tools
                if tool not in result.tech_stack.dependencies
            ]
            if missing_tools:
                recommendations.append(
                    f"Consider adding Python code quality tools: {', '.join(missing_tools)}"
                )

        if "javascript" in result.structure.languages or "typescript" in result.structure.languages:
            js_tools = ["eslint", "prettier"]
            missing_js_tools = [
                tool for tool in js_tools
                if tool not in result.tech_stack.dependencies and tool not in result.tech_stack.dev_dependencies
            ]
            if missing_js_tools:
                recommendations.append(
                    f"Consider adding JavaScript/TypeScript quality tools: {', '.join(missing_js_tools)}"
                )

        return recommendations

    def _add_polyglot_recommendations(self, recommendations: List[str], result: CodebaseAnalysisResult) -> None:
        """Add recommendations based on polyglot analysis results"""
        try:
            # Analyze overall quality scores
            valid_analyses = [a for a in result.file_analyses if not a.error]
            if not valid_analyses:
                return

            avg_security = sum(a.security_score for a in valid_analyses) / len(valid_analyses)
            avg_quality = sum(a.quality_score for a in valid_analyses) / len(valid_analyses)
            avg_performance = sum(a.performance_score for a in valid_analyses) / len(valid_analyses)

            # Security recommendations
            if avg_security < 70:
                recommendations.append("⚠️ Low security score detected - review security vulnerabilities")

                # Check for specific security patterns
                security_issues = []
                for analysis in valid_analyses:
                    for issue in analysis.issues:
                        if issue.type == "security" and issue.severity.value in ["high", "critical"]:
                            if "eval" in issue.message.lower():
                                security_issues.append("eval() usage")
                            elif "sql" in issue.message.lower():
                                security_issues.append("SQL injection risks")
                            elif "command" in issue.message.lower():
                                security_issues.append("command injection risks")

                if security_issues:
                    recommendations.append(f"Address critical security issues: {', '.join(set(security_issues))}")

            # Quality recommendations
            if avg_quality < 75:
                recommendations.append("📝 Code quality could be improved - review naming conventions and documentation")

                # Count missing docstrings across languages
                missing_docs = sum(1 for a in valid_analyses for issue in a.issues
                                 if "docstring" in issue.message.lower())
                if missing_docs > 5:
                    recommendations.append(f"Add documentation - {missing_docs} missing docstrings found")

            # Performance recommendations
            if avg_performance < 80:
                recommendations.append("🚀 Performance optimizations recommended")

                # Check for specific performance patterns
                perf_issues = []
                for analysis in valid_analyses:
                    for issue in analysis.issues:
                        if issue.type == "performance":
                            if "loop" in issue.message.lower():
                                perf_issues.append("inefficient loops")
                            elif "string" in issue.message.lower() and "concat" in issue.message.lower():
                                perf_issues.append("string concatenation")
                            elif "nested" in issue.message.lower():
                                perf_issues.append("nested operations")

                if perf_issues:
                    recommendations.append(f"Optimize performance issues: {', '.join(set(perf_issues))}")

            # Language-specific recommendations based on analysis
            languages_with_issues = {}
            for analysis in valid_analyses:
                lang = analysis.language
                if lang not in languages_with_issues:
                    languages_with_issues[lang] = []

                for issue in analysis.issues:
                    if issue.severity.value in ["high", "critical"]:
                        languages_with_issues[lang].append(issue.type)

            for lang, issue_types in languages_with_issues.items():
                if len(set(issue_types)) > 3:  # Multiple types of issues
                    recommendations.append(f"Review {lang} code quality - multiple issue types detected")

        except Exception as e:
            logger.warning(f"Failed to generate polyglot recommendations: {e}")


def discover_files(
    root_path: Union[str, Path], config: Optional[Dict[str, Any]] = None, **kwargs
) -> List[FileInfo]:
    """
    Discover files in a project directory

    Args:
        root_path: Root directory to scan
        config: Optional configuration for filtering
        kwargs: Additional configuration options to override defaults

    Returns:
        List of discovered FileInfo objects
    """
    # Update configuration with kwargs overrides
    config = config or {}
    config.update(kwargs)
    discoverer = FileDiscoverer(Path(root_path), config)
    return discoverer.discover_files()


def aggregate_contents(
    files: List[FileInfo], max_total_size: int = 200_000, **kwargs
) -> Dict[str, Any]:
    """
    Aggregate file contents with truncation

    Args:
        files: List of FileInfo objects to aggregate
        max_total_size: Maximum total size of content
        kwargs: Additional configuration options to override defaults

    Returns:
        Aggregated content dictionary
    """
    # Update configuration with kwargs overrides
    config = {"max_total_size": max_total_size}
    config.update(kwargs)
    aggregator = ContentAggregator(config)
    return aggregator.aggregate_contents(files)


def build_project_report(
    root_path: Union[str, Path],
    files: List[FileInfo],
    aggregated_content: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    """
    Build project structure report

    Args:
        root_path: Root directory path
        files: List of FileInfo objects
        aggregated_content: Aggregated file contents
        kwargs: Additional configuration options to override defaults

    Returns:
        Project report dictionary
    """
    # Update configuration with kwargs overrides
    config = {}
    config.update(kwargs)
    analyzer = ProjectStructureAnalyzer(Path(root_path), config)
    structure = analyzer.build_project_report(files, aggregated_content)

    detector = TechStackDetector(Path(root_path), config)
    tech_stack = detector.analyze_tech_stack(files, aggregated_content)

    return {"structure": structure, "tech_stack": tech_stack}


def analyze_codebase(
    root_path: Union[str, Path],
    max_total_size: int = 200_000,
    config: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> CodebaseAnalysisResult:
    """
    Perform comprehensive codebase analysis

    Args:
        root_path: Root directory to analyze
        max_total_size: Maximum total size of aggregated content
        config: Optional analysis configuration
        kwargs: Additional configuration options to override defaults

    Returns:
        Complete codebase analysis results

    Example:
        >>> result = analyze_codebase("/path/to/project")
        >>> print(result.project_report['summary'])
        >>> print(f"Payload size: {len(result.prompt_payload)} characters")
    """
    # Update configuration with kwargs overrides
    config = config or {}
    config.update(kwargs)
    analyzer = CodebaseAnalyzer(root_path, config)
    return analyzer.analyze_codebase(max_total_size, AnalysisScope.ALL)


# Export public API
__all__ = [
    "CodebaseAnalyzer",
    "discover_files",
    "aggregate_contents",
    "build_project_report",
    "analyze_codebase",
    "AnalysisScope",
    "CodebaseAnalysisResult",
    "ProjectStructure",
    "TechStackInfo",
    "ArchitectureInfo",
    "CodebaseStats",
    "FileInfo",
    "CodebaseAnalysisError",
    "FileDiscoveryError",
    "ContentAggregationError",
    "ProjectStructureError",
]
