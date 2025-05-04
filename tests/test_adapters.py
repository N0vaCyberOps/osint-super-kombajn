"""
Testy dla adapterów narzędzi OSINT.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from osint_tools.core.base_adapter import BaseAdapter
from osint_tools.tools.maigret.adapter import MaigretAdapter


class TestBaseAdapter:
    """Testy dla bazowej klasy adaptera."""
    
    class TestAdapter(BaseAdapter[str, dict]):
        """Adapter testowy do testów."""
        
        tool_name = "test_tool"
        required_binaries = ["test_binary"]
        
        async def execute(self, input_data: str, output_path=None):
            """Implementacja metody execute dla testów."""
            return {"success": True, "data": {"test": input_data}}
    
    def test_init(self):
        """Test inicjalizacji adaptera."""
        adapter = self.TestAdapter(timeout=100, max_retries=2)
        assert adapter.timeout == 100
        assert adapter.max_retries == 2
        assert adapter.tool_name == "test_tool"
        assert adapter.required_binaries == ["test_binary"]
    
    @pytest.mark.asyncio
    async def test_run_with_retries_success(self):
        """Test mechanizmu ponownych prób - sukces."""
        adapter = self.TestAdapter()
        
        async def operation():
            return {"result": "success"}
        
        success, result, error = await adapter.run_with_retries(operation)
        
        assert success is True
        assert result == {"result": "success"}
        assert error is None
    
    @pytest.mark.asyncio
    async def test_run_with_retries_failure(self):
        """Test mechanizmu ponownych prób - niepowodzenie."""
        adapter = self.TestAdapter(max_retries=1)
        
        async def operation():
            raise ValueError("Test error")
        
        success, result, error = await adapter.run_with_retries(operation)
        
        assert success is False
        assert result is None
        assert "Test error" in error
    
    @pytest.mark.asyncio
    async def test_run_with_retries_validation(self):
        """Test mechanizmu ponownych prób z walidacją."""
        adapter = self.TestAdapter(max_retries=1)
        
        async def operation():
            return {"status": "invalid"}
        
        def validate(result):
            return result.get("status") == "valid"
        
        success, result, error = await adapter.run_with_retries(operation, validate)
        
        assert success is False
        assert result is None
        assert "Walidacja wyniku nie powiodła się" in error
    
    def test_prepare_output_path(self):
        """Test przygotowania ścieżki wyjściowej."""
        adapter = self.TestAdapter()
        
        # Test z domyślną ścieżką
        path = adapter.prepare_output_path(None, "test", "user@example.com")
        assert path.name.startswith("test_user_example.com_")
        assert path.name.endswith(".json")
        assert path.parent.name == "results"
        
        # Test z podaną ścieżką
        custom_path = Path("custom/path.json")
        path = adapter.prepare_output_path(custom_path, "test", "user")
        assert path == custom_path


class TestMaigretAdapter:
    """Testy dla adaptera Maigret."""
    
    @pytest.fixture
    def mock_maigret_path(self, tmp_path):
        """Fixture tworzący tymczasową ścieżkę z makietą skryptu Maigret."""
        maigret_dir = tmp_path / "maigret"
        maigret_dir.mkdir()
        maigret_script = maigret_dir / "maigret.py"
        maigret_script.write_text("# Mock Maigret script")
        return maigret_dir
    
    @pytest.mark.asyncio
    async def test_init(self, mock_maigret_path):
        """Test inicjalizacji adaptera Maigret."""
        adapter = MaigretAdapter(maigret_path=mock_maigret_path)
        assert adapter.tool_name == "maigret"
        assert adapter.required_binaries == ["python"]
        assert adapter.maigret_path == mock_maigret_path
    
    @pytest.mark.asyncio
    async def test_search_username_validation_error(self):
        """Test walidacji nazwy użytkownika."""
        with patch("osint_tools.tools.maigret.adapter.validate_username") as mock_validate:
            mock_validate.return_value = "Błąd walidacji"
            
            adapter = MaigretAdapter()
            result = await adapter.search_username("invalid;user")
            
            assert result["success"] is False
            assert result["error"] == "Błąd walidacji"
            assert result["username"] == "invalid;user"
    
    @pytest.mark.asyncio
    async def test_search_username_success(self, mock_maigret_path, tmp_path):
        """Test pomyślnego wyszukiwania nazwy użytkownika."""
        # Przygotuj makietę wyniku JSON
        mock_results = [
            {"username": "testuser", "site": "twitter", "status": "found"},
            {"username": "testuser", "site": "github", "status": "found"},
            {"username": "testuser", "site": "facebook", "status": "not found"}
        ]
        
        with patch("osint_tools.tools.maigret.adapter.validate_username", return_value=True), \
             patch("osint_tools.tools.maigret.adapter.sanitize_command_input", return_value="testuser"), \
             patch.object(BaseAdapter, "run_command", new_callable=AsyncMock) as mock_run_command, \
             patch.object(BaseAdapter, "load_json_file") as mock_load_json, \
             patch.object(BaseAdapter, "save_json_file") as mock_save_json:
            
            # Skonfiguruj makiety
            mock_run_command.return_value = (True, "Output", None)
            mock_load_json.return_value = (True, mock_results, None)
            mock_save_json.return_value = (True, None)
            
            # Wykonaj test
            adapter = MaigretAdapter(maigret_path=mock_maigret_path)
            output_path = tmp_path / "output.json"
            result = await adapter.search_username("testuser", output_path)
            
            # Sprawdź wyniki
            assert result["success"] is True
            assert result["username"] == "testuser"
            assert result["output_path"] == str(output_path)
            assert result["found_count"] == 2
            assert result["data"]["total_services"] == 3
            assert result["data"]["found_services"] == 2
            
            # Sprawdź, czy polecenie zostało wywołane z odpowiednimi parametrami
            cmd_args = mock_run_command.call_args[0][0]
            assert "python" in cmd_args
            assert "maigret.py" in cmd_args[1]
            assert "testuser" in cmd_args
            assert "--json" in cmd_args
