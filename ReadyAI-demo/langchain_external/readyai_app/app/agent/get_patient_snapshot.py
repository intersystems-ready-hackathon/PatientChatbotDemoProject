import langchain_intersystems
from langchain_intersystems.chat_models import init_chat_model
import iris
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.messages import HumanMessage
import base64
import asyncio


class PatientSnapshotAgent:

    def __init__(self, username, password):

        self.username = username
        self.password = password
        self.SYSTEM_PROMPT = """
        You are a helpful medical assistant designed to generate concise patient snapshots for doctors and nurses
        You have tools to query patient data from the hospital database. 
        
        The accessibility level of each of the tools will vary based on the role of the user (Doctor or Nurse). Doctors have access to all tools, while Nurses have limited access.

        When a tool request returns an Unauthorised or forbidden error, continue, but mention in your final response that you were not able to access these tools.
        """



    async def get_snapshot_agent(self):
        conn = iris.connect('localhost', 1973, 'READYAI', self.username, self.password)
        model = init_chat_model('openai', conn)

        tools = await self.get_tools()
        agent=create_agent(
            model=model,
            tools= tools,
            system_prompt=self.SYSTEM_PROMPT
        )


        return agent

    async def get_tools(self):
        auth_header = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("utf-8")
        client = MultiServerMCPClient(
            {
                "minimal": {
                    "transport": "http",
                    "url": "http://localhost:8888/mcp/readyai",
                    "headers": {"Authorization": f"Basic {auth_header}"},
                }
            }
        )

        tools = await client.get_tools()
        for tool in tools: 
            print("- ", tool, "\n")        
        return tools 


    async def stream_response(self, prompt):
        agent = await self.get_snapshot_agent()
        

        async for chunk in agent.astream(
                                        {"messages":[HumanMessage(content=prompt)]},
                                        stream_mode="messages",
                                        ):
            message, metadata = chunk

            for block in message.content_blocks:
                if block["type"] == "text":
                    yield(block["text"])
    
        return 



async def main():
    agent = PatientSnapshotAgent("SUPERUSER", "SYS")
    async for chunk in agent.stream_response("What tools do you have?"):
        print(chunk, end="", flush=True)

if __name__ == "__main__":

    asyncio.run(main())