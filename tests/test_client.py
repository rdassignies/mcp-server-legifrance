import pytest
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

TOOL_NAMES = {
    "rechercher_dans_texte_legal",
    "rechercher_code",
    "rechercher_jurisprudence_judiciaire",
}

@pytest.mark.asyncio
async def test_server_returns_three_tools(server):
    mcp_url = f"{server['url']}/mcp/"
    async with streamablehttp_client(url=mcp_url) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            await session.send_ping()
            tools = await session.list_tools()
            assert {t.name for t in tools.tools} == TOOL_NAMES

@pytest.mark.asyncio
async def test_ping_endpoint(server):
    """Test that the ping endpoint returns a 200 OK response with the expected JSON payload."""
    # Get the base URL from the server fixture
    base_url = server["url"]
    ping_url = f"{base_url}/ping"

    async with httpx.AsyncClient() as client:
        response = await client.get(ping_url)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
