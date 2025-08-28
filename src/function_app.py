# =============================================================================
#
# This application demonstrates a modern AI-powered code snippet manager built with:
#
# 1. Azure Functions - Serverless compute that runs your code in the cloud
#    - HTTP triggers - Standard RESTful API endpoints accessible over HTTP
#    - MCP triggers - Model Context Protocol for AI agent integration (e.g., GitHub Copilot)
#
# 2. Azure Cosmos DB - NoSQL database with vector search capability
#    - Stores code snippets and their vector embeddings
#    - Enables semantic search through vector similarity
#
# 3. Azure OpenAI - Provides AI models and embeddings
#    - Generates vector embeddings from code snippets
#    - These embeddings capture the semantic meaning of the code
#
# 4. Azure AI Agents - Specialized AI agents for code analysis
#    - For generating documentation and style guides from snippets
#
# The application provides two parallel interfaces for the same functionality:
# - HTTP endpoints for traditional API access
# - MCP tools for AI assistant integration

import json
import logging
import azure.functions as func
from datetime import datetime, timezone

app = func.FunctionApp()

# Register blueprints with enhanced error handling to prevent startup issues

# Core snippy functionality
try:
    from functions import bp_snippy
    app.register_blueprint(bp_snippy.bp)
    logging.info("✅ Snippy blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Snippy blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Snippy blueprint registration failed: {e}")

# Query functionality  
try:
    from routes import query
    app.register_blueprint(query.bp)
    logging.info("✅ Query blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Query blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Query blueprint registration failed: {e}")

# Embeddings functionality - now enabled for Level 2
try:
    from functions import bp_embeddings
    app.register_blueprint(bp_embeddings.bp)
    logging.info("✅ Embeddings blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Embeddings blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Embeddings blueprint registration failed: {e}")

# Ingestion functionality - blob trigger for Level 4
try:
    from functions import bp_ingestion
    app.register_blueprint(bp_ingestion.bp)
    logging.info("✅ Ingestion blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Ingestion blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Ingestion blueprint registration failed: {e}")

# Multi-agent functionality
try:
    from functions import bp_multi_agent
    app.register_blueprint(bp_multi_agent.bp)
    logging.info("✅ Multi-agent blueprint registered successfully")
except ImportError as e:
    logging.error(f"❌ Import error for Multi-agent blueprint: {e}")
except Exception as e:
    logging.error(f"❌ Multi-agent blueprint registration failed: {e}")


# =============================================================================
# HEALTH CHECK FUNCTIONALITY
# =============================================================================

# HTTP endpoint for health check
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def http_health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        JSON response with status "ok" and 200 status code
    """
    try:
        logging.info("Health check endpoint called")
        return func.HttpResponse(
            body=json.dumps({"status": "ok"}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in health check: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )


# HTTP endpoint for health check
@app.route(route="health_extended", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def http_health_check_extended(req: func.HttpRequest) -> func.HttpResponse:
    """
    Extended health check endpoint to verify connections to external services.
    
    Verifies:
    - Azure Storage connection and INGESTION_CONTAINER accessibility
    - Cosmos DB connection and database/container accessibility
    
    Returns:
        JSON response with detailed status information
    """
    logging.info("Extended Health check endpoint called")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    # Check Azure Storage connection
    storage_status = await _check_storage_connection()
    health_status["services"]["storage"] = storage_status
    
    # Check Cosmos DB connection
    cosmos_status = await _check_cosmos_connection()
    health_status["services"]["cosmos"] = cosmos_status
    
    # Determine overall health status
    all_healthy = all(
        service_status.get("healthy", False) 
        for service_status in health_status["services"].values()
    )
    
    if not all_healthy:
        health_status["status"] = "degraded"
        status_code = 503  # Service Unavailable
    else:
        status_code = 200
    
    return func.HttpResponse(
        body=json.dumps(health_status),
        mimetype="application/json",
        status_code=status_code
    )


async def _check_storage_connection() -> dict:
    """
    Check Azure Storage connection and INGESTION_CONTAINER accessibility.
    
    Returns:
        Dictionary with storage health status
    """
    try:
        from azure.storage.blob.aio import BlobServiceClient
        import os
        
        # Get connection string and container name from environment
        connection_string = os.environ.get("AzureWebJobsStorage")
        container_name = os.environ.get("INGESTION_CONTAINER", "snippet-inputs")
        
        if not connection_string:
            return {
                "healthy": False,
                "error": "AzureWebJobsStorage environment variable not found"
            }
        
        # Create async blob service client
        async with BlobServiceClient.from_connection_string(connection_string) as blob_client:
            # Check if container exists and is accessible
            container_client = blob_client.get_container_client(container_name)
            
            # This will raise an exception if container doesn't exist or is inaccessible
            container_properties = await container_client.get_container_properties()
            
            logging.info(f"Storage health check: Container '{container_name}' is accessible")
            
            return {
                "healthy": True,
                "container": container_name,
                "last_modified": container_properties.last_modified.isoformat() if container_properties.last_modified else None
            }
            
    except Exception as e:
        logging.error(f"Storage health check failed: {str(e)}")
        return {
            "healthy": False,
            "error": str(e)
        }


async def _check_cosmos_connection() -> dict:
    """
    Check Cosmos DB connection and database/container accessibility.
    
    Returns:
        Dictionary with Cosmos DB health status
    """
    try:
        from data import cosmos_ops
        
        # Test getting the container (this will create client, database, and container if needed)
        container = await cosmos_ops.get_container()
        
        # Perform a simple read operation to verify connection
        container_properties = await container.read()
        
        logging.info(f"Cosmos health check: Database '{cosmos_ops.COSMOS_DATABASE_NAME}' and container '{cosmos_ops.COSMOS_CONTAINER_NAME}' are accessible")
        
        return {
            "healthy": True,
            "database": cosmos_ops.COSMOS_DATABASE_NAME,
            "container": cosmos_ops.COSMOS_CONTAINER_NAME,
            "last_modified": container_properties.get("_ts")
        }
        
    except Exception as e:
        logging.error(f"Cosmos DB health check failed: {str(e)}")
        return {
            "healthy": False,
            "error": str(e)
        }