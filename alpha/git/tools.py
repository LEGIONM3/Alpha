"""Git Intelligence Tools for Alpha OS ToolRegistry."""

from typing import Any, Dict, List, Optional
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolPermission,
    ToolParameter,
    ValidationRule
)
from alpha.git.layer import GitRepositoryLayer

class GitStatusTool(BaseTool):
    def __init__(self, workspace_root: str, layer: Optional[GitRepositoryLayer] = None):
        super().__init__(
            name="git_status",
            description="Inspects git status: active branch, modified, untracked, and staged files.",
            capabilities=[ToolCapability.GIT],
            permissions=[ToolPermission.GIT],
            parameters={
                "repo_path": ToolParameter(name="repo_path", type="string", description="Path to git repository. Defaults to workspace root.", required=False, default="")
            }
        )
        self.workspace_root = workspace_root
        self.layer = layer or GitRepositoryLayer()

    def run(self, repo_path: str = "") -> Dict[str, Any]:
        target = repo_path if repo_path else self.workspace_root
        return self.layer.get_status(target)


class GitInspectCommitsTool(BaseTool):
    def __init__(self, workspace_root: str, layer: Optional[GitRepositoryLayer] = None):
        super().__init__(
            name="git_inspect_commits",
            description="Inspects the recent commit history of a git repository.",
            capabilities=[ToolCapability.GIT],
            permissions=[ToolPermission.GIT],
            parameters={
                "limit": ToolParameter(name="limit", type="integer", description="Number of recent commits to return.", required=False, default=5),
                "repo_path": ToolParameter(name="repo_path", type="string", description="Path to git repository. Defaults to workspace root.", required=False, default="")
            }
        )
        self.workspace_root = workspace_root
        self.layer = layer or GitRepositoryLayer()

    def run(self, limit: int = 5, repo_path: str = "") -> List[Dict[str, Any]]:
        target = repo_path if repo_path else self.workspace_root
        commits = self.layer.inspect_commits(target, limit=limit)
        return [c.model_dump() for c in commits]


class GitDiffTool(BaseTool):
    def __init__(self, workspace_root: str, layer: Optional[GitRepositoryLayer] = None):
        super().__init__(
            name="git_diff",
            description="Generates git diff for unstaged or staged modifications.",
            capabilities=[ToolCapability.GIT],
            permissions=[ToolPermission.GIT],
            parameters={
                "cached": ToolParameter(name="cached", type="boolean", description="Whether to inspect staged changes.", required=False, default=False),
                "commit": ToolParameter(name="commit", type="string", description="Specific commit hash or range e.g. HEAD~1.", required=False, default=None),
                "repo_path": ToolParameter(name="repo_path", type="string", description="Path to repository.", required=False, default="")
            }
        )
        self.workspace_root = workspace_root
        self.layer = layer or GitRepositoryLayer()

    def run(self, cached: bool = False, commit: Optional[str] = None, repo_path: str = "") -> str:
        target = repo_path if repo_path else self.workspace_root
        return self.layer.generate_diff(target, cached=cached, commit=commit)


class GitBranchAnalysisTool(BaseTool):
    def __init__(self, workspace_root: str, layer: Optional[GitRepositoryLayer] = None):
        super().__init__(
            name="git_branch_analysis",
            description="Analyzes local and remote branches in the repository.",
            capabilities=[ToolCapability.GIT],
            permissions=[ToolPermission.GIT],
            parameters={
                "repo_path": ToolParameter(name="repo_path", type="string", description="Path to git repository.", required=False, default="")
            }
        )
        self.workspace_root = workspace_root
        self.layer = layer or GitRepositoryLayer()

    def run(self, repo_path: str = "") -> Dict[str, Any]:
        target = repo_path if repo_path else self.workspace_root
        return self.layer.analyze_branches(target)


class GitReviewPullRequestTool(BaseTool):
    def __init__(self, layer: Optional[GitRepositoryLayer] = None):
        super().__init__(
            name="git_review_pr",
            description="Reviews code diffs, checks additions/deletions, flags missing tests, and spots debug logs.",
            capabilities=[ToolCapability.GIT, ToolCapability.VERIFICATION],
            permissions=[ToolPermission.GIT],
            parameters={
                "diff_text": ToolParameter(name="diff_text", type="string", description="Unified diff text to review.", required=True)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="diff_text", error_message="diff_text cannot be empty.")
            ]
        )
        self.layer = layer or GitRepositoryLayer()

    def run(self, diff_text: str) -> Dict[str, Any]:
        return self.layer.review_diff(diff_text)


class GitCloneTool(BaseTool):
    def __init__(self, layer: Optional[GitRepositoryLayer] = None):
        super().__init__(
            name="git_clone",
            description="Clones a remote git repository into a destination directory.",
            capabilities=[ToolCapability.GIT],
            permissions=[ToolPermission.GIT, ToolPermission.NETWORK, ToolPermission.WRITE_FS],
            parameters={
                "repo_url": ToolParameter(name="repo_url", type="string", description="Git clone URL.", required=True),
                "target_dir": ToolParameter(name="target_dir", type="string", description="Directory to clone into.", required=True),
                "depth": ToolParameter(name="depth", type="integer", description="Shallow clone depth.", required=False, default=1)
            }
        )
        self.layer = layer or GitRepositoryLayer()

    def run(self, repo_url: str, target_dir: str, depth: int = 1) -> Dict[str, Any]:
        cloned = self.layer.clone_repository(repo_url, target_dir, depth=depth)
        return {"status": "cloned", "target_dir": cloned}


class GitSummarizeTool(BaseTool):
    def __init__(self, workspace_root: str, layer: Optional[GitRepositoryLayer] = None):
        super().__init__(
            name="git_summarize",
            description="Summarizes git repository state: branch, commit activity, and uncommitted changes.",
            capabilities=[ToolCapability.GIT, ToolCapability.ANALYTICS],
            permissions=[ToolPermission.GIT],
            parameters={
                "repo_path": ToolParameter(name="repo_path", type="string", description="Path to repository.", required=False, default="")
            }
        )
        self.workspace_root = workspace_root
        self.layer = layer or GitRepositoryLayer()

    def run(self, repo_path: str = "") -> Dict[str, Any]:
        target = repo_path if repo_path else self.workspace_root
        return self.layer.summarize_codebase(target)
