from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    QueryType,
    QueryCaptionType,
    QueryAnswerType,
)

# -------------------------------------------------------
# Demo 2: Advanced Search Queries — Azure AI Search
#
# Builds on Demo 1 (run that first to populate the index).
#
# This script shows four query modes using the fields that
# the cognitive skill pipeline extracted from the PDFs:
#   - locations   (Named Entity Recognition)
#   - people      (Named Entity Recognition)
#   - keyphrases  (Key Phrase Extraction)
#
#   1. Full-text     — keyword search across all enriched fields
#   2. Field-scoped  — search only within a specific field
#   3. Semantic      — AI re-ranks results by meaning
#                      (requires Basic tier; falls back gracefully)
#   4. Facets        — aggregation counts across enriched fields #frequency of word repetetion across all documents
#
# Usage:
#   python 2_SemanticSearch.py
# -------------------------------------------------------

load_dotenv()

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT", "").rstrip("/")
QUERY_KEY       = os.getenv("QUERY_KEY")
INDEX_NAME      = os.getenv("INDEX_NAME", "index-tdai-aisearch")

SEP = "-" * 62


def get_client() -> SearchClient:
    return SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(QUERY_KEY),
    )


def doc_name(document: dict) -> str:
    """Return the source filename stored in the document."""
    return document.get("source") or document["id"]




# -- Query 1: Field-scoped search search using specific fileds here location therefore keyword search------------------------
def demo_field_scoped(client: SearchClient):
    print(f"\n{SEP}")
    print("  Query 1 — Field-scoped: find documents mentioning 'Las Vegas'")
    print("  Mode: search.in() on the locations field only")
    print(SEP)
    results = client.search(
        search_text="Las Vegas",
        search_fields=["locations"],
        top=2,
        select=["id", "source", "locations", "people", "keyphrases"],
    )
    for doc in results:
        score = doc.get("@search.score", 0)#keyword search score, there is no scale for this
        print(f"  [{score:.2f}]  {doc_name(doc)}") #display the document name along with its keyword search score
        print(f"    People    : {', '.join(doc.get('people', [])[:5]) or '(none)'}")#display the first 5 people mentioned in the document, or '(none)' if empty
        print(f"    Keyphrases: {', '.join(doc.get('keyphrases', [])[:5])}")
        print()
    print("  Key concept: restricting search to specific fields improves precision.")


# -- Query 2: Semantic search using meaning understanding not just key phrases-----------------------------
def demo_semantic(client: SearchClient):
    print(f"\n{SEP}")
    print("  Query 2 — Semantic: 'famous landmarks and tourist attractions'")
    print("  Mode: AI re-ranker — scores by conceptual meaning, not just keywords")
    print(SEP)
    try:
        results = client.search(
            search_text="famous landmarks and tourist attractions",
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="default",
            query_caption=QueryCaptionType.EXTRACTIVE,
            query_answer=QueryAnswerType.EXTRACTIVE,
            top=6,
            select=["id", "source", "locations", "keyphrases"],
        )

        answers = results.get_answers() #retrieve AI-generated answers from the semantic search results
        if answers:
            print("  [AI Answer]")
            for a in answers:
                print(f"    {a.text}")
            print()

        for doc in results:
            bm25   = doc.get("@search.score", 0) #keyword search score, there is no scale for this
            rerank = doc.get("@search.reranker_score", 0) #rerank score is semantic search score, scale 0 - 4, the higher the score the more relevant the document is conceptually
            captions = doc.get("@search.captions", [])
            caption  = captions[0].text if captions else "(no caption)"
            print(f"  [rerank:{rerank:.2f} / bm25:{bm25:.2f}]  {doc_name(doc)}")
            print(f"    -> {caption.strip()}")
            print()

    except Exception as exc:
        print(f"  Semantic search unavailable (requires Basic tier): {exc}")
        print()
        print("  Falling back to standard full-text for the same query:")
        results = client.search(
            search_text="famous landmarks and tourist attractions",
            top=6,
            select=["id", "source", "locations", "keyphrases"],
        )
        for doc in results:
            score = doc.get("@search.score", 0)
            print(f"  [{score:.2f}]  {doc_name(doc)}")
            print(f"    Locations : {', '.join(doc.get('locations', [])[:3])}")
            print()
        print("  Notice: BM25 ranks by keyword frequency — semantic ranking")
        print("  would re-score by conceptual relevance instead.")


# -- Query 3: Faceted aggregation to count the no. of occurences of each keyword/term across all documents------------------------
def demo_facets(client: SearchClient):
    print(f"\n{SEP}")
    print("  Query 3 — Facets: how many documents mention each location?")
    print("  Mode: Aggregation ($facet) — counts per unique value")
    print(SEP)
    results = client.search(
        search_text="*",#search for all documents
        facets=["locations,count:15"],#this specifies that we want to get the top 15 locations and their counts across all documents
        top=0,#we don't need actual documents, only facet counts
    )
    facets = results.get_facets() or {}
    buckets = facets.get("locations", []) #get the list of location buckets, each containing a location value and its count

    if buckets:
        for bucket in buckets:
            bar = "#" * int(bucket["count"])
            print(f"    {bucket['value']:30s}  {bar}  ({bucket['count']})")
    else:
        print("  No facet data returned.")

    print()
    print("  Key concept: facets let you build 'filter by location' UIs")
    print("  without writing any extra queries.")


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 62)
    print("  Advanced Search Queries")
    print("  Azure AI Search — Cognitive Fields / Semantic / Facets")
    print("=" * 62)
    print()

    client = get_client()

    demo_field_scoped(client)
    demo_semantic(client)
    demo_facets(client)

    print(f"\n{'=' * 62}")
    print("  Summary of query modes demonstrated:")
    print()
    print("  Mode             | Best for")
    print("  -----------------+--------------------------------------")
    print("  Field-scoped     | Target specific enriched fields")
    print("  Semantic         | Natural language, meaning-based rank")
    print("  Facets           | Aggregation counts, filter UIs")
    print()


if __name__ == "__main__":
    main()
