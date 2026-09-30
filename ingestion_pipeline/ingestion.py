import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import Document, Settings, SimpleDirectoryReader
from llama_index.core.graph_stores import SimplePropertyGraphStore
from llama_index.core.indices.property_graph import (
    ImplicitPathExtractor,
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


# [FILL IN]: Point this at your actual folder of JSON files
input_dir = BASE_DIR / "data"
input_dir.mkdir(exist_ok=True)

# Create a dummy JSON file only if there is no JSON yet, to avoid empty directory errors during testing
if not any(input_dir.rglob("*.json")):
    with open(input_dir / "sample.json", "w", encoding="utf-8") as f:
        json.dump(
            [{"text": "LlamaIndex is an orchestration framework. It helps developers build GraphRAG applications."}],
            f,
        )

reader = SimpleDirectoryReader(
    input_dir=str(input_dir),
    file_extractor={".json": JsonChatReader()},
    required_exts=[".json"],  # only JSON files are read
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
    ImplicitPathExtractor(),  # Infers implicit paths from existing node relationships
    SimpleLLMPathExtractor(llm=Settings.llm),  # Uses the LLM to extract entities and relations
]

index = PropertyGraphIndex.from_documents(
    documents,
    kg_extractors=kg_extractors,
    property_graph_store=graph_store,
    show_progress=True,
)


# 4. QUERYING THE GRAPHRAG SYSTEM
# Default retrievers: LLM synonym expansion + vector search over graph nodes
query_engine = index.as_query_engine(llm=Settings.llm)

# [FILL IN]: Run queries to test your knowledge graph
query = "What framework helps build GraphRAG applications?"
response = query_engine.query(query)
print(f"Query: {query}")
print(f"Answer: {response}")
