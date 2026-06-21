from typing import Literal, Dict, Any
from database_service.user_service import UserService
from database_service.preference_service import PreferenceService

AllowedCollections = Literal['user', 'preference'] #'preferences', 'interests', 'products']
AllowedOps = Literal['create', 'update', 'get']
CollectionToServiceMap: Dict[str, Any] = {
    'user': UserService,
    'preference': PreferenceService
}