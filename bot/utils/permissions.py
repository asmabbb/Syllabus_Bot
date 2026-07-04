from bot.database.queries.admins import get_role
from bot.config import OWNER_ID


def is_owner(user_id):
    return user_id == OWNER_ID



def is_super_admin(user_id):
    if is_owner(user_id):
        return True
    
    return get_role(user_id) == "super_admin"



def is_minor_admin(user_id):
    if is_owner(user_id):
        return True
    
    return get_role(user_id) == "minor_admin"



def is_admin(user_id):
    if is_owner(user_id):
        return True
    
    return get_role(user_id) in ("minor_admin", "super_admin")

