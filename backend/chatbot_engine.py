# chatbot_engine.py
class ChatbotEngine:
    def __init__(self, db1, db2, db3):
        self.db1 = db1
        self.db2 = db2
        self.db3 = db3
        self.contexts = {}

    def register_user(self, name, mobile, city, demo_otp="5762"):  # Changed 'phone' to 'mobile'
        user_id = self.db3.insert_user(name, mobile, city, demo_otp)  # Changed 'phone' to 'mobile'
        return user_id, demo_otp

    def verify_otp(self, user_id, otp):
        return self.db3.verify_otp(user_id, otp)

    def set_context(self, user_id, new_context):
        if user_id not in self.contexts:
            self.contexts[user_id] = {}
        self.contexts[user_id].update(new_context)

    def get_context(self, user_id):
        return self.contexts.get(user_id, {})