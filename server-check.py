import asyncio

from fastmcp import Client


async def main():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        tools = await client.list_tools()

        print("Connected to the MCP server successfully!")
        print("Available tools:", [tool.name for tool in tools])


if __name__ == "__main__":
    asyncio.run(main())