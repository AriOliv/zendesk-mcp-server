import asyncio
import os


def main():
    # Imported here rather than at module scope so that `zendesk-auth` does not
    # pull in the MCP server, which logs and loads configuration on import.
    from . import server

    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        server.run_http(
            host=os.environ.get("MCP_HOST", "0.0.0.0"),
            port=int(os.environ.get("MCP_PORT", "8000")),
        )
    elif transport == "stdio":
        asyncio.run(server.main())
    else:
        raise SystemExit(f"Unknown MCP_TRANSPORT {transport!r} (expected 'stdio' or 'http')")


__all__ = ["main"]
