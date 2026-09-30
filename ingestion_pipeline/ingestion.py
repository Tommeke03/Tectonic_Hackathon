import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import Document, Settings, SimpleDirectoryReader
from llama_index.core.graph_stores import SimplePropertyGraphStore
from llama_index.core.graph_stores.types import ChunkNode
from llama_index.core.indices.property_graph import (
    PropertyGraphIndex,
    SimpleLLMPathExtractor,
)
from llama_index.core.readers.base import BaseReader
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.anthropic import Anthropic

BASE_DIR = Path(__file__).parent

# 1. SETUP API KEYS & MODELS
# Keys are read from environment variables, or from a .env file next to this script
load_dotenv(BASE_DIR / ".env")
for key in ("ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
    if not os.environ.get(key):
        sys.exit(f"{key} is not set. Put it in {BASE_DIR / '.env'} as: {key}=your-key")

# Claude for entity extraction and answering (Anthropic has no embeddings API, so Gemini embeds)
Settings.llm = Anthropic(model="claude-haiku-4-5-20251001", temperature=0.1, max_retries=8)
Settings.embed_model = GoogleGenAIEmbedding(model_name="gemini-embedding-001")

print("Settings configured: Claude for the LLM, Gemini for embeddings.")


# 2. DOCUMENT INGESTION
class JsonChatReader(BaseReader):
    """Reads a JSON file (a list of records or a single object) into Documents, one per record."""

    def load_data(self, file, extra_info=None):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else [data]
        return [
            Document(
                text=json.dumps(record, ensure_ascii=False),
                metadata={"file_name": Path(file).name, **(extra_info or {})},
            )
            for record in records
        ]


class MarkdownFrontMatterReader(BaseReader):
    """Reads a Markdown file into one Document. The `key: value` front matter becomes metadata, the body becomes the text."""

    def load_data(self, file, extra_info=None):
        raw = Path(file).read_text(encoding="utf-8")
        metadata, body = {}, raw
        if raw.startswith("---"):
            _, front_matter, body = raw.split("---", 2)
            for line in front_matter.strip().splitlines():
                key, _, value = line.partition(":")
                metadata[key.strip()] = value.strip()
        return [Document(text=body.strip(), metadata={**metadata, "file_name": Path(file).name, **(extra_info or {})})]


# Ingest everything in the repo's assets folder (Markdown policies and Teams JSON exports)
input_dir = BASE_DIR.parent / "assets"

reader = SimpleDirectoryReader(
    input_dir=str(input_dir),
    file_extractor={".json": JsonChatReader(), ".md": MarkdownFrontMatterReader()},
    required_exts=[".json", ".md"],
    recursive=True,
)
documents = reader.load_data()
print(f"Loaded {len(documents)} documents.")


# 3. KNOWLEDGE GRAPH CONSTRUCTION
# [FILL IN]: If using a persistent graph database like Neo4j, swap SimplePropertyGraphStore
# with Neo4jPropertyGraphStore
graph_store = SimplePropertyGraphStore()

# Extractors guide how entities and relations are extracted from the text chunks
kg_extractors = [
    SimpleLLMPathExtractor(llm=Settings.llm),  # Uses the LLM to extract entities and relations
]

index = PropertyGraphIndex.from_documents(
    documents,
    kg_extractors=kg_extractors,
    property_graph_store=graph_store,
    show_progress=True,
)


# 4. EXPORT THE KNOWLEDGE GRAPH
# graph.json goes to the repo-level graph/ folder, which the frontend reads directly;
# LlamaIndex's own graph_store.json stays in this pipeline's output/ folder.
graph_dir = BASE_DIR.parent / "graph"
output_dir = BASE_DIR / "output"
graph_dir.mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)

# a) Plain JSON (nodes + edges, no embeddings) that any other application can read.
#    Each node's "properties" carry the source file_name/file_path it was extracted from.
graph = graph_store.graph
nodes_out = [
    {
        "id": node.id,
        "type": "chunk" if isinstance(node, ChunkNode) else "entity",
        "label": node.label,
        **({"text": node.text} if isinstance(node, ChunkNode) else {"name": node.name}),
        "properties": node.properties,
    }
    for node in graph.nodes.values()
]
edges_out = [
    {"source": r.source_id, "target": r.target_id, "label": r.label, "properties": r.properties}
    for r in graph.relations.values()
]
with open(graph_dir / "graph.json", "w", encoding="utf-8") as f:
    json.dump({"nodes": nodes_out, "edges": edges_out}, f, ensure_ascii=False, indent=2, default=str)

# b) LlamaIndex's own format, only useful to reload the graph inside LlamaIndex. It has no embeddings
#    (those live in a separate vector store that is not saved), so vector search will not work after reloading.
#    SimplePropertyGraphStore.from_persist_path("output/graph_store.json")
graph_store.persist(str(output_dir / "graph_store.json"))

print(f"Exported {len(nodes_out)} nodes and {len(edges_out)} edges to {graph_dir / 'graph.json'}")


# 5. QUERYING THE GRAPHRAG SYSTEM
# Default retrievers: LLM synonym expansion + vector search over graph nodes
query_engine = index.as_query_engine(llm=Settings.llm)

# [FILL IN]: Run queries to test your knowledge graph
query = "Hoeveel thuiswerkvergoeding krijgt een werknemer in Belgie?"
response = query_engine.query(query)
print(f"Query: {query}")
print(f"Answer: {response}")
