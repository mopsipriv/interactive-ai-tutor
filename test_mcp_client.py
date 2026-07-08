import asyncio
from fastmcp import Client

async def test():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        result = await client.call_tool("get_students_tool", {})
        print(result)

asyncio.run(test())