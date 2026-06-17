from langchain.tools import tool
from database_service.service import DatabaseService
from langchain.tools import ToolRuntime
from langchain_core.runnables import RunnableConfig
from agent_service.agent_models import BaseContext

@tool(description='This tool can retrieve user information from vector database using "User" collection')
async def get_user_data(runtime: ToolRuntime[BaseContext], config: RunnableConfig):
    """
    Retrieve user information from the vector database using the "User" collection.

    Performs a email matching search against the "User" collection
    and returns the user records matching the provided queries.

    Returns:
        list[dict] | Any: A list of matching user records retrieved from the
                          vector database. Each record may be returned as a
                          dictionary or JSON-serializable object depending on
                          the DatabaseService implementation.

    Example:
        >>> results = await get_user_data(["John Doe", "john@example.com"])
    """
    print(f'Calling get_user_data. params: {runtime.context}')
    user_email = runtime.context and runtime.context.user_email
    if user_email is None: return 'Could not find user for this session!'
    database_service = DatabaseService('User')
    return await database_service.aget({'id': {'$eq': user_email}})


@tool(description='This tool can upsert user information in vector database using "User" collection')
async def upsert_user_data(data: str, runtime: ToolRuntime[BaseContext], config: RunnableConfig):
    """
    Insert or update user information in the vector database using the "User" collection.

    Performs an upsert operation on the "User" collection — inserting the record
    if it does not exist, or updating it if a matching entry is found. The data
    is vectorized and stored for future semantic retrieval.

    Args:
        data (str): A string or JSON string representing the user data to upsert.
                    When passing structured data, serialize it as a JSON string.
                    Example (plain):      "John Doe, age 30, role admin"
                    Example (JSON):       '{"id": "123", "name": "John Doe", "email": "john@example.com", "role": "admin"}'

    Returns:
        dict | Any: The result of the upsert operation as returned by the
                    DatabaseService, typically confirming the upserted record
                    or its identifier.

    Example:
        >>> result = await upsert_user_data('{"id": "u_001", "name": "Jane Doe", "email": "jane@example.com"}')
        >>> result = await upsert_user_data("Jane Doe, software engineer, active user")
    """
    print(f'Calling upsert_user_data. params: {data}, {runtime.context}')
    user_email = runtime.context and runtime.context.user_email
    if user_email is None: return 'Could not find user for this session!'
    database_service = DatabaseService('User')
    return await database_service.acreate_one(data, user_email)

@tool(description='This tool can delete user information in vector database using "User" collection')
async def delete_user_data(id, runtime: ToolRuntime):
    """
    Delete user information in the vector database using the "User" collection.

    Performs an delete operation on the "User" collection — deleting the record

    Args:
        id (str): id of the record to be deleted

    Returns:
        dict | Any: The result of the upsert operation as returned by the
                    DatabaseService, typically confirming the upserted record
                    or its identifier.

    Example:
        >>> result = await delete_user_data(123)
        >>> result = await delete_user_data(1234)
    """
    print(f'Calling delete_user_data. params: {id}')
    user_email = runtime.context and runtime.context.user_email
    if user_email is None: return 'Could not find user for this session!'
    database_service = DatabaseService('User')
    return await database_service.adelete_one(id)