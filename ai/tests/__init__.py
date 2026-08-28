"""Tests — AI layer test suite.

Mirror the src/ structure: one test_*.py per module.
Use pytest markers:
  @pytest.mark.smoke   — tests that call real APIs (skip in CI)
  @pytest.mark.slow    — tests that take > 10s (e.g. embedding model loading)
"""
