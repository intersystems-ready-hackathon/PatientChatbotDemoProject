import asyncio
import os
import base64
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# AUTH_HEADER = base64.b64encode(b"SuperUser:SYS").decode("utf-8")
AUTH_HEADER = base64.b64encode(b"DScully:xfiles").decode("utf-8")
# AUTH_HEADER = base64.b64encode(b"NJoy:pokemon").decode("utf-8")

async def get_tools():
    client = MultiServerMCPClient(
        {
            "minimal": {
                "transport": "http",
                "url": "http://localhost:8888/mcp/readyai",
                "headers": {"Authorization": f"Basic {AUTH_HEADER}"},
            }
        }
    )

    tools = await client.get_tools()
    for tool in tools: 
        print("- ", tool, "\n")
    print("Available MCP tools:")
    
    for tool in sorted(tools, key=lambda item: item.name):
        if tool.name == "mcp_readyai_EchoUser":
            try:
                out = await tool.ainvoke({})
                print(out)
            except Exception as e:
                print(f"Error invoking {tool.name}: {e}")
        elif tool.name == "mcp_readyai_ListTables":
            try:
                out = await tool.ainvoke({})
                print(out)
            except Exception as e:
                print(f"Error invoking {tool.name}: {e}")
        
        elif tool.name == "mcp_readyai_QueryTable":
            try:
                out = await tool.ainvoke({"patientId": 3, "tableName": "Observation"})
                print(out)  
            except Exception as e:
                print(f"Error invoking {tool.name}: {e}")

        #     print(out)
        print(f"- {tool.name}")

    
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




