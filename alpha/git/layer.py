"""Git Repository Layer: CLI interface for commits, diffs, branches, cloning, and PR analysis."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GitCommit(BaseModel):
    hash: str
    author: str
    date: str
    message: str

class GitRepositoryLayer:
    """Provides high-level programmatic interfaces for Git repository inspection and operations."""

    def __init__(self, git_binary: Optional[str] = None):
        self.git_bin = git_binary or shutil.which("git") or "git"

    def _run_git(self, args: List[str], repo_dir: Path, timeout: float = 15.0) -> subprocess.CompletedProcess:
        cmd = [self.git_bin] + args
        return subprocess.run(
            cmd,
            cwd=str(repo_dir),
            text=True,
            capture_output=True,
            timeout=timeout,
            env={"LANG": "C", "PATH": os.environ.get("PATH", "")}
        )

    def get_status(self, repo_dir: str) -> Dict[str, Any]:
        p = Path(repo_dir).resolve()
        proc = self._run_git(["status", "--porcelain", "-b"], p)
        if proc.returncode != 0:
            if "not a git repository" in proc.stderr.lower():
                return {
                    "branch": "no_git",
                    "is_clean": True,
                    "modified_files": [],
                    "untracked_files": [],
                    "staged_files": [],
                    "is_git_repo": False
                }
            raise RuntimeError(f"Git status failed: {proc.stderr}")

        lines = proc.stdout.splitlines()
        branch_line = lines[0] if lines else ""
        branch = branch_line.replace("## ", "").split("...")[0].strip() if branch_line.startswith("## ") else "unknown"

        modified = []
        untracked = []
        staged = []

        for line in lines[1:]:
            if line.startswith("?? "):
                untracked.append(line[3:])
            elif line.startswith(" M ") or line.startswith("M  "):
                modified.append(line[3:])
            elif line.startswith("A  "):
                staged.append(line[3:])

        return {
            "branch": branch,
            "is_clean": len(lines) <= 1,
            "modified_files": modified,
            "untracked_files": untracked,
            "staged_files": staged,
            "is_git_repo": True
        }

    def inspect_commits(self, repo_dir: str, limit: int = 5) -> List[GitCommit]:
        p = Path(repo_dir).resolve()
        fmt = "%H|%an|%ad|%s"
        proc = self._run_git(["log", f"-n{limit}", f"--format={fmt}", "--date=short"], p)
        if proc.returncode != 0:
            if "not a git repository" in proc.stderr.lower() or "does not have any commits" in proc.stderr.lower():
                return []
            raise RuntimeError(f"Git log failed: {proc.stderr}")

        commits = []
        for line in proc.stdout.splitlines():
            parts = line.strip().split("|", 3)
            if len(parts) == 4:
                commits.append(GitCommit(
                    hash=parts[0][:8],
                    author=parts[1],
                    date=parts[2],
                    message=parts[3]
                ))
        return commits

    def analyze_branches(self, repo_dir: str) -> Dict[str, Any]:
        p = Path(repo_dir).resolve()
        proc = self._run_git(["branch", "-a"], p)
        if proc.returncode != 0:
            if "not a git repository" in proc.stderr.lower():
                return {
                    "current_branch": "none",
                    "total_branches": 0,
                    "branches": [],
                    "is_git_repo": False
                }
            raise RuntimeError(f"Git branch failed: {proc.stderr}")

        branches = []
        current = ""
        for line in proc.stdout.splitlines():
            line_str = line.strip()
            if line_str.startswith("* "):
                current = line_str[2:]
                branches.append(current)
            elif line_str:
                branches.append(line_str)

        return {
            "current_branch": current,
            "total_branches": len(branches),
            "branches": branches
        }

    def generate_diff(self, repo_dir: str, cached: bool = False, commit: Optional[str] = None) -> str:
        p = Path(repo_dir).resolve()
        args = ["diff"]
        if cached:
            args.append("--cached")
        if commit:
            args.append(commit)
        proc = self._run_git(args, p)
        if proc.returncode != 0:
            raise RuntimeError(f"Git diff failed: {proc.stderr}")
        return proc.stdout

    def clone_repository(self, repo_url: str, target_dir: str, depth: int = 1) -> str:
        t = Path(target_dir).resolve()
        t.parent.mkdir(parents=True, exist_ok=True)
        cmd = [self.git_bin, "clone", f"--depth={depth}", repo_url, str(t)]
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=60.0)
        if proc.returncode != 0:
            raise RuntimeError(f"Git clone failed: {proc.stderr}")
        return str(t)

    def review_diff(self, diff_text: str) -> Dict[str, Any]:
        """Analyze a diff hunk and produce structured PR review observations."""
        additions = 0
        deletions = 0
        files_changed = set()
        flags = []

        lines = diff_text.splitlines()
        for line in lines:
            if line.startswith("+++ b/"):
                files_changed.add(line[6:])
            elif line.startswith("+") and not line.startswith("+++"):
                additions += 1
                if "TODO" in line or "FIXME" in line:
                    flags.append("Contains unresolved TODO/FIXME markers")
                if "console.log" in line or "print(" in line:
                    flags.append("Contains potential debug logging calls")
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        has_tests = any("test" in f.lower() for f in files_changed)
        if files_changed and not has_tests:
            flags.append("Changes do not include updates to test files")

        return {
            "files_changed_count": len(files_changed),
            "files_changed": sorted(list(files_changed)),
            "additions": additions,
            "deletions": deletions,
            "net_lines": additions - deletions,
            "review_flags": list(set(flags)),
            "summary": f"Diff changes {len(files_changed)} files (+{additions}, -{deletions})."
        }

    def summarize_codebase(self, repo_dir: str) -> Dict[str, Any]:
        status = self.get_status(repo_dir)
        commits = self.inspect_commits(repo_dir, limit=10)
        branches = self.analyze_branches(repo_dir)
        return {
            "repository": repo_dir,
            "status": status,
            "recent_commits": [c.model_dump() for c in commits],
            "branches": branches
        }
