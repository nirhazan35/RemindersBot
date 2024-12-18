class ReminderBot:
    def __init__(self, calendar_service, messaging_service, confirmation_manager):
        self.calendar_service = calendar_service
        self.messaging_service = messaging_service
        self.confirmation_manager = confirmation_manager

    def run_daily_check(self):
        appointments = self.calendar_service.get_tomorrow_tipul_appointments()
        for _, description, start_time in appointments:
            customer_number = self.extract_phone_number(description)
            if customer_number:
                key = f"{customer_number}${start_time}"
                self.confirmation_manager.add_confirmation(key, {
                    'customer_number': customer_number,
                    'start_time': start_time
                })
                self.messaging_service.send_confirmation_request(start_time, customer_number)

    @staticmethod
    def extract_phone_number(description):
        import re
        match = re.search(r"(?:\+9725|05)\d{8}", description)
        if match:
            phone_number = match.group(0)
            return '972' + phone_number[1:] if phone_number.startswith('05') else phone_number
        return None