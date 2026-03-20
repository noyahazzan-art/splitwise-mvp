#!/usr/bin/env python3
"""
Splitwise Agent Service - Port 8080
Monitoring and management service for Splitwise MVP.
"""

from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Configuration
SPLITWISE_API_URL = "http://localhost:8001"

app = FastAPI(
    title="Splitwise Agent Service",
    description="Monitoring & Management Agent for Splitwise MVP",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    splitwise_api: str
    services: dict


class SystemInfo(BaseModel):
    service: str
    port: int
    status: str
    uptime: str


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Agent dashboard with system overview."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Splitwise Agent - Port 8080</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white min-h-screen p-6">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold text-cyan-400 mb-6">🤖 Splitwise Agent Service</h1>
            <div class="bg-slate-800 rounded-lg p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">System Status</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-slate-700 p-4 rounded">
                        <h3 class="text-cyan-300 font-semibold">Agent Service</h3>
                        <p class="text-green-400">✅ Running on port 8080</p>
                    </div>
                    <div class="bg-slate-700 p-4 rounded">
                        <h3 class="text-cyan-300 font-semibold">Splitwise API</h3>
                        <p id="api-status" class="text-yellow-400">🔄 Checking...</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-slate-800 rounded-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
                <div class="space-y-3">
                    <button onclick="checkHealth()" class="bg-cyan-600 hover:bg-cyan-700 px-4 py-2 rounded">
                        🔄 Health Check
                    </button>
                    <button onclick="window.open('http://localhost:8001/docs', '_blank')" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
                        📚 API Documentation
                    </button>
                    <button onclick="window.open('http://localhost:8001/dashboard', '_blank')" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">
                        📊 Splitwise Dashboard
                    </button>
                </div>
            </div>
            
            <div class="mt-6 text-center text-slate-400">
                <p>Agent Service - Port 8080 | Monitoring Splitwise MVP on Port 8001</p>
            </div>
        </div>
        
        <script>
            async function checkHealth() {
                const statusEl = document.getElementById('api-status');
                statusEl.innerHTML = '🔄 Checking...';
                statusEl.className = 'text-yellow-400';
                
                try {
                    const response = await fetch('http://localhost:8001/api');
                    if (response.ok) {
                        statusEl.innerHTML = '✅ Online';
                        statusEl.className = 'text-green-400';
                    } else {
                        statusEl.innerHTML = '❌ Error';
                        statusEl.className = 'text-red-400';
                    }
                } catch (error) {
                    statusEl.innerHTML = '❌ Offline';
                    statusEl.className = 'text-red-400';
                }
            }
            
            // Auto-check on load
            checkHealth();
            // Check every 30 seconds
            setInterval(checkHealth, 30000);
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Comprehensive health check of all services."""
    try:
        # Check Splitwise API
        async with httpx.AsyncClient() as client:
            splitwise_response = await client.get(f"{SPLITWISE_API_URL}/api", timeout=5.0)
            splitwise_status = "online" if splitwise_response.status_code == 200 else "error"
    except Exception:
        splitwise_status = "offline"

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        splitwise_api=splitwise_status,
        services={
            "agent": {"port": 8080, "status": "online"},
            "splitwise_api": {"port": 8001, "status": splitwise_status},
            "splitwise_docs": {"port": 8001, "path": "/docs", "status": splitwise_status},
            "splitwise_dashboard": {"port": 8001, "path": "/dashboard", "status": splitwise_status}
        }
    )


@app.get("/status")
async def status():
    """Simple status endpoint."""
    return {
        "service": "Splitwise Agent",
        "port": 8080,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/services")
async def list_services():
    """List all available services and their endpoints."""
    return {
        "agent": {
            "url": "http://localhost:8080",
            "description": "Monitoring & Management Agent",
            "endpoints": [
                {"path": "/", "description": "Dashboard"},
                {"path": "/health", "description": "Health Check"},
                {"path": "/status", "description": "Service Status"},
                {"path": "/services", "description": "Service List"}
            ]
        },
        "splitwise": {
            "url": "http://localhost:8001",
            "description": "Splitwise MVP API",
            "endpoints": [
                {"path": "/", "description": "API Root"},
                {"path": "/docs", "description": "API Documentation"},
                {"path": "/dashboard", "description": "Web Dashboard"},
                {"path": "/users/", "description": "User Management"},
                {"path": "/groups/", "description": "Group Management"},
                {"path": "/expenses/", "description": "Expense Tracking"},
                {"path": "/balance/", "description": "Balance & Settlements"}
            ]
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("🤖 Starting Splitwise Agent Service on port 8080...")
    print("📊 Dashboard: http://localhost:8080")
    print("🔍 Health Check: http://localhost:8080/health")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
