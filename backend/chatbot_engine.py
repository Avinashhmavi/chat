import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ChatbotEngine:
    def __init__(self, db1):
        self.db1 = db1
        self.user_context = {}

    def set_context(self, user_id, context):
        if user_id:
            self.user_context[user_id] = self.user_context.get(user_id, {})
            self.user_context[user_id].update(context)
        logger.debug(f"Updated context for user {user_id}: {self.user_context.get(user_id)}")

    def get_context(self, user_id):
        return self.user_context.get(user_id, {})

    async def register_user(self, name, mobile, city):
        try:
            otp = "123456"  # In production, generate a secure OTP
            user_id = await self.db1.insert_user(name, mobile, city, otp)
            logger.info(f"User registered: {user_id}")
            return user_id, otp
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise

    async def verify_otp(self, user_id, otp):
        try:
            return await self.db1.verify_otp(user_id, otp)
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            raise