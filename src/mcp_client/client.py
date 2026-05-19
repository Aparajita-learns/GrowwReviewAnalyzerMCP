import os
import asyncio
import shlex
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPDeliveryClient:
    """Helper to interact with Google Docs and Gmail MCP servers."""
    
    def __init__(self):
        self.docs_cmd = os.getenv("MCP_DOCS_COMMAND", "npx -y @a-bonus/google-docs-mcp")
        self.gmail_cmd = os.getenv("MCP_GMAIL_COMMAND", "npx -y @a-bonus/google-docs-mcp")

    async def call_tool(self, server_cmd: str, tool_name: str, arguments: dict):
        """Generic method to call a tool on an MCP server."""
        # Strip potential surrounding quotes from the env var
        server_cmd = server_cmd.strip('"').strip("'")
        cmd_parts = shlex.split(server_cmd, posix=False)
        
        # Windows compatibility
        if os.name == 'nt' and cmd_parts[0] == 'npx':
            cmd_parts[0] = 'npx.cmd'
            cmd_parts = ['cmd.exe', '/c'] + cmd_parts
            
        # Configure environment variables for Google MCP servers
        env = os.environ.copy()
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # Set XDG config directory to project root so the server finds google-docs-mcp/token.json
        env["XDG_CONFIG_HOME"] = root_dir
        
        # Set client ID and secret directly in the env so credentials.json is not required by the package
        creds_path = os.path.join(root_dir, "credentials.json")
        if os.path.exists(creds_path):
            try:
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                    key_data = creds_data.get("installed") or creds_data.get("web")
                    if key_data:
                        env["GOOGLE_CLIENT_ID"] = key_data.get("client_id")
                        env["GOOGLE_CLIENT_SECRET"] = key_data.get("client_secret")
            except Exception as e:
                print(f"Error parsing credentials.json for env injection: {e}")
                
        env["GMAIL_CREDENTIALS_PATH"] = os.path.join(root_dir, "credentials.json")
        if os.path.exists(os.path.join(root_dir, "token_gmail.json")):
            env["GMAIL_TOKEN_PATH"] = os.path.join(root_dir, "token_gmail.json")
        else:
            env["GMAIL_TOKEN_PATH"] = os.path.join(root_dir, "token.json")
            
        print(f"Executing MCP Command: {' '.join(cmd_parts)}")
        params = StdioServerParameters(
            command=cmd_parts[0],
            args=cmd_parts[1:],
            env=env
        )
        
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                # Small delay to ensure the subprocess has started on Windows
                await asyncio.sleep(1)
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                
                # Check for tool errors to prevent silent failures
                if hasattr(result, "isError") and result.isError:
                    error_msg = ""
                    if hasattr(result, "content") and result.content:
                        error_msg = " ".join([getattr(c, "text", str(c)) for c in result.content])
                    raise Exception(error_msg or "Unknown MCP tool execution failure")
                    
                # Inspect text content for internal error/success statuses
                if hasattr(result, "content") and result.content:
                    for c in result.content:
                        if hasattr(c, "text"):
                            try:
                                data = json.loads(c.text)
                                if isinstance(data, dict) and data.get("success") is False:
                                    raise Exception(data.get("message") or data.get("error") or "Operation failed")
                            except json.JSONDecodeError:
                                pass
                return result

    async def deliver_to_docs(self, document_id: str, markdown_content: str):
        """Calls the Google Docs MCP server to replace the document with markdown."""
        return await self.call_tool(
            self.docs_cmd,
            "replaceDocumentWithMarkdown",
            {"documentId": document_id, "markdown": markdown_content}
        )

    async def append_markdown_to_docs(self, document_id: str, markdown_content: str):
        """Calls the Google Docs MCP server to append markdown to the document."""
        return await self.call_tool(
            self.docs_cmd,
            "appendMarkdown",
            {"documentId": document_id, "markdown": markdown_content}
        )

    async def insert_image(self, document_id: str, image_uri: str):
        """Inserts an image into the Google Doc."""
        return await self.call_tool(
            self.docs_cmd,
            "insertImage",
            {"documentId": document_id, "imageUrl": image_uri, "index": 1}
        )

    async def send_gmail(self, recipient: str, subject: str, body_html: str):
        """Calls the Gmail MCP server to send an email."""
        return await self.call_tool(
            self.gmail_cmd,
            "sendEmail",
            {
                "to": recipient,
                "subject": subject,
                "body": body_html
            }
        )
