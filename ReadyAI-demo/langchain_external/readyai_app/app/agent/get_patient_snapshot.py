import asyncio
import base64
import os
from builtins import BaseExceptionGroup

import iris
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallRequest, wrap_tool_call
from langchain.messages import HumanMessage
from langchain_core.messages import ToolMessage
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


def _tool_attr(tool, name: str, default=None):
    if isinstance(tool, dict):
        return tool.get(name, default)
    return getattr(tool, name, default)


def _format_exception(exc: BaseException) -> str:
    if isinstance(exc, BaseExceptionGroup):
        nested_messages = []
        for child in exc.exceptions:
            child_message = _format_exception(child)
            if child_message:
                nested_messages.append(child_message)
        if nested_messages:
            return "; ".join(nested_messages)
    message = str(exc).strip()
    if message:
        return f"{type(exc).__name__}: {message}"
    return type(exc).__name__


@wrap_tool_call
async def _handle_tool_call_error(request: ToolCallRequest, handler):
    try:
        return await handler(request)
    except Exception as exc:
        tool_name = request.tool_call.get("name", "unknown_tool")
        tool_call_id = request.tool_call.get("id", tool_name)
        message = _format_exception(exc)
        return ToolMessage(
            content=(
                f"Tool '{tool_name}' failed with {message}. "
                "Continue without this tool and explain any resulting limitation to the user."
            ),
            name=tool_name,
            tool_call_id=tool_call_id,
            status="error",
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
        return create_agent(
            model=model,
            tools=tools,
            system_prompt=self.SYSTEM_PROMPT,
            middleware=[_handle_tool_call_error],
        )

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
        try:
            tools = await client.get_tools()
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve tools from MCP: {(e)} \n\n Have you started the iris-mcp-server transport?") from e
        return tools

    async def build_tools_access_prompt(self) -> str:
        tools = await self.get_tools()
        tool_lines = []

        for tool in tools:
            name = _tool_attr(tool, "name", "unknown_tool")
            description = _tool_attr(tool, "description", "") or "No description provided."
            tool_lines.append(f"- {name}: {description}")

        available_tools = "\n".join(tool_lines) if tool_lines else "- No tools are currently available."

        return (
            "Tell the signed-in user which tools you can access right now. "
            "Base your answer only on the tool list below. "
            "List the available tools, briefly explain what each tool is for, and mention if access appears limited by role. "
            "Do not invent tools or capabilities beyond this list.\n\n"
            f"Accessible tools:\n{available_tools}"
        )

    async def stream_response(self, prompt: str):
        
        agent = await self.get_snapshot_agent()
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
