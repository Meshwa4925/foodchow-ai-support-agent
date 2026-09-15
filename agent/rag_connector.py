from rag.rag_search import search_knowledge_base


def get_relevant_knowledge(customer_query, top_k=3):
    """
    Search the FoodChow Knowledge Base
    and return relevant information for the AI Agent.
    """

    results = search_knowledge_base(
        customer_query,
        top_k=top_k
    )

    if not results:
        return {
            "success": False,
            "query": customer_query,
            "message": "No relevant knowledge found.",
            "knowledge": []
        }

    knowledge = []

    for result in results:
        knowledge.append(
            {
                "source": result["source"],
                "content": result["content"],
                "distance": result["distance"]
            }
        )

    return {
        "success": True,
        "query": customer_query,
        "knowledge": knowledge
    }


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("--------------------------------")
    print("FoodChow Agent - RAG Connector")
    print("--------------------------------")

    customer_query = input(
        "\nEnter customer issue: "
    )

    result = get_relevant_knowledge(
        customer_query,
        top_k=3
    )

    print("\nAgent received knowledge:\n")

    if result["success"]:

        for i, item in enumerate(
            result["knowledge"],
            start=1
        ):

            print("=" * 60)

            print(
                f"Knowledge {i}"
            )

            print(
                f"Source: {item['source']}"
            )

            print(
                f"Distance: {item['distance']:.4f}"
            )

            print("\nContent:")

            print(
                item["content"]
            )

    else:

        print(
            result["message"]
        )