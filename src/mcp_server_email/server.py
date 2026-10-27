from fastmcp import FastMCP

from mcp_server_email.config import Settings
from mcp_server_email.tools.drafts import create_draft,send_email

mcp = FastMCP("Vyzno Mail", mask_error_details=True)

mcp.add_tool(create_draft)
mcp.add_tool(send_email)

if __name__ == "__main__":
    settings = Settings()

    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )