"""Graph module — Knowledge Graph engine and multi-hop reasoning."""

from src.graph.neo4j_client import (
    GraphHop,
    MultiHopQueryResult,
    KnowledgeGraphEngine,
    query_knowledge_graph,
)

__all__ = [
    "GraphHop",
    "MultiHopQueryResult",
    "KnowledgeGraphEngine",
    "query_knowledge_graph",
]
