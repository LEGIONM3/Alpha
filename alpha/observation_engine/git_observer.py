"""Git Observer for Project Alpha.

Gathers live empirical observations from Git:
- git diff analysis (unstaged and staged changes, diff stat, modified lines)
- commit inspection (recent commit hashes, authors, timestamps, commit messages)
- changed file analysis (modified, staged, untracked, deleted files)
- branch state analysis (current branch, upstream tracking, ahead/behind)
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from alpha.observation_engine.observation import Observation


class GitObserver:
    """Collects empirical observations from the repository's live Git state."""

    def __init__(self, workspace_root: Optional[Path] = None, git_bin: Optional[str] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.git_bin = git_bin or shutil.which("git") or "git"

    def _run_git(self, args: List[str], timeout: float = 10.0) -> subprocess.CompletedProcess:
        cmd = [self.git_bin] + args
        return subprocess.run(
            cmd,
            cwd=str(self.workspace_root),
            text=True,
            capture_output=True,
            timeout=timeout,
            env={"LANG": "C", "PATH": os.environ.get("PATH", "")}
        )

    def is_git_available(self) -> bool:
        try:
            res = self._run_git(["rev-parse", "--is-inside-work-tree"])
            return res.returncode == 0
        except Exception:
            return False

    def observe_diff(self) -> List[Observation]:
        """Analyzes git diff for staged and unstaged modifications."""
        observations: List[Observation] = []
        if not self.is_git_available():
            return observations

        try:
            # Check diff stat
            res_stat = self._run_git(["diff", "--stat"])
            stat_text = res_stat.stdout.strip()

            # Check unstaged diff snippet
            res_diff = self._run_git(["diff", "-U1"])
            diff_lines = res_diff.stdout.splitlines()

            # Check cached/staged diff
            res_cached = self._run_git(["diff", "--cached", "--stat"])
            cached_text = res_cached.stdout.strip()

            if stat_text or cached_text:
                summary_parts = []
                if stat_text:
                    summary_parts.append(f"Unstaged Diffs:\n{stat_text[:300]}")
                if cached_text:
                    summary_parts.append(f"Staged Diffs:\n{cached_text[:300]}")
                if diff_lines:
                    sample_diff = "\n".join(diff_lines[:8])
                    summary_parts.append(f"Diff Sample:\n{sample_diff}")

                obs = Observation(
                    source="Git:diff",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=" | ".join(summary_parts),
                    confidence=0.99,
                    category="git_diff"
                )
                observations.append(obs)
            else:
                obs = Observation(
                    source="Git:diff",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence="Git working tree is clean: 0 unstaged and 0 staged modifications.",
                    confidence=0.99,
                    category="git_diff"
                )
                observations.append(obs)

        except Exception as e:
            observations.append(
                Observation(
                    source="Git:diff",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=f"Git diff query anomaly: {e}",
                    confidence=0.80,
                    category="git_diff"
                )
            )

        return observations

    def observe_commits(self, limit: int = 5) -> List[Observation]:
        """Inspects the most recent commit history."""
        observations: List[Observation] = []
        if not self.is_git_available():
            return observations

        try:
            res = self._run_git(["log", f"-n{limit}", "--pretty=format:%h|%an|%ad|%s", "--date=iso"])
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]

            if lines:
                commit_summaries = []
                for line in lines:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        chash, author, date, msg = parts
                        commit_summaries.append(f"[{chash}] {msg} (by {author} on {date[:19]})")
                    else:
                        commit_summaries.append(line)

                evidence = f"Recent Commits ({len(lines)}): " + " ; ".join(commit_summaries)
                obs = Observation(
                    source="Git:commits",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence,
                    confidence=0.99,
                    category="git_commits"
                )
                observations.append(obs)
            else:
                obs = Observation(
                    source="Git:commits",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence="Git repository has no commit history yet.",
                    confidence=0.95,
                    category="git_commits"
                )
                observations.append(obs)

        except Exception as e:
            observations.append(
                Observation(
                    source="Git:commits",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=f"Git commit inspection anomaly: {e}",
                    confidence=0.80,
                    category="git_commits"
                )
            )

        return observations

    def observe_changed_files(self) -> List[Observation]:
        """Analyzes modified, untracked, and deleted files via git status."""
        observations: List[Observation] = []
        if not self.is_git_available():
            return observations

        try:
            res = self._run_git(["status", "--porcelain"])
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]

            modified = [l[3:] for l in lines if l.startswith("M") or l.startswith(" M")]
            untracked = [l[3:] for l in lines if l.startswith("??")]
            deleted = [l[3:] for l in lines if l.startswith("D") or l.startswith(" D")]

            evidence = (
                f"Git Working Tree Status: Total Changed Files: {len(lines)} | "
                f"Modified ({len(modified)}): {', '.join(modified[:4]) or 'None'} | "
                f"Untracked ({len(untracked)}): {', '.join(untracked[:4]) or 'None'} | "
                f"Deleted ({len(deleted)}): {', '.join(deleted[:4]) or 'None'}"
            )

            obs = Observation(
                source="Git:changed_files",
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence=evidence,
                confidence=0.98,
                category="git_changed_files"
            )
            observations.append(obs)

        except Exception as e:
            observations.append(
                Observation(
                    source="Git:changed_files",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=f"Git status changed files anomaly: {e}",
                    confidence=0.80,
                    category="git_changed_files"
                )
            )

        return observations

    def observe_branch_state(self) -> List[Observation]:
        """Analyzes active branch name and tracking information."""
        observations: List[Observation] = []
        if not self.is_git_available():
            return observations

        try:
            res = self._run_git(["status", "-b", "--porcelain"])
            first_line = res.stdout.splitlines()[0] if res.stdout.splitlines() else "## unknown"
            branch_info = first_line.replace("## ", "").strip()

            evidence = f"Git Active Branch: {branch_info}"
            obs = Observation(
                source="Git:branch_state",
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence=evidence,
                confidence=0.99,
                category="git_branch_state"
            )
            observations.append(obs)

        except Exception as e:
            observations.append(
                Observation(
                    source="Git:branch_state",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=f"Git branch inspection anomaly: {e}",
                    confidence=0.80,
                    category="git_branch_state"
                )
            )

        return observations

    def observe_all(self) -> List[Observation]:
        """Collects observations across all Git vectors."""
        results: List[Observation] = []
        results.extend(self.observe_branch_state())
        results.extend(self.observe_changed_files())
        results.extend(self.observe_commits(limit=5))
        results.extend(self.observe_diff())
        return results
