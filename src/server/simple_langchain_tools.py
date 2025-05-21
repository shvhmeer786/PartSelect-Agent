"""
Simple implementation of LangChain-compatible tools without using Pydantic inheritance.
These tools maintain the same interface but avoid Pydantic validation issues.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleProductLookupTool:
    """Tool for looking up product details by part number."""
    
    def __init__(self, catalog_client):
        """Initialize with a catalog client."""
        self.name = "product_lookup_tool"
        self.description = "Look up detailed information about a specific part by its part number"
        self.catalog_client = catalog_client
    
    async def _arun(self, part_number: str) -> str:
        """Async implementation of the tool."""
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
    
    def run(self, part_number: str) -> str:
        """Synchronous implementation that calls the async method."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(part_number))


class SimpleCompatibilityTool:
    """Tool for checking compatibility between parts and models."""
    
    def __init__(self, catalog_client):
        """Initialize with a catalog client."""
        self.name = "compatibility_tool"
        self.description = "Check if a part is compatible with a specific appliance model"
        self.catalog_client = catalog_client
    
    async def _arun(self, query: str) -> str:
        """Async implementation of the tool."""
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
    
    def run(self, query: str) -> str:
        """Synchronous implementation that calls the async method."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(query))


class SimpleInstallationGuideTool:
    """Tool for retrieving installation guides for parts."""
    
    def __init__(self, docs_client, deepseek_api_key=None):
        """Initialize with a docs client."""
        self.name = "installation_guide_tool"
        self.description = "Get step-by-step installation instructions for a specific part"
        self.docs_client = docs_client
        self.deepseek_api_key = deepseek_api_key
    
    async def _arun(self, query: str) -> str:
        """Async implementation of the tool."""
        try:
            # Parse the query
            parts = query.split(":", 1)
            part_name = parts[0].strip()
            appliance_type = parts[1].strip() if len(parts) > 1 else None
            
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
                # Handle case where doc could be a string
                if isinstance(doc, str):
                    installation_info += doc
                    continue
                
                # Handle case where doc is a dictionary
                title = doc.get("title", "Installation Guide")
                installation_info += f"## {title}\n\n"
                
                # Extract steps from content
                content = doc.get("content", {})
                
                # Handle case where content is a string
                if isinstance(content, str):
                    installation_info += f"{content}\n\n"
                    continue
                
                # Handle case where content is a dictionary
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
    
    def run(self, query: str) -> str:
        """Synchronous implementation that calls the async method."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(query))


class SimpleErrorDiagnosisTool:
    """Tool for diagnosing appliance problems and suggesting likely parts that need replacement."""
    
    def __init__(self, docs_client, catalog_client, deepseek_api_key=None):
        """Initialize with docs and catalog clients."""
        self.name = "error_diagnosis_tool"
        self.description = "Diagnose appliance problems and suggest likely parts that need replacement"
        self.docs_client = docs_client
        self.catalog_client = catalog_client
        self.deepseek_api_key = deepseek_api_key
    
    async def _arun(self, query: str) -> str:
        """Async implementation of the tool."""
        try:
            # Parse the query
            parts = query.split(":", 1)
            problem = parts[0].strip()
            appliance_type = parts[1].strip() if len(parts) > 1 else None
            
            # Get troubleshooting docs for the problem
            docs = await self.docs_client.get_troubleshooting_docs(problem=problem, appliance_type=appliance_type, limit=3)
            
            if not docs or len(docs) == 0:
                return f"No troubleshooting information found for '{problem}'."
            
            # Compile diagnosis information
            diagnosis = f"# Diagnosis for: {problem}\n\n"
            likely_parts = set()
            
            for doc in docs:
                # Handle case where doc could be a string
                if isinstance(doc, str):
                    diagnosis += doc + "\n\n"
                    parts_mentioned = self._extract_parts_from_text(doc)
                    likely_parts.update(parts_mentioned)
                    continue
                
                # Handle case where doc is a dictionary
                title = doc.get("title", "Troubleshooting Guide")
                diagnosis += f"## {title}\n\n"
                
                # Extract information from content
                content = doc.get("content", {})
                
                # Handle case where content is a string
                if isinstance(content, str):
                    diagnosis += f"{content}\n\n"
                    parts_mentioned = self._extract_parts_from_text(content)
                    likely_parts.update(parts_mentioned)
                    continue
                
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
    
    def _extract_parts_from_text(self, text: str) -> Set[str]:
        """Extract likely part names from text."""
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
    
    def run(self, query: str) -> str:
        """Synchronous implementation that calls the async method."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(query)) 