import os
import json
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import ClientSecretCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
import streamlit as st
import logging

class AzureSearchManager:
    def __init__(self, search_endpoint=None, index_name=None, api_key=None):
        """
        Initialize Azure Search Manager

        Args:
            search_endpoint: Azure Search endpoint URL
            index_name: Name of the search index
            api_key: API key for authentication (optional, will use Azure AD if not provided)
        """
        # Configuration
        self.search_endpoint = search_endpoint or "https://search-ne-rnd-dev-01-dev-ds-1a-genie.search.windows.net"
        self.index_name = index_name or "specification-mappings"

        # Azure AD Authentication - Use environment variables
        self.tenant_id = os.environ.get('AZURE_TENANT_ID', '')
        self.client_id = os.environ.get('AZURE_CLIENT_ID', '')
        self.client_secret = os.environ.get('AZURE_CLIENT_SECRET', '')

        # Initialize clients
        self.credential = None
        self.search_client = None
        self.index_client = None

        # Set up authentication
        if api_key:
            self.credential = AzureKeyCredential(api_key)
        else:
            try:
                self.credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            except Exception as e:
                st.error(f"Failed to initialize Azure credentials: {e}")
                return

        try:
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.index_name,
                credential=self.credential
            )

            self.index_client = SearchIndexClient(
                endpoint=self.search_endpoint,
                credential=self.credential
            )

        except Exception as e:
            st.error(f"Failed to initialize Azure Search clients: {e}")

    def search_specifications(self, query, top=10, filters=None):
        """
        Search for specifications in Azure Search

        Args:
            query: Search query string
            top: Number of results to return
            filters: Optional OData filter string

        Returns:
            List of search results
        """
        if not self.search_client:
            st.error("Azure Search client not initialized")
            return []

        try:
            search_results = self.search_client.search(
                search_text=query,
                top=top,
                filter=filters,
                include_total_count=True
            )

            results = []
            for result in search_results:
                results.append(result)

            return results

        except Exception as e:
            st.error(f"Search failed: {e}")
            return []

    def get_document_by_id(self, document_id):
        """
        Retrieve a specific document by ID

        Args:
            document_id: The document ID to retrieve

        Returns:
            Document data or None if not found
        """
        if not self.search_client:
            st.error("Azure Search client not initialized")
            return None

        try:
            result = self.search_client.get_document(key=document_id)
            return result
        except Exception as e:
            st.error(f"Failed to retrieve document {document_id}: {e}")
            return None

    def search_by_airline(self, airline_name, top=10):
        """
        Search for specifications by airline name

        Args:
            airline_name: Name of the airline
            top: Number of results to return

        Returns:
            List of search results
        """
        filter_query = f"airline eq '{airline_name}'"
        return self.search_specifications("*", top=top, filters=filter_query)

    def search_by_message_type(self, message_type, top=10):
        """
        Search for specifications by message type

        Args:
            message_type: Type of message (e.g., 'PNR', 'EMD', etc.)
            top: Number of results to return

        Returns:
            List of search results
        """
        filter_query = f"messageType eq '{message_type}'"
        return self.search_specifications("*", top=top, filters=filter_query)

    def get_index_statistics(self):
        """
        Get statistics about the search index

        Returns:
            Dictionary with index statistics
        """
        if not self.index_client:
            st.error("Azure Search index client not initialized")
            return {}

        try:
            index = self.index_client.get_index(self.index_name)
            stats = self.index_client.get_service_statistics()

            return {
                'index_name': index.name,
                'field_count': len(index.fields),
                'document_count': stats.counters.document_count,
                'storage_size': stats.counters.storage_size,
                'index_size': stats.counters.index_size
            }
        except Exception as e:
            st.error(f"Failed to get index statistics: {e}")
            return {}

    def suggest(self, query, suggester_name="sg", top=5):
        """
        Get search suggestions

        Args:
            query: Partial query for suggestions
            suggester_name: Name of the suggester to use
            top: Number of suggestions to return

        Returns:
            List of suggestions
        """
        if not self.search_client:
            st.error("Azure Search client not initialized")
            return []

        try:
            suggestions = self.search_client.suggest(
                search_text=query,
                suggester_name=suggester_name,
                top=top
            )

            return [suggestion['text'] for suggestion in suggestions]
        except Exception as e:
            st.error(f"Suggestion failed: {e}")
            return []

    def test_connection(self):
        """
        Test the connection to Azure Search

        Returns:
            Boolean indicating if connection is successful
        """
        try:
            # Try to get a single document to test connection
            results = self.search_specifications("*", top=1)
            return True
        except Exception as e:
            st.error(f"Connection test failed: {e}")
            return False