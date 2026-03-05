#!/usr/bin/env python3
"""
Simple interactive RAG - Ask a question about your document
"""

import json
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("CHATGPT_API_KEY"))
MODEL = "gpt-4o-2024-11-20"
TREE_PATH = "./results/Blood-Donation-2024_structure.json"


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
    """Step 1: Tree Search - LLM identifies relevant sections"""
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
    return node_ids


def extract_context(tree_data, node_ids):
    """Step 2: Context Extraction - Get full text from identified nodes"""
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

    return contexts


def generate_answer(query, contexts):
    """Step 3: Answer Generation - LLM generates answer with citations"""
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
    return answer


def query_document(query):
    """Main RAG pipeline"""
    print(f"\n🔍 Searching document for: '{query}'\n")

    # Load tree
    tree_data = load_tree(TREE_PATH)
    tree_summary = create_tree_summary(tree_data)

    # Step 1: Tree Search
    print("→ Finding relevant sections...")
    node_ids = tree_search(query, tree_summary)
    print(f"  Found {len(node_ids)} relevant sections\n")

    # Step 2: Context Extraction
    print("→ Extracting content...")
    contexts = extract_context(tree_data, node_ids)
    print(f"  Retrieved text from {len(contexts)} sections\n")

    # Step 3: Answer Generation
    print("→ Generating answer...\n")
    answer = generate_answer(query, contexts)

    print("=" * 70)
    print("ANSWER:")
    print("=" * 70)
    print(answer)
    print("=" * 70)

    return answer


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("📚 PageIndex RAG - Blood Donation Policy Document")
    print("=" * 70)

    while True:
        print("\n")
        question = input("💬 Your question (or 'quit' to exit): ").strip()

        if question.lower() in ['quit', 'exit', 'q', '']:
            print("\n👋 Goodbye!")
            break

        try:
            query_document(question)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again with a different question.\n")
