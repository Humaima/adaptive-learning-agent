import json
from pathlib import Path
import networkx as nx

from src.models.schemas import Concept


class ConceptGraph:
    """
    Directed graph where an edge (A -> B) means 'A is a prerequisite of B'.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_concept(self, concept: Concept):
        self.graph.add_node(
            concept.id, name=concept.name, domain=concept.domain, description=concept.description
        )

    def get_concepts_by_domain(self, domain: str) -> list[str]:
        return [
            node_id
            for node_id, attrs in self.graph.nodes(data=True)
            if attrs is not None and attrs.get("domain") == domain
        ]

    def add_prerequisite(self, prerequisite_id: str, concept_id: str):
        """prerequisite_id must be learned before concept_id."""
        if prerequisite_id not in self.graph or concept_id not in self.graph:
            raise ValueError("Both concepts must be added before linking them.")
        self.graph.add_edge(prerequisite_id, concept_id)
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_edge(prerequisite_id, concept_id)
            raise ValueError(f"Adding edge {prerequisite_id} -> {concept_id} creates a cycle.")

    def get_direct_prerequisites(self, concept_id: str) -> list[str]:
        return list(self.graph.predecessors(concept_id))

    def get_all_prerequisites(self, concept_id: str) -> list[str]:
        """All ancestors, topologically ordered (learn earliest ones first)."""
        ancestors = nx.ancestors(self.graph, concept_id)
        subgraph = self.graph.subgraph(ancestors | {concept_id})
        order = list(nx.topological_sort(subgraph))
        order.remove(concept_id)
        return order

    def get_dependents(self, concept_id: str) -> list[str]:
        """Concepts that require this one — useful once mastery updates."""
        return list(self.graph.successors(concept_id))

    def get_learning_path(self, target_concept_id: str) -> list[str]:
        """Full ordered path: prerequisites in learning order, then the target."""
        return self.get_all_prerequisites(target_concept_id) + [target_concept_id]

    def to_json(self, path: str):
        data = nx.node_link_data(self.graph)
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def from_dataset_json(cls, path: str, strict: bool = False) -> "ConceptGraph":
        """
        Loads a dataset shaped as:
        {
          "concepts": [{"id", "name", "domain", "description"}, ...],
          "prerequisites": [{"prerequisite_id", "concept_id"}, ...]
        }
        Skips (or raises on, if strict=True) edges that are cyclic or reference unknown ids —
        LLM-drafted datasets occasionally produce one or two of these.
        """
        data = json.loads(Path(path).read_text())
        cg = cls()

        for c in data["concepts"]:
            cg.add_concept(Concept(**c))

        skipped = []
        for edge in data["prerequisites"]:
            prereq_id, concept_id = edge["prerequisite_id"], edge["concept_id"]
            try:
                cg.add_prerequisite(prereq_id, concept_id)
            except ValueError as e:
                skipped.append((prereq_id, concept_id, str(e)))

        if skipped:
            report = "\n".join(f"  {p} -> {c}: {err}" for p, c, err in skipped)
            msg = f"Skipped {len(skipped)} invalid/cyclic edges:\n{report}"
            if strict:
                raise ValueError(msg)
            print(f"[WARNING] {msg}")

        return cg

    def get_next_recommended_concepts(
        self, mastery: dict[str, float], threshold: float, limit: int = 4
    ) -> list[str]:
        """
        Returns up to `limit` concept ids the student is ready to learn next:
        not yet mastered, but every direct prerequisite already is.
        Ordered by the graph's natural topological order (earlier concepts first).
        """
        mastered = {cid for cid, score in mastery.items() if score is not None and score >= threshold}

        recommended = []
        for cid in nx.topological_sort(self.graph):
            if cid in mastered:
                continue
            prereqs = set(self.get_direct_prerequisites(cid))
            if prereqs.issubset(mastered):
                recommended.append(cid)
            if len(recommended) >= limit:
                break
        return recommended

    def get_concept_info(self, concept_id: str) -> dict:
        """Returns {'name', 'domain', 'description'} for a single concept."""
        if concept_id not in self.graph.nodes:
            raise ValueError(f"Concept '{concept_id}' not found in graph.")
        data = self.graph.nodes[concept_id]
        return {
            "name": data.get("name", concept_id),
            "domain": data.get("domain", ""),
            "description": data.get("description", ""),
        }