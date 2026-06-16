from langchain_mcp_adapters.client import MultiServerMCPClient

async def get_mcp_tools():
    client = MultiServerMCPClient({
        'search_tool': {
            'transport': 'http',
            'url': 'http://localhost:8001/mcp'
        }
    })

    return await client.get_tools()

async def check_mcp():
    client = MultiServerMCPClient({
        'local_tools': {
            'transport': 'http',
            'url': 'http://localhost:8001/mcp'
        }
    })

    return await client.get_tools()