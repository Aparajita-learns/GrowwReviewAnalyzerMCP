import asyncio
import os
import shlex
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

async def list_tools():
    server_cmd = os.getenv("MCP_DOCS_COMMAND", "npx -y @a-bonus/google-docs-mcp")
    server_cmd = server_cmd.strip('"').strip("'")
    cmd_parts = shlex.split(server_cmd, posix=False)
    
    if os.name == 'nt' and cmd_parts[0] == 'npx':
        cmd_parts[0] = 'npx.cmd'
        cmd_parts = ['cmd.exe', '/c'] + cmd_parts

    print(f"Connecting to: {' '.join(cmd_parts)}")
    
    params = StdioServerParameters(
        command=cmd_parts[0],
        args=cmd_parts[1:],
        env=os.environ.copy()
    )
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("\nAvailable Tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

if __name__ == "__main__":
    asyncio.run(list_tools())
