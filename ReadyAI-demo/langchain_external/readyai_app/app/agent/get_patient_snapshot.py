import asyncio
import base64
import json

import iris
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallRequest, wrap_tool_call
from langchain.messages import HumanMessage, ToolMessage
from langchain_intersystems.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

_IRIS_HOST = "iris"
_IRIS_PORT = 1972
_IRIS_NAMESPACE = "READYAI"
_MCP_URL = "http://iris:8888/mcp/readyai/"
_MCP_HOST_HEADER = "localhost:8888"
_LLM_CONFIG_NAME = "gpt-5-nano"



def _display_tool_name(name: str) -> str:
    displayname = name.split("_")[-1]
    return displayname


@wrap_tool_call
async def _handle_tool_call_error(request: ToolCallRequest, handler):
    """
    Error-handling middleware for tool calls. 
    If a tool call raises an exception, catch it and return a ToolMessage with status "error" and the exception message as content.
    This allows the agent to continue operating even if a tool fails
    """
    try:
        return await handler(request)
    except Exception as exc:
        tool_name = request.tool_call["name"]
        tool_call_id = request.tool_call["id"]
        return ToolMessage(
            content=f"Tool '{tool_name}' failed with {exc}. Continue without this tool and explain any resulting limitation to the user.",
            name=tool_name,
            tool_call_id=tool_call_id,
            status="error",
        )


class PatientSnapshotAgent:
    """
    Agent for retrieving patient snapshots using MCP tools.
    """
    def __init__(self, username: str, password: str):
        """Initialize the agent with credentials for MCP authentication."""

        self.username = username
        self.password = password
        self.SYSTEM_PROMPT = (
            "You have tools to query patient data from the hospital database. "
            "Tool accessibility varies by role: Doctors have access to all tools; Nurses have limited access. "
            "You can use EchoUser to confirm the user's identity and role."
            "and if a tool is inaccessible due to role restrictions, you should note this in your response. "
            "If you have the list tables and query tables tools, try to use them to check observations if the prompt asks for a snapshot"
        )



    async def get_snapshot_agent(self):
        """
        Initialize an agent with a chat model and tools retrieved from the MCP server.
        """

        # Retrieve a chat model from IRIS Config Store (using a short name defined in _LLM_CONFIG_NAME)
        conn = iris.connect(_IRIS_HOST, _IRIS_PORT, _IRIS_NAMESPACE, self.username, self.password)
        try:
            model = init_chat_model(_LLM_CONFIG_NAME, conn)
        finally:
            conn.close()

        tools = await self.get_tools()
        return create_agent(
            model=model,
            tools=tools,
            system_prompt=self.SYSTEM_PROMPT,
            middleware=[_handle_tool_call_error],
        )

    async def get_tools(self):
        """
        Retrieve the list of tools available to this agent from the MCP server.
        Uses basic authentication with the agent's username and password.
        """
        auth_header = base64.b64encode(
            f"{self.username}:{self.password}".encode("utf-8")
        ).decode("utf-8")

        client = MultiServerMCPClient(
            {
                "readyai": {
                    "transport": "http",
                    "url": _MCP_URL,
                    # iris-mcp-server rejects Host: iris:8888 from inside Docker.
                    "headers": {
                        "Authorization": f"Basic {auth_header}",
                        "Host": _MCP_HOST_HEADER,
                    },
                }
            }
        )
        
        try:
            tools = await client.get_tools()
            if self.username=="NJoy":
                tools = [tool for tool in tools if "basic" in tool.name ]
            return tools
        except Exception as exc:
            raise RuntimeError(
                f"Failed to retrieve tools from MCP at {_MCP_URL}: {exc}"
            ) from exc


    async def list_accessible_tools_response(self) -> str:
        tools = await self.get_tools()
        if not tools:
            return "I do not currently have any MCP tools available."

        lines = ["I can currently access these tools:"]
        for tool in sorted(tools, key=lambda t: _display_tool_name(t.name).lower()):
            lines.append(f"- {_display_tool_name(tool.name)}: {tool.description}")
        lines.append("This list is based on the tools currently exposed to your signed-in role.")
        return "\n".join(lines)

    async def stream_response(self, prompt: str):
        yield "Processing your request...\n\n"
        yield prompt + "\n\n"
        if  "What tools do you have?" in prompt[20:]:
            yield await self.list_accessible_tools_response()
            return

        seen_tool_calls = {}
        try:
            agent = await self.get_snapshot_agent()
            async for chunk in agent.astream(
                {"messages": [HumanMessage(content=prompt)]},
                stream_mode="messages",
            ):
                message, _ = chunk

                if message.type in ("ai", "AIMessageChunk"):
                    for block in message.content_blocks:
                        if block["type"] == "text":
                            yield block["text"]
                        elif block["type"] == "tool_call":
                            tool_id = block["id"]
                            tool_name = block["name"]
                            seen_tool_calls[tool_id] = tool_name
                            yield {
                                "type": "tool_call",
                                "id": tool_id,
                                "name": tool_name,
                                "status": "running",
                                "args": json.dumps(block["args"], indent=2, sort_keys=True),
                            }

                elif message.type == "tool":
                    tool_id = message.tool_call_id
                    yield {
                        "type": "tool_result",
                        "id": tool_id,
                        "name": seen_tool_calls.get(tool_id, message.name),
                        "status": message.status or "completed",
                        "content": message.content,
                    }

        except Exception as e:
            yield f"\n\nError during agent execution: {e}"


async def main():
    agent = PatientSnapshotAgent("SuperUser", "SYS")
    async for chunk in agent.stream_response("What tools do you have?"):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
