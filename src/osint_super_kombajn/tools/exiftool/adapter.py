"""
Adapter dla narzędzia ExifTool.
"""
class ExifToolAdapter:
    def extract_metadata(self, file_path):
        return {"camera": "Example Camera", "location": "Example Location"}
