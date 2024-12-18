class PendingConfirmationManager:
    def __init__(self):
        self.pending_confirmations = {}

    def add_confirmation(self, key, data):
        self.pending_confirmations[key] = data

    def get_confirmation(self, key):
        return self.pending_confirmations.pop(key, None)

    def has_confirmation(self, key):
        return key in self.pending_confirmations