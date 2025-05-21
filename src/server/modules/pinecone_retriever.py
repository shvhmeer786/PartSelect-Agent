#!/usr/bin/env python3
"""
PineconeRetriever: Vector database retrieval for Installation Guides and Diagnostic Information
This module provides a unified interface for retrieving relevant documents from Pinecone for RAG.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from pinecone import Pinecone, Index, ServerlessSpec, PodSpec
from langchain_core.embeddings import Embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeRetriever:
    """
    Retriever for installation guides and diagnostic information using Pinecone vector database.
    Handles document retrieval for RAG-based applications.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: str = "us-west1-gcp",
        index_name: str = "partselect",
        embeddings_model: Optional[Embeddings] = None,
        namespace: str = "default"
    ):
        """
        Initialize the Pinecone retriever.
        
        Args:
            api_key: Pinecone API key (defaults to PINECONE_API_KEY env var)
            environment: Pinecone environment
            index_name: Name of the Pinecone index
            embeddings_model: LangChain-compatible embeddings model
            namespace: Namespace within the Pinecone index
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = index_name
        self.environment = environment
        self.embeddings_model = embeddings_model
        self.namespace = namespace
        self.vector_store = None
        
        if not self.api_key:
            logger.warning("No Pinecone API key provided. Using mock data instead.")
            self.use_mock = True
        else:
            self.use_mock = False
            try:
                # Initialize Pinecone client
                self._init_pinecone()
            except Exception as e:
                logger.error(f"Error initializing Pinecone: {e}")
                self.use_mock = True
                
        logger.info(f"PineconeRetriever initialized: {'using mock data' if self.use_mock else 'connected to Pinecone'}")
    
    def _init_pinecone(self):
        """Initialize Pinecone client and vector store."""
        try:
            # Initialize Pinecone
            pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            existing_indexes = [index.name for index in pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                # Create index with dimensions appropriate for the embedding model
                dimensions = 1536  # Default for OpenAI embeddings
                pc.create_index(
                    name=self.index_name,
                    dimension=dimensions,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-west-2")
                )
            
            # Connect to the index
            self.index = pc.Index(self.index_name)
            
            # Set up the vector store if embedding model is provided
            if self.embeddings_model:
                self.vector_store = PineconeVectorStore(
                    index_name=self.index_name,
                    embedding=self.embeddings_model,
                    namespace=self.namespace
                )
                logger.info(f"Connected to Pinecone vector store: {self.index_name}")
            else:
                logger.warning("No embeddings model provided, vector store functionality is limited")
                
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            self.use_mock = True
            raise
    
    async def retrieve(
        self, 
        query: str, 
        doc_type: str = None, 
        appliance_type: str = None,
        top_k: int = 3,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Retrieve relevant documents from Pinecone.
        
        Args:
            query: User query to search for
            doc_type: Type of document to retrieve (installation, troubleshooting)
            appliance_type: Type of appliance (refrigerator, dishwasher)
            top_k: Number of documents to retrieve
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of relevant documents with metadata
        """
        if self.use_mock:
            return self._get_mock_docs(query, doc_type, appliance_type, top_k)
        
        try:
            if not self.embeddings_model:
                logger.warning("No embeddings model provided, using fallback retrieval")
                return self._fallback_retrieval(query, doc_type, appliance_type, top_k)
            
            # Embed the query
            query_embedding = self.embeddings_model.embed_query(query)
            
            # Build the filter for metadata
            filter_dict = {}
            if doc_type:
                filter_dict["doc_type"] = doc_type
            if appliance_type:
                filter_dict["appliance_type"] = appliance_type
            
            # Perform vector search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                namespace=self.namespace,
                include_metadata=True
            )
            
            # Process and return results
            documents = []
            for match in results.matches:
                if match.score >= score_threshold:
                    doc = {
                        "id": match.id,
                        "score": match.score,
                        **match.metadata
                    }
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving from Pinecone: {e}")
            return self._get_mock_docs(query, doc_type, appliance_type, top_k)
    
    def _fallback_retrieval(
        self, 
        query: str, 
        doc_type: str = None, 
        appliance_type: str = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Fallback metadata-based retrieval when embedding model isn't available.
        
        Args:
            query: Search query
            doc_type: Document type filter
            appliance_type: Appliance type filter
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        # Build the filter
        filter_dict = {}
        if doc_type:
            filter_dict["doc_type"] = doc_type
        if appliance_type:
            filter_dict["appliance_type"] = appliance_type
        
        try:
            # Use metadata filtering only
            response = self.index.query(
                vector=[0.0] * 1536,  # Dummy vector
                top_k=1000,  # Get more results since we'll post-filter
                filter=filter_dict if filter_dict else None,
                namespace=self.namespace,
                include_metadata=True
            )
            
            # Perform basic keyword matching
            results = []
            for match in response.matches:
                # Check if query terms are in the document text
                text = match.metadata.get("text", "")
                title = match.metadata.get("title", "")
                
                if any(term.lower() in (text + title).lower() for term in query.split()):
                    results.append({
                        "id": match.id,
                        "score": 0.5,  # Arbitrary score since not using embeddings
                        **match.metadata
                    })
                    
                    if len(results) >= top_k:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback retrieval error: {e}")
            return self._get_mock_docs(query, doc_type, appliance_type, top_k)
    
    def _get_mock_docs(
        self, 
        query: str, 
        doc_type: str = None, 
        appliance_type: str = None,
        limit: int = 3
    ) -> List[Dict]:
        """
        Provide mock documents when Pinecone is not available.
        
        Args:
            query: Search query
            doc_type: Document type filter
            appliance_type: Appliance type filter
            limit: Number of documents to return
            
        Returns:
            List of mock documents
        """
        query_lower = query.lower()
        
        # Mock installation guides
        if doc_type == "installation" or "install" in query_lower or "how to" in query_lower:
            if "water filter" in query_lower or "filter" in query_lower:
                return [{
                    "id": "doc1",
                    "title": "Water Filter Installation",
                    "doc_type": "installation",
                    "appliance_type": "refrigerator",
                    "score": 0.95,
                    "content": {
                        "raw_text": "# Installation Guide for Water Filter\n\n## Step-by-Step Instructions:\n1. Turn off the water supply\n2. Remove the old filter by turning counterclockwise\n3. Insert the new filter and turn clockwise until it locks\n4. Run water for 5 minutes to clear the system",
                        "steps": [
                            "Turn off the water supply",
                            "Remove the old filter by turning counterclockwise",
                            "Insert the new filter and turn clockwise until it locks",
                            "Run water for 5 minutes to clear the system"
                        ]
                    }
                }]
            elif "ice maker" in query_lower:
                return [{
                    "id": "doc2",
                    "title": "Ice Maker Installation",
                    "doc_type": "installation",
                    "appliance_type": "refrigerator",
                    "score": 0.92,
                    "content": {
                        "raw_text": "# Installation Guide for Ice Maker\n\n## Step-by-Step Instructions:\n1. Disconnect power to the refrigerator\n2. Remove the freezer shelves for access\n3. Disconnect the wiring harness\n4. Remove mounting screws and old ice maker\n5. Install new ice maker and reattach mounting screws\n6. Connect wiring harness\n7. Restore power and test operation",
                        "steps": [
                            "Disconnect power to the refrigerator",
                            "Remove the freezer shelves for access",
                            "Disconnect the wiring harness",
                            "Remove mounting screws and old ice maker",
                            "Install new ice maker and reattach mounting screws",
                            "Connect wiring harness",
                            "Restore power and test operation"
                        ]
                    }
                }]
            else:
                return [{
                    "id": "doc3",
                    "title": "Control Board Installation",
                    "doc_type": "installation",
                    "appliance_type": "dishwasher",
                    "score": 0.85,
                    "content": {
                        "raw_text": "# Installation Guide for Dishwasher Control Board\n\n## Step-by-Step Instructions:\n1. Disconnect power\n2. Remove the outer door panel\n3. Locate the control board at the top of the door\n4. Disconnect all wire harnesses (take a photo first)\n5. Remove mounting screws\n6. Install new board and reconnect wires\n7. Reinstall door and test",
                        "steps": [
                            "Disconnect power",
                            "Remove the outer door panel",
                            "Locate the control board at the top of the door",
                            "Disconnect all wire harnesses (take a photo first)",
                            "Remove mounting screws",
                            "Install new board and reconnect wires",
                            "Reinstall door and test"
                        ]
                    }
                }]
        
        # Mock troubleshooting documents
        elif doc_type == "troubleshooting" or "not working" in query_lower or "problem" in query_lower or "fix" in query_lower:
            if "ice" in query_lower or "ice maker" in query_lower:
                return [{
                    "id": "doc4",
                    "title": "Ice Maker Troubleshooting",
                    "doc_type": "troubleshooting",
                    "appliance_type": "refrigerator",
                    "score": 0.93,
                    "content": {
                        "raw_text": "# Ice Maker Troubleshooting\n\nCommon problems and solutions for ice makers not producing ice:\n\n1. Water supply issue - check if water line is frozen, kinked, or not connected properly\n2. Water filter needs replacement - replace if older than 6 months\n3. Ice maker assembly failure - may need replacement if mechanically damaged\n4. Control board issue - check for error codes on refrigerator display",
                        "symptoms": {
                            "Ice maker not producing ice": "Check water supply, filter, and ice maker assembly",
                            "Ice maker makes noise but no ice": "Likely a water supply issue or frozen water line",
                            "Small or hollow ice cubes": "Low water pressure or partial blockage in water line"
                        },
                        "parts": [
                            {"name": "Ice Maker Assembly", "part_number": "DA97-07365G", "price": 129.99},
                            {"name": "Water Filter", "part_number": "DA29-00020B", "price": 49.99},
                            {"name": "Water Inlet Valve", "part_number": "DD62-00067A", "price": 39.99}
                        ]
                    }
                }]
            elif "drain" in query_lower or "draining" in query_lower:
                return [{
                    "id": "doc5",
                    "title": "Dishwasher Draining Problems",
                    "doc_type": "troubleshooting",
                    "appliance_type": "dishwasher",
                    "score": 0.91,
                    "content": {
                        "raw_text": "# Dishwasher Not Draining\n\nCommon causes and solutions for dishwashers not draining properly:\n\n1. Clogged drain filter - remove and clean the filter at the bottom of the dishwasher\n2. Drain pump failure - check for obstructions or replace if motor is non-functional\n3. Drain hose kinked or blocked - inspect and straighten or clear\n4. Check valve clogged - clean or replace the check valve",
                        "symptoms": {
                            "Water remains in bottom after cycle": "Clogged filter or drain pump issue",
                            "Dishwasher backs up into sink": "Drain hose or air gap blockage",
                            "Dishwasher stops mid-cycle": "Possible drain pump failure or control board issue"
                        },
                        "parts": [
                            {"name": "Dishwasher Drain Pump", "part_number": "WPW10348269", "price": 86.49},
                            {"name": "Dishwasher Check Valve", "part_number": "W10195677", "price": 15.99},
                            {"name": "Drain Hose Kit", "part_number": "W10221546", "price": 25.99}
                        ]
                    }
                }]
            else:
                return [{
                    "id": "doc6",
                    "title": "Refrigerator Cooling Problems",
                    "doc_type": "troubleshooting",
                    "appliance_type": "refrigerator",
                    "score": 0.87,
                    "content": {
                        "raw_text": "# Refrigerator Not Cooling\n\nCommon causes and solutions for refrigerators not cooling properly:\n\n1. Dirty condenser coils - clean coils located under or behind refrigerator\n2. Faulty evaporator fan - listen for unusual noise, replace if necessary\n3. Defrost system failure - check for frost buildup on evaporator coils\n4. Compressor problems - if compressor isn't running, may need professional service",
                        "symptoms": {
                            "Refrigerator and freezer not cold": "Possible compressor issue or sealed system problem",
                            "Refrigerator warm but freezer cold": "Likely evaporator fan or damper control issue",
                            "Frost buildup in freezer": "Defrost system failure"
                        },
                        "parts": [
                            {"name": "Evaporator Fan Motor", "part_number": "DA31-00146E", "price": 75.99},
                            {"name": "Defrost Heater", "part_number": "DA47-00244U", "price": 45.99},
                            {"name": "Temperature Control Board", "part_number": "DA41-00669A", "price": 159.99}
                        ]
                    }
                }]
                
        # Default fallback document
        else:
            return [{
                "id": "doc7",
                "title": "General Appliance Maintenance",
                "doc_type": "general",
                "appliance_type": "all",
                "score": 0.75,
                "content": {
                    "raw_text": "# General Appliance Maintenance\n\nRegular maintenance tips for appliances:\n\n1. Clean refrigerator condenser coils every 6-12 months\n2. Replace water filters every 6 months\n3. Clean dishwasher filter monthly\n4. Check and tighten any loose connections\n5. Inspect seals and gaskets for damage\n6. Keep appliance vents and airways clear",
                    "maintenance_schedule": {
                        "monthly": ["Clean dishwasher filter", "Clean refrigerator drip tray"],
                        "quarterly": ["Check door seals", "Clean refrigerator interior"],
                        "bi-annually": ["Replace water filter", "Clean condenser coils"]
                    }
                }
            }]
            
    async def retrieve_and_format_for_llm(
        self, 
        query: str, 
        doc_type: str = None, 
        appliance_type: str = None,
        top_k: int = 3
    ) -> str:
        """
        Retrieve documents and format them for use in an LLM prompt.
        
        Args:
            query: User query
            doc_type: Document type filter
            appliance_type: Appliance type filter
            top_k: Number of documents to retrieve
            
        Returns:
            Formatted context string for LLM input
        """
        docs = await self.retrieve(query, doc_type, appliance_type, top_k)
        
        if not docs:
            return "No relevant documentation found. Please provide an answer based on general knowledge."
        
        # Format the documents into a context string
        context = "### RELEVANT DOCUMENTATION ###\n\n"
        
        for i, doc in enumerate(docs):
            context += f"DOCUMENT {i+1}: {doc.get('title', 'Untitled Document')}\n"
            score = doc.get('score', 0)
            context += f"Relevance Score: {score:.2f}\n"
            content = doc.get('content', {})
            
            # Extract text content
            raw_text = content.get('raw_text', '')
            if raw_text:
                context += f"Content: {raw_text}\n\n"
            
            # Extract steps if available
            steps = content.get('steps', [])
            if steps and len(steps) > 0:
                context += "Steps:\n"
                for j, step in enumerate(steps):
                    context += f"  {j+1}. {step}\n"
                context += "\n"
                
            # Extract symptoms if available (for troubleshooting)
            symptoms = content.get('symptoms', {})
            if symptoms:
                context += "Symptoms and Solutions:\n"
                for symptom, solution in symptoms.items():
                    context += f"  - {symptom}: {solution}\n"
                context += "\n"
                
            # Extract parts if available
            parts = content.get('parts', [])
            if parts and len(parts) > 0:
                context += "Recommended Parts:\n"
                for part in parts:
                    part_name = part.get('name', 'Unknown Part')
                    part_number = part.get('part_number', 'N/A')
                    price = part.get('price', 'N/A')
                    context += f"  - {part_name} (Part #{part_number}, Price: ${price})\n"
                context += "\n"
                
            context += "---\n"
        
        return context 