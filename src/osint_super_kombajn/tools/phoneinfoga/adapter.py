"""
Adapter dla narzędzia PhoneInfoga.
"""
class PhoneInfogaAdapter:
    def search(self, phone_number):
        return {"carrier": "Example Carrier", "country": "Poland"}
