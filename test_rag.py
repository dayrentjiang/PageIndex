#!/usr/bin/env python3
"""
Simple RAG test script using PageIndex tree structure
Based on the cookbook approach - minimal and straightforward
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("CHATGPT_API_KEY"))
MODEL = "gpt-4o-2024-11-20"


def load_tree(tree_path):
    """Load the PageIndex tree structure"""
    with open(tree_path, 'r') as f:
        data = json.load(f)
    return data


def create_tree_summary(tree_data):
    """Create a simplified view of the tree for LLM navigation"""
    structure = tree_data.get('structure', [])

    def summarize_node(node, level=0):
        indent = "  " * level
        summary = f"{indent}- {node.get('title', 'Untitled')} (Node ID: {node.get('node_id', 'N/A')}, Pages: {node.get('start_index', '?')}-{node.get('end_index', '?')})\n"
        if 'summary' in node:
            summary += f"{indent}  Summary: {node['summary'][:150]}...\n"

        # Process child nodes
        if 'nodes' in node:
            for child in node['nodes']:
                summary += summarize_node(child, level + 1)

        return summary

    tree_summary = "Document Tree Structure:\n\n"
    for node in structure:
        tree_summary += summarize_node(node)

    return tree_summary


def tree_search(query, tree_summary):
    """
    Step 1: Tree Search - LLM identifies relevant sections
    """
    prompt = f"""You are helping to search a document. Given the query and document structure, identify the most relevant sections (node IDs).

Query: {query}

{tree_summary}

Return a JSON list of relevant node IDs, ranked by relevance:
{{"node_ids": ["0001", "0002", ...]}}

Only return the JSON, nothing else."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result = response.choices[0].message.content.strip()
    # Extract JSON from markdown code blocks if present
    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    elif "```" in result:
        result = result.split("```")[1].split("```")[0].strip()

    node_ids = json.loads(result)["node_ids"]
    print(f"✓ Tree Search found {len(node_ids)} relevant sections: {node_ids}")
    return node_ids


def extract_context(tree_data, node_ids):
    """
    Step 2: Context Extraction - Get full text from identified nodes
    """
    structure = tree_data.get('structure', [])

    def find_node_by_id(nodes, node_id):
        for node in nodes:
            if node.get('node_id') == node_id:
                return node
            if 'nodes' in node:
                result = find_node_by_id(node['nodes'], node_id)
                if result:
                    return result
        return None

    contexts = []
    for node_id in node_ids:
        node = find_node_by_id(structure, node_id)
        if node:
            contexts.append({
                'node_id': node_id,
                'title': node.get('title', 'Untitled'),
                'pages': f"{node.get('start_index', '?')}-{node.get('end_index', '?')}",
                'text': node.get('text', node.get('summary', ''))
            })

    print(f"✓ Extracted context from {len(contexts)} sections")
    return contexts


def generate_answer(query, contexts):
    """
    Step 3: Answer Generation - LLM generates answer with citations
    """
    # Build context string with citations
    context_str = "\n\n".join([
        f"[{ctx['node_id']}] {ctx['title']} (Pages {ctx['pages']}):\n{ctx['text']}"
        for ctx in contexts
    ])

    prompt = f"""Answer the following question based on the provided document excerpts. Include specific citations with node IDs and page numbers.

Question: {query}

Document Excerpts:
{context_str}

Provide a clear, concise answer with citations in the format [Node ID, Page X]."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    answer = response.choices[0].message.content.strip()
    print(f"✓ Generated answer with citations")
    return answer


def query_document(tree_path, query):
    """
    Main RAG pipeline: Tree Search → Context Extraction → Answer Generation
    """
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    # Load tree
    print("Loading tree structure...")
    tree_data = load_tree(tree_path)
    tree_summary = create_tree_summary(tree_data)

    # Step 1: Tree Search
    print("\n1. Tree Search - Finding relevant sections...")
    node_ids = tree_search(query, tree_summary)

    # Step 2: Context Extraction
    print("\n2. Context Extraction - Retrieving full text...")
    contexts = extract_context(tree_data, node_ids)

    # Step 3: Answer Generation
    print("\n3. Answer Generation - Creating answer with citations...")
    answer = generate_answer(query, contexts)

    print(f"\n{'='*60}")
    print("ANSWER:")
    print(f"{'='*60}\n")
    print(answer)
    print(f"\n{'='*60}\n")

    return answer


if __name__ == "__main__":
    # Path to your generated tree structure
    TREE_PATH = "./results/Blood-Donation-2024_structure.json"

    # Test queries
    test_queries = [
        "What are the deferral periods for tattoos and piercings?",
        "What is the Plasma Pathway?",
        "What are the recommendations for men who have sex with men (MSM)?"
    ]

    print("\n" + "="*60)
    print("PageIndex RAG Test Script")
    print("="*60)

    import sys

    # Check if running in interactive mode
    run_interactive = sys.stdin.isatty()

    # Run test queries
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n### Test Query {i}/{len(test_queries)} ###")
        query_document(TREE_PATH, query)

        if i < len(test_queries) and run_interactive:
            input("\nPress Enter to continue to next query...")

    print("\n✅ All test queries completed!")

    # Interactive mode (only if stdin is available)
    if run_interactive:
        print("\n" + "="*60)
        print("Interactive Mode - Enter your own queries (type 'quit' to exit)")
        print("="*60)

        while True:
            user_query = input("\n> Your question: ").strip()
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            if user_query:
                query_document(TREE_PATH, user_query)
    else:
        print("\n(Run in terminal for interactive mode)")
