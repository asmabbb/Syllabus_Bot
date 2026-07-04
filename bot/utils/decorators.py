from bot.utils.permissions import is_admin, is_super_admin

def admin_only(func): 

    def wrapper(message, bot):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "You do not have permission to use this command.")
            return
        
        return func(message, bot)
    
    return wrapper



def super_admin_only(func):

    def wrapper(message, bot):
        if not is_super_admin(message.from_user.id):
            bot.send_message(message.chat.id, "Only Superior Admins can use this command." )
            
            return
        
        return func(message, bot)
    
    return wrapper