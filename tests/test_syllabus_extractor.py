import json
from src.graph.generate_dataset import ConceptDraft, PrerequisiteEdge
from src.graph.syllabus_extractor import merge_dataset


def test_merge_adds_new_concepts_and_edges(tmp_path):
    existing = {"concepts": [], "prerequisites": []}
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(existing))

    new_concepts = [ConceptDraft(id="cell_structure", name="Cell Structure", domain="Biology", description="...")]
    added_c, added_e = merge_dataset(str(path), new_concepts, [], str(path))

    result = json.loads(path.read_text())
    assert added_c == 1
    assert result["concepts"][0]["id"] == "cell_structure"


def test_merge_dedupes_colliding_ids_and_remaps_edges(tmp_path):
    existing = {
        "concepts": [{"id": "cell_structure", "name": "Cell Structure", "domain": "Biology", "description": "..."}],
        "prerequisites": [],
    }
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(existing))

    new_concepts = [
        ConceptDraft(id="cell_structure", name="Cell Structure (Chem context)", domain="Chemistry", description="..."),
        ConceptDraft(id="atomic_bonds", name="Atomic Bonds", domain="Chemistry", description="..."),
    ]
    new_edges = [PrerequisiteEdge(prerequisite_id="atomic_bonds", concept_id="cell_structure")]

    added_c, added_e = merge_dataset(str(path), new_concepts, new_edges, str(path))
    result = json.loads(path.read_text())

    ids = {c["id"] for c in result["concepts"]}
    assert "cell_structure_chemistry" in ids  # renamed to avoid collision
    assert added_c == 2 and added_e == 1

    edge = result["prerequisites"][0]
    assert edge["concept_id"] == "cell_structure_chemistry"  # edge correctly followed the rename