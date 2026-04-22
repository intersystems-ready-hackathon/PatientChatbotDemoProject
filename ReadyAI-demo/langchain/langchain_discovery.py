import asyncio
import os
import base64

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# auth = "NJoy:pokemon"
# 

auth = "DScully:xfiles"
AUTH_HEADER = base64.b64encode(auth.encode("utf-8")).decode("utf-8")


TOOL_PROBES = {
    "mcp_readyai_advanced_ListTables": {},
    "mcp_readyai_advanced_QueryTable": {"patientId": 3, "tableName": "Observation"},
    "mcp_readyai_basic_ListPatientsBySurname": {"surname": "Larson"},
    "mcp_readyai_basic_ListMedications": {"patientId": 3},
}

from langchain_mcp_adapters.client import MultiServerMCPClient

# auth = "SuperUser:SYS"
AUTH_HEADER = base64.b64encode(auth.encode("utf-8")).decode("utf-8")

async def get_tools():
    client = MultiServerMCPClient(
        {
        "readyai": {
            "transport": "http",
            "url": "http://localhost:8888/mcp/readyai/",
            "headers": {"Authorization": f"Basic {AUTH_HEADER}"},
        }
        }
    )
    tools = await client.get_tools()

    print("logged in with " + auth)
    print("using MCP proxy " + "http://localhost:8888/mcp/readyai/")
    print("Available MCP tools:")
    for tool in tools: 
        print("- ", tool.name)
    
    for tool in sorted(tools, key=lambda item: item.name):
        if tool.name == "mcp_readyai_advanced_ListTables":
            try:
                out = await tool.ainvoke(TOOL_PROBES[tool.name])
                print(str(out)[:200])
            except Exception as e:
                print(f"Error invoking {tool.name}: {e}")
        elif tool.name == "mcp_readyai_advanced_QueryTable":
            try:
                out = await tool.ainvoke(TOOL_PROBES[tool.name])
                print(str(out)[:200])  
            except Exception as e:
                print(f"Error invoking {tool.name}: {e}")
        elif tool.name == "mcp_readyai_basic_ListPatientsBySurname":
            try:
                out = await tool.ainvoke(TOOL_PROBES[tool.name])
                print(str(out)[:200])
            except Exception as e:
                print(f"Error invoking {tool.name}: {e}")
        elif tool.name == "mcp_readyai_basic_ListMedications":
            try:
                out = await tool.ainvoke(TOOL_PROBES[tool.name])
                print(str(out)[:200])
            except Exception as e:
                print(f"Error invoking {tool.name}: {e}")



    
    return tools 

async def main():
    tools = await get_tools()
    # print(tools)
    if tools== [] or tools is None:
        print("No tools available. Exiting.")
        return
    # llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
    # agent = create_agent(llm, tools=tools)

    # async for chunk in agent.astream(
    #     {
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": "Can you tell me patient number 25 with the tables in the database?"
    #             }
    #         ]
    #     },
    #     stream_mode="messages",
    # ):
    #     message, metadata = chunk

    #     for block in message.content_blocks:
    #         if block["type"] == "text":
    #             print(block["text"], end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())




