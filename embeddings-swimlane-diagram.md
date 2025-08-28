# 🏊‍♂️ Embeddings Orchestration Swimlane Diagram

## Azure Functions Durable Orchestration - Code Snippet Embedding Pipeline

```mermaid
sequenceDiagram
    participant Client as 🌐 HTTP Client
    participant Starter as 🚀 HTTP Starter<br/>(http_start_embeddings)
    participant Orchestrator as 🎭 Orchestrator<br/>(embeddings_orchestrator)
    participant EmbedActivity as ⚡ Embed Activity<br/>(embed_chunk_activity)
    participant PersistActivity as 💾 Persist Activity<br/>(persist_snippet_activity)
    participant OpenAI as 🧠 Azure OpenAI<br/>(Embeddings API)
    participant CosmosDB as 🗄️ Cosmos DB<br/>(Vector Storage)

    Note over Client, CosmosDB: 📋 Phase 1: Request Initiation
    
    Client->>+Starter: POST /api/orchestrators/embeddings<br/>{"projectId": "my-project",<br/>"snippets": [{"name": "func1", "code": "..."}]}
    
    Starter->>Starter: ❌ validate_input() → False<br/>(⚠️ Currently broken!)
    
    alt Input Valid (after fix)
        Starter->>+Orchestrator: 🎬 Start Orchestration<br/>(Durable Functions)
        Starter-->>Client: 📍 202 Accepted + Status URL<br/>(Non-blocking response)
        
        Note over Orchestrator, CosmosDB: 📋 Phase 2: Orchestration Logic
        
        loop For each snippet
            Orchestrator->>Orchestrator: 🔪 Chunk code into 800-char pieces<br/>chunks = [text[i:i+800] for i in range(...)]
            
            Note over Orchestrator, EmbedActivity: 📋 Phase 3: Fan-Out Pattern
            
            par Parallel Embedding Generation
                Orchestrator->>+EmbedActivity: 🎯 Task 1: embed_chunk(chunk[0])
                EmbedActivity->>+OpenAI: 🧠 Generate embedding<br/>model: text-embedding-3-small
                OpenAI-->>-EmbedActivity: 📊 Vector[1536] (float array)
                EmbedActivity-->>-Orchestrator: ✅ embedding_1
            and
                Orchestrator->>+EmbedActivity: 🎯 Task 2: embed_chunk(chunk[1])
                EmbedActivity->>+OpenAI: 🧠 Generate embedding
                OpenAI-->>-EmbedActivity: 📊 Vector[1536]
                EmbedActivity-->>-Orchestrator: ✅ embedding_2
            and
                Orchestrator->>+EmbedActivity: 🎯 Task N: embed_chunk(chunk[N])
                EmbedActivity->>+OpenAI: 🧠 Generate embedding
                OpenAI-->>-EmbedActivity: 📊 Vector[1536]
                EmbedActivity-->>-Orchestrator: ✅ embedding_N
            end
            
            Note over Orchestrator, PersistActivity: 📋 Phase 4: Fan-In & Aggregation
            
            Orchestrator->>Orchestrator: 🧮 Aggregate embeddings<br/>avg = [sum(vectors[i])/count for i in dim]
            
            Orchestrator->>+PersistActivity: 💾 persist_snippet_activity<br/>({name, code, embedding[], language})
            PersistActivity->>+CosmosDB: 🗄️ cosmos_ops.upsert_document()<br/>(with vector index)
            CosmosDB-->>-PersistActivity: ✅ Document saved
            PersistActivity-->>-Orchestrator: ✅ {ok: true, id: "..."}
        end
        
        Orchestrator-->>-Starter: 🎉 Orchestration Complete<br/>All snippets processed
    else Input Invalid
        Starter-->>Client: ❌ 400 Bad Request<br/>{"error": "Invalid input"}
    end

    Note over Client, CosmosDB: 📋 Phase 5: Status Monitoring (Optional)
    
    opt Status Checking
        Client->>Starter: GET {statusUrl}<br/>Check orchestration progress
        Starter-->>Client: 📊 Status Response<br/>{runtimeStatus: "Completed"}
    end

    Note over Client, CosmosDB: 📋 Result: Code snippets are now searchable via vector similarity! 🔍
```

## 🏗️ **Component Responsibilities**

| Swimlane | Component | Responsibility | Technology |
|----------|-----------|----------------|------------|
| 🌐 | **HTTP Client** | Initiates requests, monitors status | REST API calls |
| 🚀 | **HTTP Starter** | Validates input, starts orchestration | Azure Functions HTTP trigger |
| 🎭 | **Orchestrator** | Coordinates workflow, manages fan-out/fan-in | Durable Functions (sync) |
| ⚡ | **Embed Activity** | Generates embeddings for text chunks | Azure Functions Activity (async) |
| 💾 | **Persist Activity** | Saves processed data to database | Azure Functions Activity (async) |
| 🧠 | **Azure OpenAI** | Converts text to vector embeddings | AI/ML Service |
| 🗄️ | **Cosmos DB** | Stores snippets with vector search capability | NoSQL Database |

## 🔄 **Data Flow Transformation**

```mermaid
graph LR
    A[📝 Raw Code Snippet] --> B[🔪 Text Chunks<br/>800 chars each]
    B --> C[🧠 Individual Embeddings<br/>Vector[1536] each]
    C --> D[🧮 Aggregated Embedding<br/>Mean Vector[1536]]
    D --> E[💾 Stored Document<br/>Code + Vector + Metadata]
    E --> F[🔍 Searchable via<br/>Vector Similarity]
```

## ⚡ **Key Benefits of This Architecture**

1. **🔄 Scalability**: Parallel processing of multiple chunks
2. **🛡️ Reliability**: Durable Functions handle failures gracefully
3. **📊 Monitoring**: Built-in status tracking and replay safety
4. **🚀 Performance**: Non-blocking responses with async operations
5. **🔍 Searchability**: Vector embeddings enable semantic search

## ⚠️ **Current Issue to Fix**

```python
def validate_input(input: dict) -> bool:
    """Validate the input JSON for the orchestration."""
    return False  # ❌ This breaks all requests!
```

**Should be:**
```python
def validate_input(input: dict) -> bool:
    """Validate the input JSON for the orchestration."""
    if not input or not isinstance(input, dict):
        return False
    
    snippets = input.get("snippets", [])
    if not isinstance(snippets, list) or not snippets:
        return False
        
    # Validate each snippet has required fields
    for snippet in snippets:
        if not isinstance(snippet, dict):
            return False
        if not snippet.get("name") or not snippet.get("code"):
            return False
            
    return True  # ✅ Valid input
```
