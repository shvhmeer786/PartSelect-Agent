#!/usr/bin/env python3
"""
Simple Pinecone vector database emulator.
Provides a mock implementation of the Pinecone API for development and testing.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uuid
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI(title="Pinecone Emulator")

# Data models
class CreateIndexRequest(BaseModel):
    name: str
    dimension: int
    metric: str = "cosine"
    pods: int = 1
    replicas: int = 1
    metadata_config: Optional[Dict[str, Any]] = None

class UpsertRequest(BaseModel):
    vectors: List[Dict[str, Any]]
    namespace: Optional[str] = "default"

class QueryVector(BaseModel):
    id: Optional[str] = None
    values: List[float]
    sparse_values: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    vector: List[float]
    namespace: Optional[str] = "default"
    top_k: int = 10
    include_metadata: bool = True
    include_values: bool = False
    filter: Optional[Dict[str, Any]] = None

class Match(BaseModel):
    id: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    values: Optional[List[float]] = None

class QueryResponse(BaseModel):
    matches: List[Match]
    namespace: str

# In-memory storage
indexes = {}
vectors = {}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/indexes")
def create_index(request: CreateIndexRequest):
    """Create a new index."""
    if request.name in indexes:
        raise HTTPException(status_code=400, detail=f"Index {request.name} already exists")
    
    indexes[request.name] = {
        "name": request.name,
        "dimension": request.dimension,
        "metric": request.metric,
        "status": "ready"
    }
    
    vectors[request.name] = {}
    
    return {"message": f"Created index: {request.name}"}

@app.get("/indexes")
def list_indexes():
    """List all indexes."""
    return {"indexes": [{"name": name, **info} for name, info in indexes.items()]}

@app.delete("/indexes/{index_name}")
def delete_index(index_name: str):
    """Delete an index."""
    if index_name not in indexes:
        raise HTTPException(status_code=404, detail=f"Index {index_name} not found")
    
    del indexes[index_name]
    del vectors[index_name]
    
    return {"message": f"Deleted index: {index_name}"}

@app.post("/vectors/upsert")
def upsert_vectors(index_name: str, request: UpsertRequest):
    """Upsert vectors into an index."""
    if index_name not in indexes:
        raise HTTPException(status_code=404, detail=f"Index {index_name} not found")
    
    namespace = request.namespace or "default"
    
    if namespace not in vectors[index_name]:
        vectors[index_name][namespace] = {}
    
    for vector in request.vectors:
        vector_id = vector.get("id", str(uuid.uuid4()))
        vector_values = vector.get("values", [])
        metadata = vector.get("metadata", {})
        
        if len(vector_values) != indexes[index_name]["dimension"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Vector dimension mismatch. Expected {indexes[index_name]['dimension']}"
            )
        
        vectors[index_name][namespace][vector_id] = {
            "values": vector_values,
            "metadata": metadata
        }
    
    return {"upserted_count": len(request.vectors)}

@app.post("/query")
def query(index_name: str, request: QueryRequest):
    """Query vectors in an index."""
    if index_name not in indexes:
        raise HTTPException(status_code=404, detail=f"Index {index_name} not found")
    
    namespace = request.namespace or "default"
    
    if namespace not in vectors[index_name]:
        return {"matches": [], "namespace": namespace}
    
    query_vector = np.array(request.vector).reshape(1, -1)
    
    # Calculate similarities for all vectors in the namespace
    similarities = []
    for vector_id, vector_data in vectors[index_name][namespace].items():
        vector_values = np.array(vector_data["values"]).reshape(1, -1)
        
        # Apply filter if present
        if request.filter:
            metadata = vector_data["metadata"]
            # Simple filter implementation (only exact matches)
            matches_filter = all(
                metadata.get(k) == v for k, v in request.filter.items()
            )
            if not matches_filter:
                continue
        
        similarity = cosine_similarity(query_vector, vector_values)[0][0]
        similarities.append((vector_id, similarity, vector_data))
    
    # Sort by similarity and take top_k
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_matches = similarities[:request.top_k]
    
    # Format response
    matches = []
    for vector_id, score, vector_data in top_matches:
        match = {
            "id": vector_id,
            "score": float(score),
            "metadata": vector_data["metadata"] if request.include_metadata else None
        }
        
        if request.include_values:
            match["values"] = vector_data["values"]
            
        matches.append(Match(**match))
    
    return QueryResponse(matches=matches, namespace=namespace)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 