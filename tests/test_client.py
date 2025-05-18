import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

TOOL_NAMES = {
    "rechercher_dans_texte_legal",
    "rechercher_code",
    "rechercher_jurisprudence_judiciaire",
}


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_server_returns_three_tools(server):
    """
    Ensure the mcp server returns exactly the expected three tools.
    """
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await session.send_ping()
            tools = await session.list_tools()
            assert len(tools.tools) == 3
