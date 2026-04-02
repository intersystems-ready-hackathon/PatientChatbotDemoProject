import iris
from langchain_intersystems.chat_models import init_chat_model
from langchain_intersystems import init_mcp_client
import pprint
import asyncio

conn = iris.connect('localhost', 1973, 'READYAI', 'DScully', 'xfiles')  # change as needed
model = init_chat_model('gpt-5-nano', conn)
print(model.invoke('Hello, how are you?'))


# client = init_mcp_client(['config-test-remote'], conn)

# pprint.pprint(asyncio.run(client.get_tools()))