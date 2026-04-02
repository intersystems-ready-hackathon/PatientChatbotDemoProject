import asyncio
import base64
import os

import iris
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_intersystems.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

_IRIS_HOST = os.environ.get("IRIS_HOST", "iris")
_IRIS_PORT = int(os.environ.get("IRIS_PORT", "1972"))
_IRIS_NAMESPACE = os.environ.get("IRIS_NAMESPACE", "READYAI")
_MCP_URL = os.environ.get("MCP_URL", "http://iris:8888/mcp/readyai")
_LLM_CONFIG_NAME = os.environ.get("LLM_CONFIG_NAME", "gpt-5-nano")

SYSTEM_PROMPT = (
    "You have tools to query patient data from the hospital database. "
    "Tool accessibility varies by role: Doctors have access to all tools; Nurses have limited access. "
    "You can use EchoUser to confirm the user's identity and role. The metadata states the required role for each tool"
        "and if a tool is inaccessible due to role restrictions, you should note this in your response. "
)


class PatientSnapshotAgent:

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.SYSTEM_PROMPT = SYSTEM_PROMPT

    def _iris_conn(self):
        return iris.connect(_IRIS_HOST, _IRIS_PORT, _IRIS_NAMESPACE, self.username, self.password)

    async def get_snapshot_agent(self):
        conn = self._iris_conn()
        model = init_chat_model(_LLM_CONFIG_NAME, conn)
        conn.close()

        tools = await self.get_tools()
        return create_agent(model=model, tools=tools, system_prompt=self.SYSTEM_PROMPT)

    async def get_tools(self):
        auth_header = base64.b64encode(
            f"{self.username}:{self.password}".encode("utf-8")
        ).decode("utf-8")
        client = MultiServerMCPClient(
            {
                "readyai": {
                    "transport": "http",
                    "url": _MCP_URL,
                    "headers": {"Authorization": f"Basic {auth_header}"},
                }
            }
        )
        return await client.get_tools()

    async def stream_response(self, prompt: str):
        try:
            agent = await self.get_snapshot_agent()
        except Exception as e:
            yield f"Error initialising agent: {e}"
            return
        try:
            async for chunk in agent.astream(
                {"messages": [HumanMessage(content=prompt)]},
                stream_mode="messages",
            ):
                message, _ = chunk
                if message.type not in ("ai", "AIMessageChunk"):
                    continue
                for block in message.content_blocks:
                    if block["type"] == "text":
                        yield block["text"]
        except Exception as e:
            yield f"\n\n Error during agent execution: {e}"


async def main():
    agent = PatientSnapshotAgent("SuperUser", "SYS")
    async for chunk in agent.stream_response("What tools do you have?"):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
