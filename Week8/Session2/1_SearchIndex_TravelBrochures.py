from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# -------------------------------------------------------
# Demo 1: Knowledge Mining — Margie's Travel Brochures
#
# This script queries an Azure AI Search index that was built
# by an indexer pipeline in the Azure portal. The pipeline:
# we are setting up indexes manually in this example
#   1. Reads PDFs from the documents/ folder (uploaded to
#      Azure Blob Storage as the data source) #not uploaded to blob in this example
#   2. Runs cognitive skills to extract: #using langauge services endpoint
#         - locations   (Named Entity Recognition)
#         - people      (Named Entity Recognition)
#         - keyphrases  (Key Phrase Extraction)
#   3. Stores the enriched data in the search index 
#
# This script is the front-end — it lets you search across
# all that extracted content with a simple text query.
#
# Prerequisites (run once before using this script):
#   1. Run setup_search_index.py to create and populate the index
#      (reads PDFs from documents/, runs NER + key phrase extraction,
#      then pushes enriched documents to Azure AI Search) #doing enrichment at local side and then pushing to azure ai search when then takes care of chunking,embedding
#   2. Set SEARCH_ENDPOINT, QUERY_KEY, and INDEX_NAME in .env
#
# Usage:
#   python 1_SearchIndex_TravelBrochures.py
# -------------------------------------------------------


def main():

    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    try:

        # Get config settings
        load_dotenv()
        search_endpoint = os.getenv('SEARCH_ENDPOINT')
        query_key = os.getenv('QUERY_KEY')
        index = os.getenv('INDEX_NAME')

        # Get a search client
        search_client = SearchClient(search_endpoint, index, AzureKeyCredential(query_key))

        # Loop until the user types 'quit'
        while True:
            # Get query text
            query_text = input("Enter a query (or type 'quit' to exit): ")
            if query_text.lower() == "quit":
                break
            if len(query_text) == 0:
                print("Please enter a query.")
                continue

            # Clear the console
            os.system('cls' if os.name == 'nt' else 'clear')

            # Search the index
            found_documents = search_client.search(
                search_text=query_text,
                #return only these fields from the matching documents, also helps reduce payload size and improve performance
                select=["id", "source", "locations", "people", "keyphrases"],
                include_total_count=True #includes the total count of matching documents in the response
            )

            # Parse the results
            print(f"\nSearch returned {found_documents.get_count()} documents:")
            for document in found_documents:
                doc_name = document.get("source") or document["id"]
                print(f"\nDocument: {doc_name}")
                print(" - Locations:")
                for location in document["locations"]:
                    print(f"   - {location}")
                print(" - People:")
                for person in document["people"]:
                    print(f"   - {person}")
                print(" - Key phrases:")
                for phrase in document["keyphrases"]:
                    print(f"   - {phrase}")

    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    main()
