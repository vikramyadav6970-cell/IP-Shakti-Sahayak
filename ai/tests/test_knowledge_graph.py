"""Unit tests for the Knowledge Graph and Multi-Hop reasoning engine."""

import pytest

from src.graph.neo4j_client import (
    GraphHop,
    MultiHopQueryResult,
    KnowledgeGraphEngine,
    query_knowledge_graph,
    DEFAULT_GRAPH_NODES,
)


def test_in_memory_graph_nodes_and_edges():
    """Knowledge graph initializes core nodes across products, herbs, laws, and sections."""
    engine = KnowledgeGraphEngine()
    graph = engine._build_in_memory_graph()

    assert len(graph["products"]) >= 3
    assert len(graph["herbs"]) >= 3
    assert len(graph["laws"]) >= 5
    assert len(graph["sections"]) >= 5


def test_multi_hop_ashwagandha_eu_export():
    """Multi-hop query for Ashwagandha export to EU traverses formulation -> BDA -> Nagoya -> EU THMPD."""
    res: MultiHopQueryResult = query_knowledge_graph(
        herb_name="Ashwagandha",
        destination_jurisdiction="EU",
        intent="EXPORT",
    )

    assert len(res.hops) == 3
    assert res.requires_abs_clearance is True
    assert res.requires_foreign_authorization is True
    assert any("Nagoya" in s for s in res.applicable_statutes)
    assert any("EU Directive" in s for s in res.applicable_statutes)
    assert "Withania somnifera" in res.hops[0].target_node
    assert len(res.supporting_chunk_ids) == 3


def test_multi_hop_turmeric_us_fda():
    """Multi-hop query for Turmeric export to USA connects BDA export clearance with US DSHEA cGMP."""
    res: MultiHopQueryResult = query_knowledge_graph(
        herb_name="Turmeric Curcumin",
        destination_jurisdiction="USA",
        intent="EXPORT",
    )

    assert len(res.hops) == 3
    assert any("DSHEA" in s for s in res.applicable_statutes)
    assert "Curcuma longa" in res.hops[0].target_node
    assert "cGMP" in res.synthesized_regulatory_path
