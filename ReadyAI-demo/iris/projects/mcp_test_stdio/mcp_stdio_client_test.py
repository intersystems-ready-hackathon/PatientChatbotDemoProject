import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_iris_mcp():
    server_params = StdioServerParameters(
        command="iris-mcp-server",
        args=["--config", "./config-stdio.toml","run" ],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Test Echo
            result = await session.call_tool("mcp_readyai_basic_ListPatientsBySurname", {"surname": "Larson"})
            print(f"ListPatientsBySurname result: {result}")

asyncio.run(test_iris_mcp())