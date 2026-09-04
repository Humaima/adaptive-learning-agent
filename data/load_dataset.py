from src.graph.concept_graph import ConceptGraph

if __name__ == "__main__":
    cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")
    print("ML concepts:", cg.get_concepts_by_domain("ML"))
    print("Path to backpropagation:", cg.get_learning_path("backpropagation"))
