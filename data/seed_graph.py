from src.graph.concept_graph import ConceptGraph
from src.models.schemas import Concept

def build_neural_networks_101() -> ConceptGraph:
    cg = ConceptGraph()

    concepts = [
        Concept(id="linear_algebra", name="Linear Algebra",
                description="Vectors, matrices, dot products, matrix multiplication."),
        Concept(id="calculus", name="Calculus",
                description="Derivatives, chain rule, partial derivatives."),
        Concept(id="probability", name="Probability Basics",
                description="Random variables, distributions, expectation."),
        Concept(id="neural_networks", name="Neural Networks",
                description="Layers, weights, activations, forward pass."),
        Concept(id="backpropagation", name="Backpropagation",
                description="Computing gradients via the chain rule to update weights."),
    ]
    for c in concepts:
        cg.add_concept(c)

    # prerequisite -> concept
    cg.add_prerequisite("linear_algebra", "neural_networks")
    cg.add_prerequisite("calculus", "neural_networks")
    cg.add_prerequisite("probability", "neural_networks")
    cg.add_prerequisite("neural_networks", "backpropagation")
    cg.add_prerequisite("calculus", "backpropagation")

    return cg


if __name__ == "__main__":
    cg = build_neural_networks_101()
    cg.to_json("data/neural_networks_101.json")
    print("Seed graph saved to data/neural_networks_101.json")
    print("Learning path to 'backpropagation':", cg.get_learning_path("backpropagation"))