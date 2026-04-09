import asyncio
import base64
import json
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
        seen_tool_calls = {}
        try:
            async for chunk in agent.astream(
                {"messages": [HumanMessage(content=prompt)]},
                stream_mode="messages",
            ):
                message, _ = chunk
                if message.type in ("ai", "AIMessageChunk"):
                    blocks = getattr(message, "content_blocks", []) or []
                    for block in blocks:
                        if block["type"] == "text":
                            yield block["text"]
                        elif block["type"] == "tool_call":
                            tool_name = block.get("name")
                            tool_id = block.get("id") or tool_name
                            if not tool_name or not tool_id:
                                continue

                            tool_args = block.get("args", {})
                            if not isinstance(tool_args, str):
                                tool_args = json.dumps(tool_args, indent=2, sort_keys=True)

                            seen_tool_calls[tool_id] = tool_name
                            yield {
                                "type": "tool_call",
                                "id": tool_id,
                                "name": tool_name,
                                "status": "running",
                                "args": tool_args,
                            }

                    tool_calls = getattr(message, "tool_calls", []) or []
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("name")
                        tool_id = tool_call.get("id") or tool_name
                        if not tool_name or not tool_id or tool_id in seen_tool_calls:
                            continue

                        tool_args = tool_call.get("args", {})
                        if not isinstance(tool_args, str):
                            tool_args = json.dumps(tool_args, indent=2, sort_keys=True)

                        seen_tool_calls[tool_id] = tool_name
                        yield {
                            "type": "tool_call",
                            "id": tool_id,
                            "name": tool_name,
                            "status": "running",
                            "args": tool_args,
                        }

                    tool_call_chunks = getattr(message, "tool_call_chunks", []) or []
                    for tool_call_chunk in tool_call_chunks:
                        tool_name = tool_call_chunk.get("name")
                        tool_id = tool_call_chunk.get("id") or tool_name
                        if not tool_name or not tool_id or tool_id in seen_tool_calls:
                            continue

                        tool_args = tool_call_chunk.get("args", {})
                        if not isinstance(tool_args, str):
                            tool_args = json.dumps(tool_args, indent=2, sort_keys=True)

                        seen_tool_calls[tool_id] = tool_name
                        yield {
                            "type": "tool_call",
                            "id": tool_id,
                            "name": tool_name,
                            "status": "running",
                            "args": tool_args,
                        }
                elif message.type == "tool":
                    tool_id = getattr(message, "tool_call_id", None)
                    tool_name = getattr(message, "name", None) or seen_tool_calls.get(tool_id)
                    if not tool_id or not tool_name:
                        continue

                    tool_content = getattr(message, "content", "")
                    if isinstance(tool_content, list):
                        tool_content = "\n".join(str(item) for item in tool_content)

                    yield {
                        "type": "tool_result",
                        "id": tool_id,
                        "name": tool_name,
                        "status": getattr(message, "status", "completed") or "completed",
                        "content": str(tool_content).strip(),
                    }
        except Exception as e:
            yield f"\n\n Error during agent execution: {e}"


async def main():
    agent = PatientSnapshotAgent("SuperUser", "SYS")
    async for chunk in agent.stream_response("What tools do you have?"):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
