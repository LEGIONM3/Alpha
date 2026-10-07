# WHAT_FAILED.md
## Discovered Failures, Bugs, and Architectural Breakages

**Audit Completed:** October 2026  

---

### 1. Root-Cause Analysis of Discovered Failures

1. **Client Timeout Premature Fallback (500ms):**
   - *Failure:* `OpenAICompatibleClient` in `alpha/model_intelligence/connector/client.py` defaulted to `timeout_seconds = 0.5` with `enable_mock_fallback = True`.
   - *Consequence:* Any real model query taking > 500ms silently timed out and returned canned mock outputs, giving the illusion of model connectivity while completely bypassing the real foundation model.
   - *Root Cause:* Unit test artifact left in production connector.

2. **Gemma 4 Heretic Thinking Token Truncation:**
   - *Failure:* When `max_tokens` was configured <= 450 for structured schema output, Gemma 4 Heretic consumed 400-580 tokens in its internal chain-of-thought (`reasoning_content`) and hit `finish_reason: length` before emitting valid JSON into `content`.
   - *Consequence:* `json.decoder.JSONDecodeError` on parsing model output.
   - *Root Cause:* Underestimating reasoning token overhead of deep-thinking SLMs.

3. **LM Studio Bare `json_object` Rejection (HTTP 400):**
   - *Failure:* Sending `response_format: {"type": "json_object"}` returned HTTP 400 Bad Request from the local LM Studio server.
   - *Consequence:* Structured output tests failed when attempting standard JSON object mode.
   - *Root Cause:* Local endpoint requires formal OpenAI `json_schema` specifications rather than unstructured `json_object`.

4. **Missing Identity Source of Truth (`alpha_identity.md`):**
   - *Failure:* `alpha_identity.md` did not exist on disk in the repository root prior to this run.
   - *Consequence:* Identity loader was unable to find canonical specification.

5. **Heuristic Cognitive Pathways Disconnected from Model:**
   - *Failure:* `TaskDecomposer`, `Planner`, `ReflectionEngine`, and `KnowledgeSynthesisEngine` contained static string templates and topological converters that never queried the model endpoint.

6. **Tool Discovery Using Hash Projection instead of Real Embeddings:**
   - *Failure:* `ToolSemanticVector` in `alpha/tools/discovery.py` computed a 128-dimensional character hash projection (`hash(tok) % 128`) instead of querying `text-embedding-nomic-embed-text-v1.5`.

7. **Initial Boot Stage 6 Incompatibility:**
   - *Failure:* `alpha_boot.py` initially queried `runtime.agents` instead of `runtime.registry.count()`.
   - *Consequence:* Triggered fail-safe boot abort at Stage 6.
