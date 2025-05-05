"""
Adapter dla narzędzia Maigret.
"""
class MaigretAdapter:
    def search(self, username):
        return {"found": ["instagram", "facebook", "linkedin"]}
