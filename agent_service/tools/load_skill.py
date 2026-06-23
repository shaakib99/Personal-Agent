from langchain.tools import tool, ToolRuntime
from agent_service.config import AVAILABLE_SKILLS
from agent_service.agent_models import BaseContext
@tool(description='Loads a skill instruction file and injects it into context. ')
async def load_skill(skill: AVAILABLE_SKILLS, runtime: ToolRuntime[BaseContext]):
    """
    Load a skill file from disk and return its contents for prompt injection.

    Args:
        skill (AVAILABLE_SKILLS): The skill to load.
        runtime (ToolRuntime): Injected automatically by LangChain.

    Returns:
        str: Contents of the skill file.
    """
    print(f'Loading skill: {skill}')
    try:
        with open(f'agent_service/skills/{skill}', 'r') as f:
            return f.read()
    except Exception as e:
        print(f'Could not load skill: {skill}, Error {e.__str__()}')
        return f'Could not load skill: {skill}, Error {e.__str__()}'