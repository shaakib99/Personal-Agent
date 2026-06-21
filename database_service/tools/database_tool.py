from langchain.tools import tool, ToolRuntime
from agent_service.agent_models import BaseContext
from database_service.config import CollectionToServiceMap, AllowedCollections, AllowedOps
from typing import Dict, Any


@tool(description='get metadata in json format to perform a CRUD operation in persistent memory')
async def get_metadata_json(collection_name: AllowedCollections, ops: AllowedOps):
    """
    Retrieve metadata schema for a specific collection and operation type.

    This tool MUST be called before performing any CRUD operation (create, update,
    get, delete) to understand the required fields, data types, and constraints
    for the target collection. The returned metadata defines what fields are
    mandatory or optional for the intended operation.

    Args:
        collection_name (AllowedCollections): The name of the target collection
            to retrieve metadata for (e.g., 'users', 'orders').
        ops (AllowedOps): The intended CRUD operation type
            (e.g., 'create', 'update', 'get', 'delete').

    Returns:
        str | dict: A JSON-compatible dictionary describing the collection schema
            and field requirements for the given operation, or an error string
            if the collection name is invalid.

    Example:
        >>> metadata = await get_metadata_json('users', 'create')
        >>> # Returns field definitions to guide the create_new_record call
    """
    print(f'calling get_metadata_json {collection_name}, {ops}')
    try:
        service = CollectionToServiceMap.get(collection_name, None)
        if service is None:
            return f'{collection_name} is not a valid collection'
        return await service().get_metadata_json(ops)
    except Exception as e: 
        return f'[Error] {e.__str__()}.'



@tool(description='save data into persistent memory for a collection')
async def create_new_record(collection_name: AllowedCollections, data: Dict[str, Any]):
    """
    Insert a new record into the specified collection in persistent memory.

    Before calling this tool, always invoke `get_metadata_json` with ops='create'
    to determine the required and optional fields for the target collection.
    The `data` payload must conform to the schema returned by that metadata call.

    Args:
        collection_name (AllowedCollections): The name of the target collection
            where the new record will be inserted (e.g., 'users', 'orders').
        data (Dict[str, Any]): A dictionary containing the fields and values
            for the new record. Field requirements are defined by the collection
            metadata — call `get_metadata_json(collection_name, 'create')` first.

    Returns:
        str | dict: The created record or a confirmation response on success,
            or an error string if the collection name is invalid.

    Example:
        >>> record = await create_new_record('users', {'name': 'Alice', 'email': 'alice@example.com'})
    """
    print(f'calling create_new_record {collection_name}, {data}')
    try:
        service = CollectionToServiceMap.get(collection_name, None)
        if service is None:
            return f'{collection_name} is not a valid collection'
        return await service().acreate_one(data)
    except Exception as e: 
        print(f'[Error] {e.__str__()}. Try calling get_metadata_json first?')
        return f'[Error] {e.__str__()}. Try calling get_metadata_json first?'



@tool(description='update data into persistent memory for a collection')
async def update_one_record(collection_name: AllowedCollections, data: Dict[str, Any]):
    """
    Modify an existing record in the specified collection in persistent memory.

    Before calling this tool, always invoke `get_metadata_json` with ops='update'
    to determine which fields are required (e.g., a record identifier) and which
    are updatable for the target collection. Only provide the fields that need
    to be changed alongside any required identifier fields.

    Args:
        collection_name (AllowedCollections): The name of the target collection
            containing the record to update (e.g., 'users', 'orders').
        data (Dict[str, Any]): A dictionary containing the identifier of the
            record to update along with the fields and new values to apply.
            Field requirements are defined by the collection metadata —
            call `get_metadata_json(collection_name, 'update')` first.

    Returns:
        str | dict: The updated record or a confirmation response on success,
            or an error string if the collection name is invalid.

    Example:
        >>> result = await update_record('users', {'id': '123', 'email': 'newemail@example.com'})
    """
    print(f'calling update_one_record {collection_name}, {data}')
    try:
        service = CollectionToServiceMap.get(collection_name, None)
        if service is None:
            return f'{collection_name} is not a valid collection'
        return await service().aupdate_one(data)
    except Exception as e: 
        return f'[Error] {e.__str__()}. Try calling get_metadata_json first?'


# database_tool.py
@tool(description='get records data from persistent memory of a collection')
async def get_records(collection_name: AllowedCollections, params: Dict[str, Any]):
    """
    Fetch multiple/single records from the specified collection using filter parameters.

    Before calling this tool, invoke `get_metadata_json` with ops='get' to
    understand the filterable fields for the target collection.

    IMPORTANT - cross-collection lookups:
        Some collections filter by a related collection's id, NOT by email or
        other user-facing fields. For example, querying 'preference' requires
        a 'user_id' which is the id from the 'user' collection. If you only
        have an email, first call get_records on 'user' filtered by email to
        resolve the id, then use that id as the filter value.

    Args:
        collection_name (AllowedCollections): The name of the target collection.
        params (Dict[str, Any]): Must follow the shape:
            {
                "text": "<semantic search string, or empty string>",
                "filter": { "<field>": "<value>" }
            }
            Call get_metadata_json(collection_name, 'get') first to know
            which filter fields are valid for the collection.

    Returns:
        str | list: A list of matching records on success,
            or an error string if the collection name is invalid.
    """
    print(f'calling get_records {collection_name}, {params}')
    try:
        service = CollectionToServiceMap.get(collection_name, None)
        if service is None:
            return f'{collection_name} is not a valid collection'
        result = await service().aget(params)
        print(f'result from get_records {result}')
        return result
    except Exception as e: 
        return f'[Error] {e.__str__()}. Try calling get_metadata_json first?'


@tool(description='delete a single record from persistent memory of a collection')
async def delete_one_record(collection_name: AllowedCollections, id: str):
    """
    Permanently remove a single record by its unique identifier from the specified collection.

    Before calling this tool, invoke `get_metadata_json` with ops='delete' to confirm
    the identifier field name, format, and any constraints or side effects associated
    with deletion in the target collection. This action is irreversible.

    Args:
        collection_name (AllowedCollections): The name of the target collection
            from which the record will be deleted (e.g., 'users', 'orders').
        id (str): The unique identifier of the record to delete. Refer to
            the collection metadata for the expected ID format and field name.

    Returns:
        str | dict: A confirmation response or the deleted record on success,
            or an error string if the collection name is invalid or the
            record is not found.

    Example:
        >>> result = await delete_one_records('users', '64f1a2b3c4d5e6f7a8b9c0d1')
    """
    print(f'calling delete_one_record {collection_name}, {id}')
    try:
        service = CollectionToServiceMap.get(collection_name, None)
        if service is None:
            return f'{collection_name} is not a valid collection'
        return await service().adelete_one(id)
    except Exception as e: 
        return f'[Error] {e.__str__()}. Try calling get_metadata_json first?'


@tool(description='get basic information about the current user. for detail lookup, call needed to persistent storage')
async def get_basic_information_of_current_user(runtime: ToolRuntime[BaseContext]):
    '''
    Returns basic information like email from context
    '''
    print(f'calling get_basic_information_of_current_user')
    user_email = runtime.context and runtime.context.user_email
    if user_email is None: return f'[ERROR] could not found details about current user'
    return {
        'email': user_email
    }   