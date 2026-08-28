"""Unit tests for the Evaluation Harness."""

import json
from pathlib import Path
import pytest

from src.evaluation.run_eval import EvalHarness, EvalMetrics, run_evaluation


@pytest.mark.asyncio
async def test_eval_harness_dataset_loading():
    """Harness successfully loads the 100-question benchmark dataset."""
    harness = EvalHarness()
    questions = harness.load_dataset()

    assert len(questions) >= 50
    assert "id" in questions[0]
    assert "domain_intent" in questions[0]
    assert "expected_collections" in questions[0]


@pytest.mark.asyncio
async def test_eval_harness_execution_sample():
    """Harness runs across a sample subset and computes explainable metrics."""
    harness = EvalHarness()
    metrics: EvalMetrics = await harness.run(max_samples=10)

    assert metrics.total_questions == 10
    assert metrics.collection_routing_accuracy >= 0.70
    assert metrics.context_gathering_accuracy >= 0.90
    assert metrics.sub_task_decomposition_accuracy >= 0.90
    assert metrics.overall_score > 0.0


def test_eval_harness_cli_run(tmp_path):
    """Harness runs end-to-end and outputs structured JSON report."""
    output_file = tmp_path / "test_report.json"
    metrics = run_evaluation(output_file=output_file, max_samples=5)

    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_questions"] == 5
    assert "overall_score" in data
