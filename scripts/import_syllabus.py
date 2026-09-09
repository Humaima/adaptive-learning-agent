import sys
from pathlib import Path

from src.graph.concept_graph import ConceptGraph
from src.graph.syllabus_extractor import extract_syllabus_dataset, merge_dataset

DATASET_PATH = "data/concepts_dataset.json"


def main(syllabus_file: str):
    syllabus_text = Path(syllabus_file).read_text()
    cg = ConceptGraph.from_dataset_json(DATASET_PATH)

    print(f"Extracting concepts from '{syllabus_file}'...")
    dataset = extract_syllabus_dataset(syllabus_text, cg)
    print(f"Extracted {len(dataset.concepts)} new concepts, {len(dataset.prerequisites)} prerequisite edges.")

    added_concepts, added_edges = merge_dataset(DATASET_PATH, dataset.concepts, dataset.prerequisites, DATASET_PATH)
    print(f"Merged {added_concepts} concepts and {added_edges} edges into {DATASET_PATH}")

    print("\nRe-validating merged graph (any warnings below indicate a skipped bad edge)...")
    ConceptGraph.from_dataset_json(DATASET_PATH)
    print("Done. Review the diff in data/concepts_dataset.json before committing.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.import_syllabus <path_to_syllabus.txt>")
        sys.exit(1)
    main(sys.argv[1])