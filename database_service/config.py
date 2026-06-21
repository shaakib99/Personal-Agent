from typing import Literal, Dict, Any
from database_service.user_service import UserService
from database_service.preference_service import PreferenceService
from database_service.interest_service import InterestService
from database_service.conversation_service import ConversationService

AllowedCollections = Literal['user', 'preference', 'interest', 'conversation'] #'preferences', 'products']
AllowedOps = Literal['create', 'update', 'get']
CollectionToServiceMap: Dict[str, Any] = {
    'user': UserService,
    'preference': PreferenceService,
    'interest': InterestService,
    'conversation': ConversationService
}