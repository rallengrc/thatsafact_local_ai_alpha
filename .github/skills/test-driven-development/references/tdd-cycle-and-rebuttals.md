# TDD Cycle & Rationalization Prevention

> **Source:** Superpowers v7.0.0 (`code/superpowers/skills/test-driven-development/`)

---

## 1. Why Test Order Matters

Writing tests after writing code suffers from four psychological and technical defects:
1. **Confirmation Bias:** Post-hoc tests mirror the implementation rather than validating the specification.
2. **False Passes:** Tests written after code are rarely tested in a failing state; they may pass trivially due to flawed assertion syntax.
3. **Coupled Design:** Pre-written code dictates test shape, leading to awkward mocks and untestable seams.
4. **Skipped Edge Cases:** Once code runs, fatigue sets in and negative/boundary tests get skipped.

---

## 2. Rationalization Prevention Table

| Common Excuse | Hard Reality | Required Action |
| :--- | :--- | :--- |
| "I'll write code first to see how it works, then add tests" | You will write tests that confirm your code, not tests that prove requirements. | Delete code. Write the test first. |
| "This change is too trivial for TDD" | Trivial changes cause 40% of production regressions. | Write the 3-line unit test. |
| "Writing tests first slows me down" | TDD eliminates hours of manual debugging and rework. | Follow Red-Green cycle. |
| "The existing codebase has no tests for this" | You are adding new code; start the test foundation now. | Add the first test file. |
| "I'll test it manually with curl / CLI" | Manual tests do not run in CI or protect against regressions. | Formalize the curl call into pytest. |

---

## 3. Python Pytest TDD Example

```python
# Step 1: Write test (test_router.py)
def test_tantivy_robust_parsing():
    from scripts.search_router.tantivy_searcher import TantivySearcher
    searcher = TantivySearcher()
    # Punctuation query that previously triggered a Rust syntax error
    results = searcher.search("def test_func():")
    assert isinstance(results, list)

# Step 2: Run test -> Fails with AttributeError or SyntaxError
# Step 3: Implement minimal fallback in tantivy_searcher.py
# Step 4: Run test -> Passes
# Step 5: Refactor
```
