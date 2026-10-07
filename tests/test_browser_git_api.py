"""Tests for Browser Intelligence, Git Intelligence, and API Intelligence."""

import os
import time
import pytest
from alpha.browser.adapter import BrowserToolAdapter, ExtractedPage
from alpha.browser.tools import BrowserSearchTool, BrowserExtractTool, BrowserSummarizeTool, BrowserCompareTool
from alpha.git.layer import GitRepositoryLayer
from alpha.git.tools import GitStatusTool, GitReviewPullRequestTool, GitSummarizeTool
from alpha.api.gateway import APIGateway, CircuitState, CircuitBreakerOpenError, TokenBucketRateLimiter
from alpha.api.tools import ApiRestRequestTool, ApiWebhookTriggerTool, ApiCircuitBreakerStatusTool

def test_browser_adapter_and_tools():
    adapter = BrowserToolAdapter()
    sample_html = """
    <html>
      <head><title>System Architecture Guide</title></head>
      <body>
        <nav><a href="/home">Home</a></nav>
        <h1>Core Architecture</h1>
        <p>Alpha uses a <strong>decoupled</strong> cognitive scaffolding approach.</p>
        <script>console.log("ignore me");</script>
      </body>
    </html>
    """
    page = adapter.extract_content(sample_html, url="https://alpha.internal/arch")
    assert page.title == "System Architecture Guide"
    assert "Core Architecture" in page.markdown_content
    assert "ignore me" not in page.markdown_content
    assert page.word_count > 0

    # Source ranking & citation
    ranked = adapter.rank_sources("cognitive scaffolding", [page])
    assert len(ranked) == 1
    assert ranked[0].relevance_score > 0.0
    assert "System Architecture Guide" in ranked[0].citation

    # Browser Tools
    search_tool = BrowserSearchTool(adapter)
    results = search_tool.run(query="python concurrency", num_results=2)
    assert len(results) >= 1
    assert "citation" in results[0]

    compare_tool = BrowserCompareTool(adapter)
    comp_res = compare_tool.run(pages=[
        {"url": "u1", "title": "t1", "clean_text": "Sample content one"},
        {"url": "u2", "title": "t2", "clean_text": "Sample content two"}
    ])
    assert comp_res["sources_compared"] == 2

def test_git_layer_and_tools():
    git = GitRepositoryLayer()
    # Check current workspace repository
    status = git.get_status(os.getcwd())
    assert "branch" in status
    assert "is_clean" in status

    # Review PR diff
    diff_hunk = """
--- a/alpha/core/engine.py
+++ b/alpha/core/engine.py
@@ -10,3 +10,4 @@
+print("debug")
+# TODO: Fix this later
"""
    review = git.review_diff(diff_hunk)
    assert review["files_changed_count"] == 1
    assert any("TODO" in flag for flag in review["review_flags"])
    assert any("debug" in flag for flag in review["review_flags"])

    # Git Review PR tool
    pr_tool = GitReviewPullRequestTool(git)
    pr_res = pr_tool.run(diff_text=diff_hunk)
    assert pr_res["additions"] == 2

def test_api_gateway_and_circuit_breaker():
    gw = APIGateway()
    # Token Bucket Rate Limiter
    limiter = TokenBucketRateLimiter(rate_per_second=2.0, capacity=2.0)
    assert limiter.acquire() is True
    assert limiter.acquire() is True
    assert limiter.acquire() is False  # Exhausted capacity

    # Circuit Breaker state transitions
    cb = gw._get_circuit_breaker("test.api.internal")
    assert cb.state == CircuitState.CLOSED

    # Record 3 failures to trip
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    # Mock REST request tool
    rest_tool = ApiRestRequestTool(gw)
    resp = rest_tool.run(method="GET", url="mock://service/items")
    assert resp["status_code"] == 200
    assert resp["data"]["mock_response"] == "ok"

    # Webhook trigger tool with HMAC signature
    wh_tool = ApiWebhookTriggerTool(gw)
    wh_res = wh_tool.run(
        target_url="mock://webhook/events",
        event_name="build.completed",
        payload={"build_id": 123},
        secret_key="secret123"
    )
    assert wh_res["status_code"] == 200
