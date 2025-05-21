import requests
from bs4 import BeautifulSoup
import time
import re
import uuid
import urllib.parse
import random
from typing import Dict, List, Optional, Union, Set, Any, Callable, Type, Literal, ClassVar
from pymongo import MongoClient
from pymongo.collection import Collection
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
import asyncio
import aiohttp
import os
import json
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from .mock_data import MockDataProvider
from .validators import IntentType
import redis
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the LangChain Tool Wrappers
class ProductLookupTool(BaseTool):
    """
    Tool for looking up product details by part number.
    Uses CatalogClient to retrieve part information.
    """
    name: ClassVar[str] = "product_lookup_tool"
    description: ClassVar[str] = "Look up detailed information about a specific part by its part number"
    
    def __init__(self, catalog_client=None, **kwargs):
        """
        Initialize the product lookup tool with a catalog client.
        
        Args:
            catalog_client: An instance of CatalogClient or AsyncCatalogClient
        """
        super().__init__(**kwargs)
        self.catalog_client = catalog_client
    
    async def _run_async(
        self, part_number: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async implementation to look up part details.
        
        Args:
            part_number: The part number to look up
            run_manager: Callback manager for the tool run
            
        Returns:
            JSON string with part details or error message
        """
        try:
            # Get the part from the catalog client
            part = await self.catalog_client.get_part(part_number)
            
            if not part:
                return json.dumps({"error": f"Part {part_number} not found"})
            
            # Return the part details as JSON
            return json.dumps(part, indent=2)
            
        except Exception as e:
            logger.error(f"Error looking up part {part_number}: {e}")
            return json.dumps({"error": f"Error looking up part: {str(e)}"})
    
    def _run(
        self, part_number: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Run the tool to look up part details.
        
        Args:
            part_number: The part number to look up
            run_manager: Callback manager for the tool run
            
        Returns:
            JSON string with part details or error message
        """
        # For synchronous operation, we'll use asyncio to run the async method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._run_async(part_number, run_manager))
        return result

class CompatibilityTool(BaseTool):
    """
    Tool for checking compatibility between parts and models.
    Uses CatalogClient to determine if a part is compatible with a specific model.
    """
    name: ClassVar[str] = "compatibility_tool"
    description: ClassVar[str] = "Check if a part is compatible with a specific appliance model"
    
    def __init__(self, catalog_client=None, **kwargs):
        """
        Initialize the compatibility tool with a catalog client.
        
        Args:
            catalog_client: An instance of CatalogClient or AsyncCatalogClient
        """
        super().__init__(**kwargs)
        self.catalog_client = catalog_client
    
    async def _run_async(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async implementation to check compatibility.
        
        Args:
            query: The query string in format "part_number:model_number"
            run_manager: Callback manager for the tool run
            
        Returns:
            "Fits" if compatible, "Not Compatible" if not, or error message
        """
        try:
            # Parse the query
            parts = query.split(":")
            if len(parts) != 2:
                return "Invalid query format. Use 'part_number:model_number'"
            
            part_number, model_number = parts[0].strip(), parts[1].strip()
            
            # Check compatibility
            is_compatible = await self.catalog_client.check_compatibility(part_number, model_number)
            
            if is_compatible:
                # Get additional details for context
                part = await self.catalog_client.get_part(part_number)
                part_name = part.get("name", "Unknown Part") if part else "Unknown Part"
                
                return f"Fits: {part_name} (Part #{part_number}) is compatible with model {model_number}."
            else:
                return f"Not Compatible: Part #{part_number} is not compatible with model {model_number}."
            
        except Exception as e:
            logger.error(f"Error checking compatibility: {e}")
            return f"Error checking compatibility: {str(e)}"
    
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Run the tool to check compatibility.
        
        Args:
            query: The query string in format "part_number:model_number"
            run_manager: Callback manager for the tool run
            
        Returns:
            "Fits" if compatible, "Not Compatible" if not, or error message
        """
        # For synchronous operation, we'll use asyncio to run the async method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._run_async(query, run_manager))
        return result

class InstallationGuideTool(BaseTool):
    """
    Tool for retrieving installation guides for parts.
    Uses DocsClient to get installation documentation and can be extended with vector search.
    """
    name: ClassVar[str] = "installation_guide_tool"
    description: ClassVar[str] = "Get step-by-step installation instructions for a specific part"
    
    def __init__(self, docs_client=None, deepseek_api_key=None, pinecone_retriever=None, **kwargs):
        """
        Initialize the installation guide tool with a docs client.
        
        Args:
            docs_client: An instance of DocsClient or AsyncDocsClient
            deepseek_api_key: Optional API key for Deepseek LLM to enhance instructions
            pinecone_retriever: Optional PineconeRetriever for RAG implementation
        """
        super().__init__(**kwargs)
        self.docs_client = docs_client
        self.deepseek_api_key = deepseek_api_key
        self.pinecone_retriever = pinecone_retriever
    
    async def _run_async(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async implementation to get installation instructions.
        
        Args:
            query: The query string in format "part_name:appliance_type" (appliance_type is optional)
            run_manager: Callback manager for the tool run
            
        Returns:
            Numbered installation steps or error message
        """
        try:
            # Parse the query
            parts = query.split(":", 1)
            part_name = parts[0].strip()
            appliance_type = parts[1].strip() if len(parts) > 1 else None

            # If we have PineconeRetriever, use the RAG approach
            if self.pinecone_retriever:
                logger.info(f"Using PineconeRetriever for installation guide: {query}")
                return await self._run_rag_installation(query, part_name, appliance_type)
            
            # Otherwise fall back to the original implementation
            # First, try to get specific repair steps for the part
            repair_steps = await self.docs_client.get_repair_steps(part_name, appliance_type)
            
            if repair_steps and len(repair_steps) > 0:
                # Format the steps with numbers
                numbered_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(repair_steps)])
                
                # Get safety notes
                safety_notes = await self.docs_client.get_safety_notes(appliance_type)
                safety_section = ""
                if safety_notes and len(safety_notes) > 0:
                    safety_section = "\n\n⚠️ SAFETY PRECAUTIONS:\n" + "\n".join([f"• {note}" for note in safety_notes])
                
                return f"# Installation Guide for {part_name}\n\n## Step-by-Step Instructions:\n{numbered_steps}{safety_section}"
            
            # If no specific steps, get general installation docs
            docs = await self.docs_client.get_installation_docs(part_name=part_name, appliance_type=appliance_type, limit=2)
            
            if not docs or len(docs) == 0:
                return f"No installation instructions found for {part_name}."
            
            # Compile information from the docs
            installation_info = "# Installation Guide\n\n"
            
            for doc in docs:
                installation_info += f"## {doc.get('title', 'Installation Guide')}\n\n"
                
                # Extract steps from content
                content = doc.get("content", {})
                steps = content.get("steps", [])
                
                if steps and len(steps) > 0:
                    installation_info += "### Steps:\n"
                    installation_info += "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                    installation_info += "\n\n"
                else:
                    # Fallback to raw text if structured steps aren't available
                    raw_text = content.get("raw_text", "")
                    if raw_text:
                        installation_info += f"{raw_text}\n\n"
            
            # Get safety notes
            safety_notes = await self.docs_client.get_safety_notes(appliance_type)
            if safety_notes and len(safety_notes) > 0:
                installation_info += "## ⚠️ Safety Precautions:\n"
                installation_info += "\n".join([f"• {note}" for note in safety_notes])
            
            return installation_info
            
        except Exception as e:
            logger.error(f"Error getting installation guide: {e}")
            return f"Error retrieving installation guide: {str(e)}"
    
    async def _run_rag_installation(self, query: str, part_name: str, appliance_type: str = None) -> str:
        """
        Use the RAG approach with Pinecone and Deepseek LLM to generate installation instructions.
        
        Args:
            query: Original user query
            part_name: The part name extracted from the query
            appliance_type: Optional appliance type
            
        Returns:
            Detailed installation instructions
        """
        try:
            # Get relevant documents from Pinecone using the query
            context = await self.pinecone_retriever.retrieve_and_format_for_llm(
                query, 
                doc_type="installation", 
                appliance_type=appliance_type,
                top_k=3
            )
            
            # If no Deepseek API key, just return the formatted docs
            if not self.deepseek_api_key:
                # Extract and format the most relevant document
                return self._format_raw_context_to_guide(context, part_name)
            
            # Create a prompt for the LLM to generate installation steps
            prompt = self._create_installation_prompt(query, context, part_name, appliance_type)
            
            # Call the DeepSeek API
            response = await self._call_deepseek_api(prompt)
            
            if not response:
                # Fall back to formatting the raw context
                return self._format_raw_context_to_guide(context, part_name)
                
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG installation: {e}")
            return f"I apologize, but I encountered an error retrieving the installation instructions for {part_name}. Please try asking in a different way."
    
    async def _call_deepseek_api(self, prompt: str) -> str:
        """
        Call the DeepSeek API to generate a response based on the RAG prompt.
        
        Args:
            prompt: The prompt containing context and query
            
        Returns:
            LLM-generated response
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,  # Lower temperature for factual responses
                "max_tokens": 1000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.deepseek.com/v1/chat/completions", 
                                        headers=headers, 
                                        json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        generated_text = result["choices"][0]["message"]["content"]
                        return generated_text
                    else:
                        error_text = await response.text()
                        logger.error(f"Error from DeepSeek API: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {e}")
            return None
    
    def _create_installation_prompt(self, query: str, context: str, part_name: str, appliance_type: str = None) -> str:
        """
        Create a prompt for the DeepSeek LLM to generate installation instructions.
        
        Args:
            query: Original user query
            context: Retrieved document context
            part_name: Name of the part
            appliance_type: Type of appliance
            
        Returns:
            Formatted prompt string
        """
        appliance_type_str = f" for a {appliance_type}" if appliance_type else ""
        
        return f"""You are an expert appliance repair technician. I need you to provide detailed installation instructions for a {part_name}{appliance_type_str}. 

Use the following reference documentation to create a comprehensive installation guide:

{context}

Based on this information, please provide a clear, step-by-step installation guide for the {part_name}. Include:

1. Any required tools or materials
2. Safety precautions that should be taken
3. Detailed, numbered steps for installation
4. Any tips for testing the installation

Format the response as a proper installation guide with headings and clearly numbered steps. If the documentation doesn't provide complete information, use your expertise to fill in reasonable details, but make sure they're consistent with typical installation procedures for this type of part.
"""
    
    def _format_raw_context_to_guide(self, context: str, part_name: str) -> str:
        """
        Format the raw context into an installation guide when LLM is unavailable.
        
        Args:
            context: The raw document context
            part_name: The part name for the title
            
        Returns:
            Formatted installation guide
        """
        if not context or "No relevant documentation found" in context:
            return f"I'm sorry, but I don't have specific installation instructions for {part_name}."
        
        # Extract steps from the context
        steps = []
        in_steps_section = False
        for line in context.split("\n"):
            if line.startswith("Steps:"):
                in_steps_section = True
                continue
            elif in_steps_section and line.strip() and not line.startswith("---"):
                # Check if line looks like a step (starts with a number and period)
                if re.match(r"\s*\d+\.", line):
                    steps.append(line.strip())
            elif in_steps_section and (not line.strip() or line.startswith("---")):
                in_steps_section = False
        
        # If no steps found, try to extract from raw_text
        if not steps:
            raw_text_matches = re.findall(r"Content: (.*?)(?:\n\n|$)", context, re.DOTALL)
            if raw_text_matches:
                raw_text = raw_text_matches[0]
                # Try to find numbered steps in the raw text
                step_matches = re.findall(r"\d+\.\s*(.*?)(?=\d+\.|$)", raw_text, re.DOTALL)
                if step_matches:
                    steps = [step.strip() for step in step_matches]
        
        # Format the guide
        installation_guide = f"# Installation Guide for {part_name}\n\n"
        
        # Extract any safety precautions
        safety_notes = []
        if "⚠️" in context or "SAFETY" in context.upper() or "CAUTION" in context.upper():
            safety_section = re.search(r"(?:⚠️|SAFETY|PRECAUTION).*?(?=---|\Z)", context, re.IGNORECASE | re.DOTALL)
            if safety_section:
                safety_text = safety_section.group(0)
                safety_notes = re.findall(r"[•-]\s*(.*?)(?=\n|$)", safety_text)
        
        if safety_notes:
            installation_guide += "## ⚠️ SAFETY PRECAUTIONS:\n"
            for note in safety_notes:
                installation_guide += f"• {note}\n"
            installation_guide += "\n"
        
        # Add the steps
        installation_guide += "## Step-by-Step Instructions:\n"
        if steps:
            for i, step in enumerate(steps, 1):
                # Remove any existing numbers at the beginning of the step
                step_text = re.sub(r"^\s*\d+\.\s*", "", step)
                installation_guide += f"{i}. {step_text}\n"
        else:
            # If no structured steps could be extracted, include the raw text
            raw_text_matches = re.findall(r"Content: (.*?)(?:\n\n|---)", context, re.DOTALL)
            if raw_text_matches:
                installation_guide += raw_text_matches[0].strip() + "\n"
            else:
                installation_guide += "No specific step-by-step instructions available for this part.\n"
                installation_guide += "Please consult the appliance manual or contact customer support for detailed installation help.\n"
        
        return installation_guide
    
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Run the tool to get installation instructions.
        
        Args:
            query: The query string in format "part_name:appliance_type" (appliance_type is optional)
            run_manager: Callback manager for the tool run
            
        Returns:
            Numbered installation steps or error message
        """
        # For synchronous operation, we'll use asyncio to run the async method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._run_async(query, run_manager))
        return result

class ErrorDiagnosisTool(BaseTool):
    """
    Tool for diagnosing appliance problems and suggesting likely parts that need replacement.
    Uses DocsClient to get troubleshooting documentation and can be extended with vector search.
    """
    name: ClassVar[str] = "error_diagnosis_tool"
    description: ClassVar[str] = "Diagnose appliance problems and suggest likely parts that need replacement"
    
    def __init__(self, docs_client=None, catalog_client=None, deepseek_api_key=None, pinecone_retriever=None, **kwargs):
        """
        Initialize the error diagnosis tool with docs and catalog clients.
        
        Args:
            docs_client: An instance of DocsClient or AsyncDocsClient
            catalog_client: An instance of CatalogClient or AsyncCatalogClient
            deepseek_api_key: Optional API key for Deepseek LLM to enhance diagnosis
            pinecone_retriever: Optional PineconeRetriever for RAG implementation
        """
        super().__init__(**kwargs)
        self.docs_client = docs_client
        self.catalog_client = catalog_client
        self.deepseek_api_key = deepseek_api_key
        self.pinecone_retriever = pinecone_retriever
    
    async def _run_async(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async implementation to diagnose problems and suggest parts.
        
        Args:
            query: The query string in format "problem:appliance_type" (appliance_type is optional)
            run_manager: Callback manager for the tool run
            
        Returns:
            Diagnosis with possible causes and suggested parts to check/replace
        """
        try:
            # Parse the query
            parts = query.split(":", 1)
            problem = parts[0].strip()
            appliance_type = parts[1].strip() if len(parts) > 1 else None

            # If we have PineconeRetriever, use the RAG approach
            if self.pinecone_retriever:
                logger.info(f"Using PineconeRetriever for error diagnosis: {query}")
                return await self._run_rag_diagnosis(query, problem, appliance_type)
            
            # Otherwise fall back to the original implementation
            # Get troubleshooting docs for the problem
            docs = await self.docs_client.get_troubleshooting_docs(problem=problem, appliance_type=appliance_type, limit=3)
            
            if not docs or len(docs) == 0:
                return f"No troubleshooting information found for '{problem}'."
            
            # Compile diagnosis information
            diagnosis = f"# Diagnosis for: {problem}\n\n"
            likely_parts = set()
            
            for doc in docs:
                diagnosis += f"## {doc.get('title', 'Troubleshooting Guide')}\n\n"
                
                # Extract information from content
                content = doc.get("content", {})
                
                # Extract symptoms and solutions
                symptoms = content.get("symptoms", {})
                if symptoms:
                    for symptom, solution in symptoms.items():
                        diagnosis += f"### Symptom: {symptom}\n"
                        diagnosis += f"Solution: {solution}\n\n"
                        
                        # Extract likely parts from the solution text
                        parts_mentioned = self._extract_parts_from_text(solution)
                        likely_parts.update(parts_mentioned)
                
                # If no structured symptoms, use raw text
                raw_text = content.get("raw_text", "")
                if raw_text and not symptoms:
                    diagnosis += f"{raw_text}\n\n"
                    
                    # Extract likely parts from the raw text
                    parts_mentioned = self._extract_parts_from_text(raw_text)
                    likely_parts.update(parts_mentioned)
            
            # Add suggestions for likely parts to check/replace
            if likely_parts:
                diagnosis += "## Likely Parts to Check/Replace:\n"
                
                # Try to get more info about each part from the catalog
                for part_name in likely_parts:
                    # Search for the part
                    parts_info = await self.catalog_client.search_parts(part_name, appliance_type, limit=1)
                    
                    if parts_info and len(parts_info) > 0:
                        part = parts_info[0]
                        part_number = part.get("partNumber", "Unknown")
                        price = part.get("price", "Unknown")
                        
                        diagnosis += f"• {part_name} (Part #{part_number}, Price: ${price})\n"
                    else:
                        diagnosis += f"• {part_name}\n"
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error diagnosing problem: {e}")
            return f"Error diagnosing problem: {str(e)}"
    
    async def _run_rag_diagnosis(self, query: str, problem: str, appliance_type: str = None) -> str:
        """
        Use the RAG approach with Pinecone and Deepseek LLM to diagnose the problem.
        
        Args:
            query: Original user query
            problem: The problem description extracted from the query
            appliance_type: Optional appliance type
            
        Returns:
            Detailed diagnosis and part recommendations
        """
        try:
            # Get relevant documents from Pinecone using the query
            context = await self.pinecone_retriever.retrieve_and_format_for_llm(
                query, 
                doc_type="troubleshooting", 
                appliance_type=appliance_type,
                top_k=3
            )
            
            # If no Deepseek API key, just return the formatted docs
            if not self.deepseek_api_key:
                # Extract and format the most relevant document
                return self._format_raw_context_to_diagnosis(context, problem)
            
            # Create a prompt for the LLM to generate a diagnosis
            prompt = self._create_diagnosis_prompt(query, context, problem, appliance_type)
            
            # Call the DeepSeek API
            response = await self._call_deepseek_api(prompt)
            
            if not response:
                # Fall back to formatting the raw context
                return self._format_raw_context_to_diagnosis(context, problem)
                
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG diagnosis: {e}")
            return f"I apologize, but I encountered an error diagnosing the problem: {problem}. Please try asking in a different way."
    
    async def _call_deepseek_api(self, prompt: str) -> str:
        """
        Call the DeepSeek API to generate a response based on the RAG prompt.
        
        Args:
            prompt: The prompt containing context and query
            
        Returns:
            LLM-generated response
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,  # Lower temperature for factual responses
                "max_tokens": 1000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.deepseek.com/v1/chat/completions", 
                                        headers=headers, 
                                        json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        generated_text = result["choices"][0]["message"]["content"]
                        return generated_text
                    else:
                        error_text = await response.text()
                        logger.error(f"Error from DeepSeek API: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {e}")
            return None
    
    def _create_diagnosis_prompt(self, query: str, context: str, problem: str, appliance_type: str = None) -> str:
        """
        Create a prompt for the DeepSeek LLM to generate a diagnosis.
        
        Args:
            query: Original user query
            context: Retrieved document context
            problem: Description of the problem
            appliance_type: Type of appliance
            
        Returns:
            Formatted prompt string
        """
        appliance_type_str = f"{appliance_type} " if appliance_type else ""
        
        return f"""You are an expert appliance repair technician. A customer has a {appliance_type_str}problem: "{problem}"

Use the following reference documentation to diagnose the problem and recommend parts that may need to be replaced:

{context}

Based on this information, please provide:

1. A brief analysis of the likely causes of the problem
2. Step-by-step troubleshooting instructions
3. A list of parts that may need to be replaced, including part numbers and prices if available

Format your response as a clear diagnostic report with headings and bullet points. Focus on practical solutions the customer can implement.
"""
    
    def _format_raw_context_to_diagnosis(self, context: str, problem: str) -> str:
        """
        Format the raw context into a diagnosis when LLM is unavailable.
        
        Args:
            context: The raw document context
            problem: The problem description
            
        Returns:
            Formatted diagnosis report
        """
        if not context or "No relevant documentation found" in context:
            return f"I'm sorry, but I don't have specific diagnostic information for this problem: {problem}."
        
        # Extract document title for main heading
        title_match = re.search(r"DOCUMENT \d+: (.*?)(?:\n|$)", context)
        title = title_match.group(1) if title_match else f"Diagnosis for: {problem}"
        
        diagnosis = f"# {title}\n\n"
        
        # Extract possible causes
        raw_text_matches = re.findall(r"Content: (.*?)(?:\n\n|$)", context, re.DOTALL)
        if raw_text_matches:
            diagnosis += raw_text_matches[0].strip() + "\n\n"
        
        # Extract symptoms and solutions
        symptoms_section = False
        symptoms = []
        for line in context.split("\n"):
            if "Symptoms and Solutions:" in line:
                symptoms_section = True
                continue
            elif symptoms_section and line.strip() and not line.startswith("---"):
                if line.startswith("  -"):
                    symptoms.append(line.strip())
            elif symptoms_section and (not line.strip() or line.startswith("---")):
                symptoms_section = False
        
        if symptoms:
            diagnosis += "## Common Symptoms and Solutions:\n"
            for symptom in symptoms:
                diagnosis += f"{symptom}\n"
            diagnosis += "\n"
        
        # Extract recommended parts
        parts_section = False
        parts = []
        for line in context.split("\n"):
            if "Recommended Parts:" in line:
                parts_section = True
                continue
            elif parts_section and line.strip() and not line.startswith("---"):
                if line.startswith("  -"):
                    parts.append(line.strip())
            elif parts_section and (not line.strip() or line.startswith("---")):
                parts_section = False
        
        if parts:
            diagnosis += "## Recommended Parts:\n"
            for part in parts:
                diagnosis += f"{part}\n"
        
        return diagnosis
    
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Run the tool to diagnose problems and suggest parts.
        
        Args:
            query: The query string in format "problem:appliance_type" (appliance_type is optional)
            run_manager: Callback manager for the tool run
            
        Returns:
            Diagnosis with possible causes and suggested parts to check/replace
        """
        # For synchronous operation, we'll use asyncio to run the async method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._run_async(query, run_manager))
        return result
    
    def _extract_parts_from_text(self, text: str) -> Set[str]:
        """
        Extract likely part names from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Set of likely part names
        """
        # Common parts for refrigerators and dishwashers
        common_parts = {
            "compressor", "condenser", "evaporator", "fan motor", "water filter",
            "ice maker", "thermostat", "temperature control", "defrost heater",
            "door gasket", "water valve", "dispenser", "control board",
            "pump", "spray arm", "heating element", "water inlet valve", 
            "float switch", "timer", "control panel", "door latch", "drain hose"
        }
        
        found_parts = set()
        
        # Check for parts mentioned in the text
        text_lower = text.lower()
        for part in common_parts:
            if part in text_lower:
                # Get proper capitalization (first letter of each word capitalized)
                found_parts.add(' '.join(word.capitalize() for word in part.split()))
        
        return found_parts

class IntentClassificationTool:
    """
    Tool for classifying user intents using the Deepseek LLM.
    Used as a fallback when rule-based classification is insufficient.
    """
    name = "intent_classification"
    description = "Classifies user queries into intents: lookup, compatibility, install, diagnose, or out_of_scope"
    
    def __init__(self, deepseek_api_key=None):
        """Initialize with an API key for Deepseek."""
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.deepseek_api_key:
            logging.warning("No Deepseek API key provided. Intent classification will not work.")
    
    def _run(self, query: str) -> str:
        """Run intent classification on a query."""
        if not self.deepseek_api_key:
            raise ValueError("No Deepseek API key provided")
        
        prompt = self._create_prompt(query)
        
        try:
            response = self._call_deepseek_api(prompt)
            intent = self._extract_intent_from_response(response)
            return intent
        except Exception as e:
            logging.error(f"Error classifying intent with Deepseek: {e}")
            # Default to out_of_scope when classification fails
            return "out_of_scope"
    
    def _create_prompt(self, query: str) -> str:
        """Create a prompt for the DeepSeek API."""
        return f"""
        You are a specialized intent classifier for an appliance parts system.
        Your task is to categorize user queries related to refrigerator and dishwasher parts.
        
        The possible intents are:
        - lookup: User wants to find or identify a specific part
        - compatibility: User wants to check if a part is compatible with their appliance
        - install: User needs installation instructions for a part
        - diagnose: User has an issue and needs to diagnose which part may be causing it
        - out_of_scope: Query is not related to refrigerator or dishwasher parts
        
        Analyze the following query and respond with only one of the intent labels above:
        
        User query: "{query}"
        
        Intent:
        """
    
    def _call_deepseek_api(self, prompt: str) -> str:
        """Call the Deepseek API with the given prompt."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _extract_intent_from_response(self, response: str) -> str:
        """Extract the intent from the API response."""
        # Lower case and strip whitespace
        response = response.lower().strip()
        
        # Map of valid intents
        valid_intents = {
            "lookup", "compatibility", "install", "diagnose", "out_of_scope"
        }
        
        # Check if response is one of the valid intents
        for intent in valid_intents:
            if intent in response:
                return intent
        
        # Default to out_of_scope if no match
        return "out_of_scope"

class AsyncCatalogClient:
    """
    Async client for accessing product catalog information from MongoDB.
    Uses Motor for asynchronous MongoDB access.
    """
    
    def __init__(self, mongodb_uri: str, database_name: str = "partselect", collection_name: str = "parts", use_mock: bool = False):
        """
        Initialize the catalog client with MongoDB connection details.
        
        Args:
            mongodb_uri: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection to store parts
            use_mock: Whether to use mock data instead of MongoDB
        """
        self.use_mock = use_mock
        
        if use_mock:
            self.mock_provider = MockDataProvider()
            logger.info("Initialized AsyncCatalogClient with MockDataProvider")
        else:
            # Use Motor for async MongoDB operations
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.client[database_name]
            self.collection = self.db[collection_name]
            logger.info(f"Initialized AsyncCatalogClient with MongoDB collection {database_name}.{collection_name}")
    
    async def get_part(self, part_number: str) -> Optional[Dict]:
        """
        Get part details by part number.
        
        Args:
            part_number: The part number to look up
            
        Returns:
            Part details dictionary or None if not found
        """
        if self.use_mock:
            return self.mock_provider.get_part_by_number(part_number)
        
        # Use async MongoDB query
        part = await self.collection.find_one({"partNumber": part_number})
        
        # Convert MongoDB ObjectId to string for JSON serialization
        if part and "_id" in part:
            part["_id"] = str(part["_id"])
            
        return part
    
    async def search_parts(self, query: str, appliance_type: str = None, limit: int = 10) -> List[Dict]:
        """
        Search for parts matching the query.
        
        Args:
            query: Search query string
            appliance_type: Optional filter for refrigerator or dishwasher
            limit: Maximum number of results to return
            
        Returns:
            List of matching part dictionaries
        """
        if self.use_mock:
            return self.mock_provider.search_parts(query, appliance_type, limit)
        
        # Create a regex for case-insensitive search
        regex_pattern = f".*{re.escape(query)}.*"
        
        # Build the search query
        search_query = {
            "$or": [
                {"partNumber": {"$regex": regex_pattern, "$options": "i"}},
                {"name": {"$regex": regex_pattern, "$options": "i"}},
                {"description": {"$regex": regex_pattern, "$options": "i"}}
            ]
        }
        
        # Add appliance type filter if specified
        if appliance_type:
            search_query["applianceType"] = appliance_type
        
        # Execute async query
        cursor = self.collection.find(search_query).limit(limit)
        results = []
        
        # Iterate through async cursor to get results
        async for part in cursor:
            # Convert MongoDB ObjectId to string for JSON serialization
            if "_id" in part:
                part["_id"] = str(part["_id"])
            results.append(part)
            
        return results
    
    async def find_by_model(self, model_number: str, limit: int = 10) -> List[Dict]:
        """
        Find parts compatible with a specific model.
        
        Args:
            model_number: Model number to find compatible parts for
            limit: Maximum number of results to return
            
        Returns:
            List of compatible part dictionaries
        """
        if self.use_mock:
            return self.mock_provider.find_compatible_parts(model_number, limit)
        
        # Query for parts compatible with the model number
        query = {"compatibleModels": model_number}
        
        # Execute async query
        cursor = self.collection.find(query).limit(limit)
        results = []
        
        # Iterate through async cursor to get results
        async for part in cursor:
            # Convert MongoDB ObjectId to string for JSON serialization
            if "_id" in part:
                part["_id"] = str(part["_id"])
            results.append(part)
            
        return results
    
    async def check_compatibility(self, part_number: str, model_number: str) -> bool:
        """
        Check if a part is compatible with a specific model.
        
        Args:
            part_number: Part number to check
            model_number: Model number to check compatibility with
            
        Returns:
            True if compatible, False otherwise
        """
        if self.use_mock:
            return self.mock_provider.is_part_compatible(part_number, model_number)
        
        # Get the part first
        part = await self.get_part(part_number)
        
        if not part or "compatibleModels" not in part:
            return False
            
        # Check if the model number is in the compatible models list
        return model_number in part["compatibleModels"]
    
    async def get_popular_parts(self, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Get popular parts, optionally filtered by appliance type.
        
        Args:
            appliance_type: Optional appliance type filter ("refrigerator" or "dishwasher")
            limit: Maximum number of parts to return
            
        Returns:
            List of popular part dictionaries
        """
        if self.use_mock:
            return self.mock_provider.get_popular_parts(appliance_type, limit)
        
        # Build the query
        query = {}
        if appliance_type:
            query["applianceType"] = appliance_type
        
        # Execute async query, sort by popularity (assumimg a popularity field exists)
        # If not, we could use a different approach like sorting by sales count
        cursor = self.collection.find(query).sort("popularity", -1).limit(limit)
        results = []
        
        # Iterate through async cursor to get results
        async for part in cursor:
            # Convert MongoDB ObjectId to string for JSON serialization
            if "_id" in part:
                part["_id"] = str(part["_id"])
            results.append(part)
            
        return results


class AsyncDocsClient:
    """
    Async client for accessing documentation like installation and troubleshooting guides.
    Uses Motor for asynchronous MongoDB access.
    """
    
    def __init__(self, mongodb_uri: str, database_name: str = "partselect", collection_name: str = "docs", use_mock: bool = False):
        """
        Initialize the documentation client with MongoDB connection details.
        
        Args:
            mongodb_uri: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection to store docs
            use_mock: Whether to use mock data instead of MongoDB
        """
        self.use_mock = use_mock
        
        if use_mock:
            self.mock_provider = MockDataProvider()
            logger.info("Initialized AsyncDocsClient with MockDataProvider")
        else:
            # Use Motor for async MongoDB operations
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.client[database_name]
            self.collection = self.db[collection_name]
            logger.info(f"Initialized AsyncDocsClient with MongoDB collection {database_name}.{collection_name}")
    
    async def get_installation_docs(self, part_number: str = None, part_name: str = None, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Get installation documentation for a part.
        
        Args:
            part_number: Part number to find installation docs for
            part_name: Name of the part to find installation docs for
            appliance_type: Type of appliance (refrigerator or dishwasher)
            limit: Maximum number of results to return
            
        Returns:
            List of installation doc dictionaries
        """
        if self.use_mock:
            return self.mock_provider.get_installation_docs(part_name, appliance_type, limit)
        
        # Build the query
        query = {"type": "installation"}
        
        if part_number:
            query["partNumber"] = part_number
            
        if part_name:
            # Use a regex for case-insensitive search
            query["title"] = {"$regex": f".*{re.escape(part_name)}.*", "$options": "i"}
            
        if appliance_type:
            query["applianceType"] = appliance_type
        
        # Execute async query
        cursor = self.collection.find(query).limit(limit)
        results = []
        
        # Iterate through async cursor to get results
        async for doc in cursor:
            # Convert MongoDB ObjectId to string for JSON serialization
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            results.append(doc)
            
        return results
    
    async def get_troubleshooting_docs(self, symptom: str = None, problem: str = None, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Get troubleshooting documentation for a symptom.
        
        Args:
            symptom: Deprecated - use problem instead
            problem: Problem or symptom to find troubleshooting docs for
            appliance_type: Type of appliance (refrigerator or dishwasher)
            limit: Maximum number of results to return
            
        Returns:
            List of troubleshooting doc dictionaries
        """
        # For backwards compatibility
        problem = problem or symptom
        
        if self.use_mock:
            return self.mock_provider.get_troubleshooting_docs(problem, appliance_type, limit)
        
        # Build the query
        query = {"type": "troubleshooting"}
        
        if problem:
            # Use a regex for case-insensitive search in both title and content
            problem_regex = f".*{re.escape(problem)}.*"
            query["$or"] = [
                {"title": {"$regex": problem_regex, "$options": "i"}},
                {"content.raw_text": {"$regex": problem_regex, "$options": "i"}}
            ]
            
        if appliance_type:
            query["applianceType"] = appliance_type
        
        # Execute async query
        cursor = self.collection.find(query).limit(limit)
        results = []
        
        # Iterate through async cursor to get results
        async for doc in cursor:
            # Convert MongoDB ObjectId to string for JSON serialization
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            results.append(doc)
            
        return results
    
    async def search_docs(self, query: str, doc_type: str = None, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Search all documentation with a query string.
        
        Args:
            query: Search query string
            doc_type: Optional filter for doc type (installation, troubleshooting)
            appliance_type: Optional filter for appliance type (refrigerator, dishwasher)
            limit: Maximum number of results to return
            
        Returns:
            List of matching doc dictionaries
        """
        if self.use_mock:
            return self.mock_provider.search_docs(query, doc_type, appliance_type, limit)
        
        # Build the query
        search_query = {}
        
        # Add text search if query is provided
        if query:
            query_regex = f".*{re.escape(query)}.*"
            search_query["$or"] = [
                {"title": {"$regex": query_regex, "$options": "i"}},
                {"content.raw_text": {"$regex": query_regex, "$options": "i"}}
            ]
            
        # Add doc type filter if specified
        if doc_type:
            search_query["type"] = doc_type
            
        # Add appliance type filter if specified
        if appliance_type:
            search_query["applianceType"] = appliance_type
        
        # Execute async query
        cursor = self.collection.find(search_query).limit(limit)
        results = []
        
        # Iterate through async cursor to get results
        async for doc in cursor:
            # Convert MongoDB ObjectId to string for JSON serialization
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            results.append(doc)
            
        return results
    
    async def get_doc_by_title(self, title: str) -> Optional[Dict]:
        """
        Get a specific document by its title.
        
        Args:
            title: Exact title of the document to retrieve
            
        Returns:
            Document dictionary or None if not found
        """
        if self.use_mock:
            return self.mock_provider.get_doc_by_title(title)
        
        # Use exact title match
        doc = await self.collection.find_one({"title": title})
        
        # Convert MongoDB ObjectId to string for JSON serialization
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
            
        return doc
    
    async def get_repair_steps(self, part_name: str, appliance_type: str = None) -> List[str]:
        """
        Get step-by-step repair instructions for replacing a part.
        
        Args:
            part_name: Name of the part to find repair steps for
            appliance_type: Optional type of appliance for more specific results
            
        Returns:
            List of repair steps as strings
        """
        if self.use_mock:
            return self.mock_provider.get_repair_steps(part_name, appliance_type)
        
        # Get installation docs for the part
        docs = await self.get_installation_docs(part_name=part_name, appliance_type=appliance_type, limit=1)
        
        if not docs:
            return []
            
        # Extract steps from the first installation doc
        doc = docs[0]
        return doc.get("content", {}).get("steps", [])
    
    async def get_safety_notes(self, appliance_type: str = None) -> List[str]:
        """
        Get safety notes for appliance repair.
        
        Args:
            appliance_type: Optional type of appliance for more specific safety notes
            
        Returns:
            List of safety notes as strings
        """
        if self.use_mock:
            return self.mock_provider.get_safety_notes(appliance_type)
        
        # Build the query for safety documents
        query = {"type": "safety"}
        
        if appliance_type and appliance_type != "general":
            query["$or"] = [
                {"applianceType": appliance_type},
                {"applianceType": "general"}
            ]
        
        # Execute async query
        doc = await self.collection.find_one(query)
        
        if not doc:
            return []
            
        # Extract safety notes
        return doc.get("content", {}).get("safety_notes", [])

# Keep the existing CatalogClient and DocsClient classes for compatibility
class CatalogClient:
    """
    Client for accessing product catalog information.
    Uses MockDataProvider instead of directly accessing MongoDB.
    """
    
    def __init__(self):
        """
        Initialize the catalog client with the mock data provider.
        """
        self.provider = MockDataProvider()
        logger.info("Initialized CatalogClient with MockDataProvider")
    
    async def get_part(self, part_number: str) -> Optional[Dict]:
        """
        Get part details by part number.
        
        Args:
            part_number: The part number to look up
            
        Returns:
            Part details dictionary or None if not found
        """
        return self.provider.get_part_by_number(part_number)
    
    async def search_parts(self, query: str, appliance_type: str = None, limit: int = 10) -> List[Dict]:
        """
        Search for parts matching the query.
        
        Args:
            query: Search query string
            appliance_type: Optional filter for refrigerator or dishwasher
            limit: Maximum number of results to return
            
        Returns:
            List of matching part dictionaries
        """
        return self.provider.search_parts(query, appliance_type, limit)
    
    async def find_by_model(self, model_number: str, limit: int = 10) -> List[Dict]:
        """
        Find parts compatible with a specific model.
        
        Args:
            model_number: Model number to find compatible parts for
            limit: Maximum number of results to return
            
        Returns:
            List of compatible part dictionaries
        """
        return self.provider.find_compatible_parts(model_number, limit)
    
    async def check_compatibility(self, part_number: str, model_number: str) -> bool:
        """
        Check if a part is compatible with a specific model.
        
        Args:
            part_number: Part number to check
            model_number: Model number to check compatibility with
            
        Returns:
            True if compatible, False otherwise
        """
        return self.provider.is_part_compatible(part_number, model_number)
    
    async def get_popular_parts(self, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Get popular parts, optionally filtered by appliance type.
        
        Args:
            appliance_type: Optional appliance type filter ("refrigerator" or "dishwasher")
            limit: Maximum number of parts to return
            
        Returns:
            List of popular part dictionaries
        """
        return self.provider.get_popular_parts(appliance_type, limit)


class DocsClient:
    """
    Client for accessing documentation like installation and troubleshooting guides.
    Uses MockDataProvider instead of directly accessing MongoDB.
    """
    
    def __init__(self):
        """
        Initialize the documentation client with the mock data provider.
        """
        self.provider = MockDataProvider()
        logger.info("Initialized DocsClient with MockDataProvider")
    
    async def get_installation_docs(self, part_name: str = None, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Get installation documentation for a part or appliance type.
        
        Args:
            part_name: Name of the part to find installation docs for
            appliance_type: Type of appliance (refrigerator or dishwasher)
            limit: Maximum number of results to return
            
        Returns:
            List of installation doc dictionaries
        """
        return self.provider.get_installation_docs(part_name, appliance_type, limit)
    
    async def get_troubleshooting_docs(self, problem: str = None, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Get troubleshooting documentation for a symptom or appliance type.
        
        Args:
            problem: Problem or symptom to find troubleshooting docs for
            appliance_type: Type of appliance (refrigerator or dishwasher)
            limit: Maximum number of results to return
            
        Returns:
            List of troubleshooting doc dictionaries
        """
        return self.provider.get_troubleshooting_docs(problem, appliance_type, limit)
    
    async def search_docs(self, query: str, doc_type: str = None, appliance_type: str = None, limit: int = 5) -> List[Dict]:
        """
        Search all documentation with a query string.
        
        Args:
            query: Search query string
            doc_type: Optional filter for doc type (installation, troubleshooting)
            appliance_type: Optional filter for appliance type (refrigerator, dishwasher)
            limit: Maximum number of results to return
            
        Returns:
            List of matching doc dictionaries
        """
        return self.provider.search_docs(query, doc_type, appliance_type, limit)
    
    async def get_doc_by_title(self, title: str) -> Optional[Dict]:
        """
        Get a specific document by its title.
        
        Args:
            title: Exact title of the document to retrieve
            
        Returns:
            Document dictionary or None if not found
        """
        return self.provider.get_doc_by_title(title)
    
    async def get_repair_steps(self, part_name: str, appliance_type: str = None) -> List[str]:
        """
        Get step-by-step repair instructions for replacing a part.
        
        Args:
            part_name: Name of the part to find repair steps for
            appliance_type: Optional type of appliance for more specific results
            
        Returns:
            List of repair steps as strings
        """
        return self.provider.get_repair_steps(part_name, appliance_type)
    
    async def get_safety_notes(self, appliance_type: str = None) -> List[str]:
        """
        Get safety notes for appliance repair.
        
        Args:
            appliance_type: Optional type of appliance for more specific safety notes
            
        Returns:
            List of safety notes as strings
        """
        return self.provider.get_safety_notes(appliance_type)

class PartSelectScraper:
    """
    A web scraper for PartSelect.ca that fetches part details and stores them in MongoDB.
    """
    
    def __init__(self, mongodb_uri: str, database_name: str = "partselect", collection_name: str = "parts"):
        """
        Initialize the scraper with MongoDB connection details.
        
        Args:
            mongodb_uri: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection to store parts
        """
        self.base_url = "https://www.partselect.ca"
        self.search_url = f"{self.base_url}/search?query="
        
        # Add SSL options to the MongoDB connection
        if "?" in mongodb_uri:
            mongodb_uri += "&tlsAllowInvalidCertificates=true"
        else:
            mongodb_uri += "?tlsAllowInvalidCertificates=true"
            
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database_name]
        self.collection: Collection = self.db[collection_name]
        
        # Create indexes for faster lookups
        self.collection.create_index("partNumber", unique=True)
        self.collection.create_index("name")
        
        # Define various browser user agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get randomized headers that closely mimic a real browser.
        
        Returns:
            Dictionary of HTTP headers
        """
        user_agent = random.choice(self.user_agents)
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache"
        }
    
    def fetch_html(self, url: str, max_retries: int = 3, backoff_factor: float = 0.5) -> Optional[str]:
        """
        Fetch HTML from a URL with retry logic and respecting robots.txt.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            
        Returns:
            HTML content as string or None if failed
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Get fresh headers for each request
                headers = self.get_headers()
                
                # Add a random delay to mimic human behavior
                time.sleep(random.uniform(1.0, 3.0))
                
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                retry_count += 1
                wait_time = backoff_factor * (2 ** retry_count)
                logger.warning(f"Request failed: {e}. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                
                if retry_count == max_retries:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def search_part(self, query: str) -> Optional[str]:
        """
        Search for a part on PartSelect.ca.
        
        Args:
            query: Part number or search term
            
        Returns:
            Product page URL if found, None otherwise
        """
        search_url = f"{self.search_url}{query}"
        html = self.fetch_html(search_url)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for the first product result
        product_link = soup.select_one('.product-card a')
        if product_link and 'href' in product_link.attrs:
            product_url = product_link['href']
            if not product_url.startswith('http'):
                product_url = f"{self.base_url}{product_url}"
            return product_url
        
        return None
    
    def extract_part_details(self, html: str) -> Optional[Dict]:
        """
        Extract part details from product page HTML.
        
        Args:
            html: HTML content of the product page
            
        Returns:
            Dictionary with part details or None if parsing failed
        """
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        part_data = {}
        
        try:
            # Extract part number
            part_number_elem = soup.select_one('.item-number')
            if part_number_elem:
                part_data['partNumber'] = part_number_elem.text.strip().replace('Item #', '')
            
            # Extract name
            name_elem = soup.select_one('h1.product-name')
            if name_elem:
                part_data['name'] = name_elem.text.strip()
            
            # Extract image URL
            image_elem = soup.select_one('.product-image img')
            if image_elem and 'src' in image_elem.attrs:
                image_url = image_elem['src']
                if not image_url.startswith('http'):
                    image_url = f"{self.base_url}{image_url}"
                part_data['imageUrl'] = image_url
            
            # Extract price
            price_elem = soup.select_one('.product-price .price')
            if price_elem:
                price_text = price_elem.text.strip()
                # Remove currency symbol and convert to float
                price = float(re.sub(r'[^\d.]', '', price_text))
                part_data['price'] = price
            
            # Extract stock information
            stock_elem = soup.select_one('.availability')
            if stock_elem:
                stock_text = stock_elem.text.strip()
                if 'in stock' in stock_text.lower():
                    part_data['stock'] = 'In Stock'
                elif 'out of stock' in stock_text.lower():
                    part_data['stock'] = 'Out of Stock'
                else:
                    part_data['stock'] = stock_text
            
            # Extract compatible models
            compatible_models = []
            models_section = soup.select_one('.compatible-models')
            if models_section:
                model_items = models_section.select('li')
                for item in model_items:
                    model_text = item.text.strip()
                    compatible_models.append(model_text)
            
            part_data['compatibleModels'] = compatible_models
            
            return part_data
            
        except Exception as e:
            logger.error(f"Error parsing part details: {e}")
            return None
    
    def get_part_details(self, query: str) -> Optional[Dict]:
        """
        Get part details by part number or search term.
        
        Args:
            query: Part number or search term
            
        Returns:
            Dictionary with part details or None if not found
        """
        # Check if part exists in MongoDB first
        if re.match(r'^[A-Za-z0-9]+$', query):  # Likely a part number
            existing_part = self.collection.find_one({"partNumber": query})
            if existing_part:
                # Convert ObjectId to string for JSON serialization
                existing_part['_id'] = str(existing_part['_id'])
                return existing_part
        
        # If not found in DB, scrape the website
        product_url = self.search_part(query)
        if not product_url:
            logger.warning(f"No product found for query: {query}")
            return None
        
        html = self.fetch_html(product_url)
        part_data = self.extract_part_details(html)
        
        if part_data:
            # Store in MongoDB
            self.upsert_part(part_data)
            return part_data
        
        return None
    
    def upsert_part(self, part_data: Dict) -> bool:
        """
        Upsert part data into MongoDB.
        
        Args:
            part_data: Part data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not part_data or 'partNumber' not in part_data:
            logger.error("Invalid part data for upsert")
            return False
        
        try:
            result = self.collection.update_one(
                {"partNumber": part_data["partNumber"]},
                {"$set": part_data},
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id is not None:
                logger.info(f"Upserted part {part_data['partNumber']} to MongoDB")
                return True
            else:
                logger.info(f"Part {part_data['partNumber']} already exists with the same data")
                return True
                
        except Exception as e:
            logger.error(f"Error upserting part to MongoDB: {e}")
            return False
    
    def bulk_upsert_parts(self, part_numbers: List[str]) -> Dict[str, int]:
        """
        Bulk upsert multiple parts by part number.
        
        Args:
            part_numbers: List of part numbers to scrape and upsert
            
        Returns:
            Dictionary with success and failure counts
        """
        results = {"success": 0, "failure": 0}
        
        for part_number in part_numbers:
            logger.info(f"Processing part: {part_number}")
            part_data = self.get_part_details(part_number)
            
            if part_data:
                results["success"] += 1
            else:
                results["failure"] += 1
            
            # Be nice to the server and avoid rate limiting
            time.sleep(2)
        
        return results

class DocScraper:
    """
    A web scraper for PartSelect.ca documentation pages that extracts repair instructions,
    troubleshooting guides, and other documentation.
    """
    
    def __init__(self, mongodb_uri: str, database_name: str = "partselect", collection_name: str = "docs"):
        """
        Initialize the document scraper with MongoDB connection details.
        
        Args:
            mongodb_uri: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection to store documents
        """
        self.base_url = "https://www.partselect.ca"
        
        # Add SSL options to the MongoDB connection
        if "?" in mongodb_uri:
            mongodb_uri += "&tlsAllowInvalidCertificates=true"
        else:
            mongodb_uri += "?tlsAllowInvalidCertificates=true"
            
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database_name]
        self.collection: Collection = self.db[collection_name]
        
        # Create indexes for faster lookups
        self.collection.create_index("docId", unique=True)
        self.collection.create_index("partNumber")
        self.collection.create_index("type")
        
        # Common URL patterns for various doc types
        self.url_patterns = {
            "installation": [
                "/installation/",
                "/repair-guide/",
                "/DIY/"
            ],
            "troubleshooting": [
                "/troubleshooting/",
                "/repair-help/",
                "/symptom/"
            ],
            "maintenance": [
                "/maintenance/",
                "/care-guide/"
            ]
        }
        
        # Define various browser user agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        
        # Track visited URLs to avoid duplicates
        self.visited_urls: Set[str] = set()
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get randomized headers that closely mimic a real browser.
        
        Returns:
            Dictionary of HTTP headers
        """
        user_agent = random.choice(self.user_agents)
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache"
        }
    
    def fetch_html(self, url: str, max_retries: int = 3, backoff_factor: float = 0.5) -> Optional[str]:
        """
        Fetch HTML from a URL with retry logic and respecting robots.txt.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            
        Returns:
            HTML content as string or None if failed
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Get fresh headers for each request
                headers = self.get_headers()
                
                # Add a random delay to mimic human behavior
                time.sleep(random.uniform(1.0, 3.0))
                
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                retry_count += 1
                wait_time = backoff_factor * (2 ** retry_count)
                logger.warning(f"Request failed: {e}. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                
                if retry_count == max_retries:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def determine_doc_type(self, url: str) -> str:
        """
        Determine the type of document based on URL pattern.
        
        Args:
            url: URL of the document
            
        Returns:
            Document type (installation, troubleshooting, maintenance, or general)
        """
        url_lower = url.lower()
        
        for doc_type, patterns in self.url_patterns.items():
            if any(pattern in url_lower for pattern in patterns):
                return doc_type
        
        return "general"
    
    def extract_part_number(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract part number from the document page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Part number if found, None otherwise
        """
        # Try different patterns to find part numbers
        # 1. Look for specific part number elements
        part_elem = soup.select_one('.part-number, .model-number, .item-number')
        if part_elem:
            text = part_elem.text.strip()
            match = re.search(r'[A-Z0-9]{5,}', text)
            if match:
                return match.group(0)
        
        # 2. Look for text patterns that might indicate part numbers
        for text in soup.stripped_strings:
            if "part number" in text.lower() or "model number" in text.lower():
                match = re.search(r'[A-Z0-9]{5,}', text)
                if match:
                    return match.group(0)
        
        # 3. Try to extract from URL
        url_parts = soup.find('meta', {'property': 'og:url'})
        if url_parts and 'content' in url_parts.attrs:
            url = url_parts['content']
            match = re.search(r'/([A-Z0-9]{5,})/', url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_doc_content(self, soup: BeautifulSoup, doc_type: str) -> Dict:
        """
        Extract content from the document page based on doc type.
        
        Args:
            soup: BeautifulSoup object of the page
            doc_type: Type of document (installation, troubleshooting, etc.)
            
        Returns:
            Dictionary with extracted content
        """
        content = {
            "title": "",
            "steps": [],
            "safety_notes": [],
            "symptoms": {},
            "diagrams": [],
            "raw_text": ""
        }
        
        # Extract title
        title_elem = soup.select_one('h1')
        if title_elem:
            content["title"] = title_elem.text.strip()
        
        # Extract raw text for vector search
        main_content = soup.select_one('main, article, .content, .main-content')
        if main_content:
            content["raw_text"] = main_content.get_text(separator=" ", strip=True)
        
        if doc_type == "installation":
            # Extract step-by-step instructions
            steps_container = soup.select('.step, .installation-step, ol > li, .steps > li')
            for step in steps_container:
                step_text = step.get_text(strip=True)
                if step_text:
                    content["steps"].append(step_text)
            
            # If no structured steps found, try to extract from paragraphs
            if not content["steps"]:
                paragraphs = soup.select('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 30:  # Filter out short paragraphs
                        content["steps"].append(text)
        
        # Extract safety notes for all doc types
        safety_notes = soup.select('.safety, .warning, .caution, .alert')
        for note in safety_notes:
            note_text = note.get_text(strip=True)
            if note_text:
                content["safety_notes"].append(note_text)
        
        if doc_type == "troubleshooting":
            # Extract symptom mappings
            symptom_elements = soup.select('.symptom, .problem, .issue')
            for elem in symptom_elements:
                # Try to find symptom and cause/solution
                symptom = elem.select_one('.symptom-name, .problem-name, h3, h4')
                solution = elem.select_one('.solution, .fix, .remedy, p')
                
                if symptom and solution:
                    symptom_text = symptom.get_text(strip=True)
                    solution_text = solution.get_text(strip=True)
                    content["symptoms"][symptom_text] = solution_text
        
        # Extract diagram text
        diagrams = soup.select('.diagram, .figure, figure')
        for diagram in diagrams:
            caption = diagram.select_one('figcaption, .caption')
            if caption:
                content["diagrams"].append(caption.get_text(strip=True))
        
        return content
    
    def process_document(self, url: str) -> Optional[Dict]:
        """
        Process a document URL to extract and store its content.
        
        Args:
            url: URL of the document
            
        Returns:
            Processed document data or None if failed
        """
        if url in self.visited_urls:
            logger.info(f"Skipping already processed URL: {url}")
            return None
        
        self.visited_urls.add(url)
        
        # Make sure URL is absolute
        if not url.startswith(('http://', 'https://')):
            url = urllib.parse.urljoin(self.base_url, url)
        
        logger.info(f"Processing document URL: {url}")
        
        html = self.fetch_html(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        doc_type = self.determine_doc_type(url)
        part_number = self.extract_part_number(soup)
        content = self.extract_doc_content(soup, doc_type)
        
        # Generate a unique ID if we don't have a part number
        doc_id = part_number if part_number else str(uuid.uuid4())
        
        doc_data = {
            "docId": doc_id,
            "partNumber": part_number,
            "type": doc_type,
            "url": url,
            "title": content["title"],
            "content": content,
            "processed_at": time.time()
        }
        
        # Store in MongoDB
        self.upsert_doc(doc_data)
        
        # Find and queue additional document links if this is an index page
        if doc_type in ["installation", "troubleshooting"] and len(content["steps"]) < 3:
            self.find_related_docs(soup, url)
        
        return doc_data
    
    def find_related_docs(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find related document links on the page.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of related document URLs
        """
        related_urls = []
        
        # Find links that match our doc patterns
        for doc_type, patterns in self.url_patterns.items():
            for pattern in patterns:
                links = soup.select(f'a[href*="{pattern}"]')
                for link in links:
                    if 'href' in link.attrs:
                        href = link['href']
                        # Make sure URL is absolute
                        if not href.startswith(('http://', 'https://')):
                            href = urllib.parse.urljoin(base_url, href)
                        
                        if href not in self.visited_urls:
                            related_urls.append(href)
        
        return related_urls
    
    def upsert_doc(self, doc_data: Dict) -> bool:
        """
        Upsert document data into MongoDB.
        
        Args:
            doc_data: Document data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not doc_data or 'docId' not in doc_data:
            logger.error("Invalid document data for upsert")
            return False
        
        try:
            result = self.collection.update_one(
                {"docId": doc_data["docId"]},
                {"$set": doc_data},
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id is not None:
                logger.info(f"Upserted document {doc_data['docId']} to MongoDB")
                return True
            else:
                logger.info(f"Document {doc_data['docId']} already exists with the same data")
                return True
                
        except Exception as e:
            logger.error(f"Error upserting document to MongoDB: {e}")
            return False
    
    def crawl_url_pattern(self, url_pattern: str, max_docs: int = 100) -> Dict[str, int]:
        """
        Crawl a URL pattern to find and process documents.
        
        Args:
            url_pattern: URL or URL pattern to crawl
            max_docs: Maximum number of documents to process
            
        Returns:
            Dictionary with success and failure counts
        """
        results = {"success": 0, "failure": 0, "skipped": 0}
        
        # Make sure URL is absolute
        if not url_pattern.startswith(('http://', 'https://')):
            url_pattern = urllib.parse.urljoin(self.base_url, url_pattern)
        
        # Start with the pattern URL
        urls_to_process = [url_pattern]
        processed_count = 0
        
        while urls_to_process and processed_count < max_docs:
            current_url = urls_to_process.pop(0)
            
            if current_url in self.visited_urls:
                results["skipped"] += 1
                continue
            
            doc_data = self.process_document(current_url)
            processed_count += 1
            
            if doc_data:
                results["success"] += 1
                
                # Find more URLs to crawl
                html = self.fetch_html(current_url)
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    related_urls = self.find_related_docs(soup, current_url)
                    
                    # Add new URLs to process, up to the max limit
                    for url in related_urls:
                        if url not in self.visited_urls and processed_count + len(urls_to_process) < max_docs:
                            urls_to_process.append(url)
            else:
                results["failure"] += 1
            
            # Be nice to the server and avoid rate limiting
            time.sleep(2)
        
        return results
    
    def bulk_process_urls(self, urls: List[str], max_per_url: int = 20) -> Dict[str, int]:
        """
        Bulk process multiple URL patterns.
        
        Args:
            urls: List of URLs or URL patterns to process
            max_per_url: Maximum documents to process per URL pattern
            
        Returns:
            Dictionary with success and failure counts
        """
        total_results = {"success": 0, "failure": 0, "skipped": 0}
        
        for url in urls:
            logger.info(f"Processing URL pattern: {url}")
            results = self.crawl_url_pattern(url, max_per_url)
            
            total_results["success"] += results["success"]
            total_results["failure"] += results["failure"]
            total_results["skipped"] += results["skipped"]
        
        return total_results

class CartTool(BaseTool):
    """
    Tool for managing shopping cart operations using Redis.
    Provides add_item, remove_item, and view_cart functionality.
    """
    name: ClassVar[str] = "cart_tool"
    description: ClassVar[str] = "Manage shopping cart operations: add items, remove items, or view the cart"
    
    def __init__(self, catalog_client=None, redis_url="redis://localhost:6379/0", **kwargs):
        """
        Initialize the cart tool with Redis connection and catalog client for product details.
        
        Args:
            catalog_client: An instance of CatalogClient or AsyncCatalogClient
            redis_url: URL for Redis connection
        """
        super().__init__(**kwargs)
        self.catalog_client = catalog_client
        self.redis_client = redis.from_url(redis_url)
        
    async def _run_async(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async implementation to perform cart operations.
        
        Args:
            query: The operation and parameters in format "operation:param1:param2"
                  Operations: add, remove, view
                  For add: "add:part_number:quantity"
                  For remove: "remove:part_number:quantity"
                  For view: "view"
            run_manager: Callback manager for the tool run
            
        Returns:
            JSON string with operation result or error message
        """
        try:
            # Parse the query
            parts = query.split(":", 2)
            operation = parts[0].strip().lower()
            
            # Generate a cart ID or use an existing one (would be tied to user session in production)
            cart_id = "cart:user123"  # In real app, this would be unique per user
            
            if operation == "add":
                if len(parts) < 3:
                    return json.dumps({"error": "Invalid format. Use 'add:part_number:quantity'"})
                
                part_number = parts[1].strip()
                try:
                    quantity = int(parts[2].strip())
                    if quantity <= 0:
                        return json.dumps({"error": "Quantity must be positive"})
                except ValueError:
                    return json.dumps({"error": "Quantity must be a valid number"})
                
                # Check if part exists
                part = await self.catalog_client.get_part(part_number)
                if not part:
                    return json.dumps({"error": f"Part {part_number} not found"})
                
                # Add to cart in Redis (hash structure)
                current_qty = self.redis_client.hget(cart_id, part_number)
                new_qty = quantity
                if current_qty:
                    new_qty += int(current_qty)
                
                self.redis_client.hset(cart_id, part_number, new_qty)
                self.redis_client.expire(cart_id, 86400)  # Expire after 24 hours
                
                # Get details for response
                return json.dumps({
                    "status": "success",
                    "message": f"Added {quantity} of {part['name']} to cart",
                    "part": part,
                    "quantity": new_qty
                })
                
            elif operation == "remove":
                if len(parts) < 2:
                    return json.dumps({"error": "Invalid format. Use 'remove:part_number[:quantity]'"})
                
                part_number = parts[1].strip()
                quantity = None
                if len(parts) == 3:
                    try:
                        quantity = int(parts[2].strip())
                        if quantity <= 0:
                            return json.dumps({"error": "Quantity must be positive"})
                    except ValueError:
                        return json.dumps({"error": "Quantity must be a valid number"})
                
                # Check if item is in cart
                current_qty = self.redis_client.hget(cart_id, part_number)
                if not current_qty:
                    return json.dumps({"error": f"Part {part_number} not in cart"})
                
                current_qty = int(current_qty)
                
                # Remove from cart
                if quantity is None or quantity >= current_qty:
                    # Remove completely
                    self.redis_client.hdel(cart_id, part_number)
                    message = f"Removed part {part_number} from cart"
                else:
                    # Reduce quantity
                    new_qty = current_qty - quantity
                    self.redis_client.hset(cart_id, part_number, new_qty)
                    message = f"Reduced quantity of part {part_number} by {quantity}"
                
                return json.dumps({
                    "status": "success",
                    "message": message
                })
                
            elif operation == "view":
                # Get all items in cart
                cart_items = self.redis_client.hgetall(cart_id)
                
                if not cart_items:
                    return json.dumps({
                        "status": "success",
                        "message": "Your cart is empty",
                        "items": []
                    })
                
                # Build cart with details
                cart_details = []
                total_price = 0
                
                for part_number, quantity in cart_items.items():
                    part_number = part_number.decode('utf-8') if isinstance(part_number, bytes) else part_number
                    quantity = int(quantity.decode('utf-8') if isinstance(quantity, bytes) else quantity)
                    
                    # Get part details
                    part = await self.catalog_client.get_part(part_number)
                    
                    if part:
                        item_price = part.get("price", 0) * quantity
                        total_price += item_price
                        
                        cart_details.append({
                            "part_number": part_number,
                            "name": part.get("name", "Unknown Part"),
                            "quantity": quantity,
                            "unit_price": part.get("price", 0),
                            "total_price": item_price
                        })
                
                return json.dumps({
                    "status": "success",
                    "message": f"Cart contains {len(cart_details)} items",
                    "items": cart_details,
                    "total_price": total_price
                })
            
            else:
                return json.dumps({
                    "error": f"Unknown operation: {operation}. Valid operations are 'add', 'remove', 'view'"
                })
                
        except Exception as e:
            logger.error(f"Error in cart operation: {e}")
            return json.dumps({"error": f"Error in cart operation: {str(e)}"})
    
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Run the tool to perform cart operations.
        
        Args:
            query: The operation and parameters
            run_manager: Callback manager for the tool run
            
        Returns:
            JSON string with operation result or error message
        """
        # For synchronous operation, we'll use asyncio to run the async method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._run_async(query, run_manager))
        return result

class OrderStatusTool(BaseTool):
    """
    Tool for checking order status from the PartSelect API.
    """
    name: ClassVar[str] = "order_status_tool"
    description: ClassVar[str] = "Check the status of an order by order number or email"
    
    def __init__(self, api_base_url="https://api.partselect.com/v1", api_key=None, use_mock=True, **kwargs):
        """
        Initialize the order status tool with API connection details.
        
        Args:
            api_base_url: Base URL for the PartSelect API
            api_key: API key for authentication
            use_mock: Whether to use mock data (for testing)
        """
        super().__init__(**kwargs)
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.use_mock = use_mock
        self.mock_orders = self._initialize_mock_orders()
    
    def _initialize_mock_orders(self) -> Dict[str, Dict]:
        """Initialize mock order data for testing"""
        return {
            "ORD123456": {
                "order_number": "ORD123456",
                "date": "2025-05-15",
                "customer_email": "john.doe@example.com",
                "status": "Shipped",
                "tracking_number": "1ZW23X4Y5678901234",
                "carrier": "UPS",
                "estimated_delivery": "2025-05-22",
                "items": [
                    {
                        "part_number": "DA29-00020B",
                        "name": "Samsung Refrigerator Water Filter",
                        "quantity": 2,
                        "price": 49.99
                    }
                ],
                "total": 99.98,
                "shipping_address": {
                    "name": "John Doe",
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": "12345"
                }
            },
            "ORD789012": {
                "order_number": "ORD789012",
                "date": "2025-05-18",
                "customer_email": "jane.smith@example.com",
                "status": "Processing",
                "items": [
                    {
                        "part_number": "WPW10295370",
                        "name": "Dishwasher Control Board",
                        "quantity": 1,
                        "price": 129.99
                    },
                    {
                        "part_number": "NLP8800",
                        "name": "Installation Kit",
                        "quantity": 1,
                        "price": 24.99
                    }
                ],
                "total": 154.98,
                "shipping_address": {
                    "name": "Jane Smith",
                    "street": "456 Oak Ave",
                    "city": "Somewhere",
                    "state": "NY",
                    "zip": "67890"
                }
            },
            "ORD345678": {
                "order_number": "ORD345678",
                "date": "2025-05-10",
                "customer_email": "bob.jones@example.com",
                "status": "Delivered",
                "delivery_date": "2025-05-17",
                "tracking_number": "9405803699300493847283",
                "carrier": "USPS",
                "items": [
                    {
                        "part_number": "4392067",
                        "name": "Dryer Repair Kit",
                        "quantity": 1,
                        "price": 39.99
                    }
                ],
                "total": 39.99,
                "shipping_address": {
                    "name": "Bob Jones",
                    "street": "789 Pine Blvd",
                    "city": "Elsewhere",
                    "state": "TX",
                    "zip": "13579"
                }
            }
        }
    
    async def _run_async(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async implementation to check order status.
        
        Args:
            query: The order number or email to check
            run_manager: Callback manager for the tool run
            
        Returns:
            JSON string with order status or error message
        """
        try:
            # If query is empty, return an error
            if not query:
                return json.dumps({"error": "Order number or email is required"})
            
            query = query.strip()
            
            # Check if using mock data
            if self.use_mock:
                return await self._get_mock_order_status(query)
            
            # Make API request to get order status
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Determine if query is an order number or email
            if "@" in query:
                url = f"{self.api_base_url}/orders?email={urllib.parse.quote(query)}"
            else:
                url = f"{self.api_base_url}/orders/{query}"
            
            # Make async request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return json.dumps(result)
                    elif response.status == 404:
                        return json.dumps({"error": f"Order not found for '{query}'"})
                    else:
                        return json.dumps({"error": f"Error checking order status: {response.status}"})
            
        except Exception as e:
            logger.error(f"Error checking order status: {e}")
            return json.dumps({"error": f"Error checking order status: {str(e)}"})
    
    async def _get_mock_order_status(self, query: str) -> str:
        """Get mock order status data for testing"""
        # Add a small delay to simulate API call
        await asyncio.sleep(0.5)
        
        # Check if query is an order number or email
        if "@" in query:
            # Search by email
            email = query.lower()
            orders = []
            
            for order_number, order_data in self.mock_orders.items():
                if order_data.get("customer_email", "").lower() == email:
                    # Add order to results
                    orders.append(order_data)
            
            if orders:
                return json.dumps({
                    "customer_email": email,
                    "orders": orders
                })
            else:
                return json.dumps({"error": f"No orders found for email '{email}'"})
        else:
            # Search by order number
            order_number = query.upper()
            if order_number in self.mock_orders:
                return json.dumps(self.mock_orders[order_number])
            else:
                return json.dumps({"error": f"Order '{order_number}' not found"})
    
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Run the tool to check order status.
        
        Args:
            query: The order number or email to check
            run_manager: Callback manager for the tool run
            
        Returns:
            JSON string with order status or error message
        """
        # For synchronous operation, we'll use asyncio to run the async method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self._run_async(query, run_manager))
        return result 