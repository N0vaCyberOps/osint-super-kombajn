"""
Adapter dla narzędzia Holehe.
"""
class HoleheAdapter:
    def check_email(self, email):
        return {"services": ["gmail", "twitter", "github"]}
