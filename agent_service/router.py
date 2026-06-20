from fastapi import APIRouter, UploadFile, Form, File
from agent_service.agent_models import ChatModel, ResumeChatModel
from agent_service.service import AgentServiceSingleton
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.documents import Document
import uuid
from pathlib import Path
import aiofiles
import asyncio

router = APIRouter(prefix='/chat', tags=['chat', 'resume'])

@router.post('')
async def chat(data: str = Form(...), files: list[UploadFile] = File(default=[])):
    parsed_data = ChatModel.model_validate_json(data)
    file_content = ''
    skill_content = ''
    for f in files:
        file_path = await _save_upload(f)
        doc_loader = UnstructuredFileLoader(file_path)
        content = doc_loader.load()
        await _remove_saved_file(file_path)
        file_content += f'''
        <uploaded_file>
            <file_name>{f.filename}</file_name>
            <file_size>{f.size}</file_size>
            <file_content>{content}</file_content>
            <note>This file has already been read and its full content is provided above. 
            DO NOT call any file reading tools for this file.</note>
        </uploaded_file>\n'''
    
    for skill in parsed_data.skills:
        skill_content += f'''
            <skill>
                <name>{skill.name}</name>
                <description>{skill.description}</description>
                <note>This skill has been added by the user. Act accordingly</note>
            </skill>\n'''
        

    parsed_data.query = file_content + skill_content +  f"User's Query: {parsed_data.query}"
    agent_service = await AgentServiceSingleton.get_instance()
    async for chunk in agent_service.chat(parsed_data):
        yield chunk

@router.post('/resume')
async def resume(data: str = Form(...)):
    parsed_data = ResumeChatModel.model_validate_json(data)
    agent_service = await AgentServiceSingleton.get_instance()
    async for chunk in agent_service.resume(parsed_data):
        yield chunk


# ----------------------------------------------------------------------
# Helper: store an uploaded file to a temporary location
# ----------------------------------------------------------------------
UPLOAD_ROOT = Path("./tmp/chat_uploads")          # <-- change to a safe directory for your app
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

async def _save_upload(file: UploadFile) -> Path:
    """Write a single UploadFile to disk and return the absolute Path."""
    suffix = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest_path = UPLOAD_ROOT / unique_name

    async with aiofiles.open(dest_path, "wb") as out_f:
        while chunk := await file.read(1024 * 1024):  # 1 MiB per chunk
            await out_f.write(chunk)

    return dest_path

async def _remove_saved_file(path: Path) -> None:
    """Remove a file from disk asynchronously."""
    try:
        await asyncio.to_thread(path.unlink)
    except FileNotFoundError:
        pass  # already gone, no problem