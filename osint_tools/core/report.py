"""
Moduł zawierający narzędzia do generowania raportów w różnych formatach.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import os
import re
from pathlib import Path
import tempfile
from jinja2 import Environment, FileSystemLoader, Template


class ReportGenerator:
    """Generator raportów OSINT w wielu formatach."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Inicjalizuje generator raportów.
        
        Args:
            templates_dir: Katalog z szablonami. Jeśli None, używa wbudowanych szablonów.
        """
        self.templates_dir = templates_dir
        
        if templates_dir and templates_dir.exists():
            self.template_env = Environment(loader=FileSystemLoader(str(templates_dir)))
        else:
            self.template_env = Environment()
            
    def generate_report(self, 
                       results: List[Dict[str, Any]], 
                       output_path: Path, 
                       format: str = "html",
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generuje raport z wyników OSINT.
        
        Args:
            results: Lista wyników narzędzi.
            output_path: Ścieżka do zapisania raportu.
            format: Format raportu (html, json, txt, pdf).
            metadata: Dodatkowe metadane do dołączenia.
            
        Returns:
            Wynik generowania raportu.
        """
        if not results:
            return {"success": False, "error": "Brak wyników do wygenerowania raportu"}
            
        try:
            generators = {
                "html": self._generate_html,
                "json": self._generate_json,
                "txt": self._generate_txt,
                "pdf": self._generate_pdf
            }
            
            if format not in generators:
                return {"success": False, "error": f"Nieobsługiwany format: {format}"}
                
            # Upewnij się, że katalog istnieje
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Wygeneruj raport
            final_path = generators[format](results, output_path, metadata)
            
            return {
                "success": True, 
                "format": format, 
                "path": str(final_path),
                "result_count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": f"Generowanie raportu nie powiodło się: {str(e)}"}
    
    def _generate_html(self, 
                      results: List[Dict[str, Any]], 
                      output_path: Path,
                      metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Generuje raport HTML.
        
        Args:
            results: Lista wyników narzędzi.
            output_path: Ścieżka do zapisania raportu.
            metadata: Dodatkowe metadane do dołączenia.
            
        Returns:
            Ścieżka do wygenerowanego raportu.
        """
        try:
            # Spróbuj załadować szablon z pliku
            if self.templates_dir and (self.templates_dir / "report.html").exists():
                template = self.template_env.get_template("report.html")
            else:
                # Użyj wbudowanego szablonu
                template_str = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>OSINT Super Kombajn - Raport</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { 
                            font-family: Arial, sans-serif; 
                            margin: 0; 
                            padding: 20px; 
                            color: #333; 
                        }
                        h1 { 
                            color: #2c3e50; 
                            border-bottom: 2px solid #3498db; 
                            padding-bottom: 10px; 
                        }
                        .tool-section { 
                            margin-bottom: 30px; 
                            border: 1px solid #ddd; 
                            padding: 15px; 
                            border-radius: 5px; 
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }
                        .tool-header { 
                            background: #f5f5f5; 
                            padding: 10px; 
                            margin: -15px -15px 15px; 
                            border-bottom: 1px solid #ddd; 
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }
                        .tool-title {
                            margin: 0;
                            font-size: 1.5em;
                        }
                        .success { 
                            color: #27ae60; 
                            background: #e8f8f0;
                            padding: 3px 8px;
                            border-radius: 4px;
                            font-weight: bold;
                        }
                        .error { 
                            color: #e74c3c; 
                            background: #fee;
                            padding: 3px 8px;
                            border-radius: 4px;
                            font-weight: bold;
                        }
                        .metadata { 
                            margin-bottom: 20px; 
                            color: #7f8c8d; 
                            font-size: 0.9em; 
                            background: #f8f9fa;
                            padding: 15px;
                            border-radius: 5px;
                        }
                        .result-data { 
                            max-height: 400px; 
                            overflow: auto; 
                            background: #f8f9fa; 
                            padding: 10px; 
                            border-radius: 3px;
                            font-family: monospace;
                            font-size: 0.9em;
                        }
                        .result-data pre { 
                            margin: 0; 
                            white-space: pre-wrap; 
                        }
                        .ai-analysis { 
                            background: #eaf2f8; 
                            padding: 15px; 
                            margin-top: 20px; 
                            border-radius: 5px;
                            border-left: 5px solid #3498db;
                        }
                        .ai-analysis h2 { 
                            color: #2980b9; 
                            margin-top: 0; 
                        }
                        .ai-section { 
                            margin-bottom: 15px; 
                        }
                        .ai-section h3 { 
                            color: #3498db; 
                            margin-bottom: 5px; 
                            border-bottom: 1px dotted #bdc3c7;
                            padding-bottom: 3px;
                        }
                        .summary-box {
                            background-color: #f5f5f5;
                            border-radius: 5px;
                            padding: 10px 15px;
                            margin-top: 10px;
                            box-shadow: inset 0 0 5px rgba(0,0,0,0.1);
                            font-size: 0.9em;
                        }
                        .stats {
                            display: flex;
                            flex-wrap: wrap;
                            gap: 10px;
                            margin-top: 10px;
                        }
                        .stat-item {
                            background: #fff;
                            border-radius: 4px;
                            padding: 8px 12px;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                            min-width: 120px;
                        }
                        .stat-value {
                            font-weight: bold;
                            font-size: 1.2em;
                            color: #2980b9;
                        }
                        footer {
                            margin-top: 30px;
                            text-align: center;
                            font-size: 0.8em;
                            color: #7f8c8d;
                            border-top: 1px solid #eee;
                            padding-top: 10px;
                        }
                    </style>
                </head>
                <body>
                    <h1>OSINT Super Kombajn - Raport</h1>
                    
                    <div class="metadata">
                        <h2>Informacje o analizie</h2>
                        <p><strong>Data wygenerowania:</strong> {{ metadata.timestamp }}</p>
                        <p><strong>Liczba narzędzi:</strong> {{ results|length }}</p>
                        {% if metadata.version %}
                        <p><strong>Wersja:</strong> {{ metadata.version }}</p>
                        {% endif %}
                        {% if metadata.target %}
                        <p><strong>Cel analizy:</strong> {{ metadata.target }}</p>
                        {% endif %}
                        
                        <div class="stats">
                            <div class="stat-item">
                                <div>Sukces</div>
                                <div class="stat-value">{{ results|selectattr('success')|list|length }}/{{ results|length }}</div>
                            </div>
                            
                            {% set found_profiles = namespace(count=0) %}
                            {% for result in results %}
                                {% if result.found_count is defined %}
                                    {% set found_profiles.count = found_profiles.count + result.found_count %}
                                {% endif %}
                            {% endfor %}
                            
                            <div class="stat-item">
                                <div>Znalezione profile</div>
                                <div class="stat-value">{{ found_profiles.count }}</div>
                            </div>
                            
                            <div class="stat-item">
                                <div>Czas wykonania</div>
                                <div class="stat-value">
                                    {% set total_time = namespace(ms=0) %}
                                    {% for result in results %}
                                        {% if result.execution_time_ms is defined %}
                                            {% set total_time.ms = total_time.ms + result.execution_time_ms %}
                                        {% endif %}
                                    {% endfor %}
                                    {{ (total_time.ms / 1000)|round(2) }}s
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    {% if metadata.ai_analysis %}
                    <div class="ai-analysis">
                        <h2>Analiza AI</h2>
                        
                        {% if metadata.ai_analysis.summary %}
                        <div class="ai-section">
                            <h3>Podsumowanie</h3>
                            <p>{{ metadata.ai_analysis.summary }}</p>
                        </div>
                        {% endif %}
                        
                        {% if metadata.ai_analysis.risks %}
                        <div class="ai-section">
                            <h3>Zagrożenia</h3>
                            <p>{{ metadata.ai_analysis.risks }}</p>
                        </div>
                        {% endif %}
                        
                        {% if metadata.ai_analysis.recommendations %}
                        <div class="ai-section">
                            <h3>Rekomendacje</h3>
                            <p>{{ metadata.ai_analysis.recommendations }}</p>
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    {% for result in results %}
                    <div class="tool-section">
                        <div class="tool-header">
                            <h2 class="tool-title">
                                {% if result.username %}
                                {{ result.tool|default('Narzędzie') }} - {{ result.username }}
                                {% elif result.email %}
                                {{ result.tool|default('Narzędzie') }} - {{ result.email }}
                                {% elif result.phone_number %}
                                {{ result.tool|default('Narzędzie') }} - {{ result.phone_number }}
                                {% elif result.file_path %}
                                {{ result.tool|default('Narzędzie') }} - {{ result.file_path }}
                                {% else %}
                                {{ result.tool|default('Nieznane narzędzie') }}
                                {% endif %}
                            </h2>
                            
                            {% if result.success %}
                            <span class="success">✓ Sukces</span>
                            {% else %}
                            <span class="error">✗ Błąd</span>
                            {% endif %}
                        </div>
                        
                        {% if result.success and result.data %}
                        <div class="summary-box">
                            {% if result.found_count is defined %}
                            <p><strong>Znalezione profile:</strong> {{ result.found_count }}</p>
                            {% endif %}
                            {% if result.execution_time_ms is defined %}
                            <p><strong>Czas wykonania:</strong> {{ result.execution_time_ms|round|int }} ms</p>
                            {% endif %}
                        </div>
                        
                        <div class="result-data">
                            <pre>{{ result.data|tojson(indent=2) }}</pre>
                        </div>
                        {% elif not result.success and result.error %}
                        <div class="error">
                            <p>Błąd: {{ result.error }}</p>
                            {% if result.retry_count is defined %}
                            <p>Liczba prób: {{ result.retry_count }}</p>
                            {% endif %}
                        </div>
                        {% endif %}
                        
                        {% if result.output_path %}
                        <p><strong>Plik wyjściowy:</strong> {{ result.output_path }}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                    
                    <footer>
                        <p>Wygenerowano przez OSINT Super Kombajn v{{ metadata.version|default('0.2.0') }}</p>
                    </footer>
                </body>
                </html>
                """
                template = self.template_env.from_string(template_str)
            
            # Przygotuj metadane
            meta = metadata or {}
            if "timestamp" not in meta:
                meta["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            # Dodaj nazwę narzędzia, jeśli brakuje
            for result in results:
                if "tool" not in result:
                    if "username" in result:
                        result["tool"] = "Username Analysis"
                    elif "email" in result:
                        result["tool"] = "Email Analysis"
                    elif "phone_number" in result:
                        result["tool"] = "Phone Analysis"
                    elif "file_path" in result:
                        result["tool"] = "File Analysis"
                    else:
                        result["tool"] = "Unknown Analysis"
                        
            # Renderuj szablon
            html_content = template.render(results=results, metadata=meta)
            
            # Upewnij się, że ścieżka ma rozszerzenie .html
            if not str(output_path).lower().endswith('.html'):
                output_path = output_path.with_suffix('.html')
                
            # Zapisz do pliku
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            return output_path
        except Exception as e:
            raise RuntimeError(f"Nie udało się wygenerować raportu HTML: {str(e)}")
    
    def _generate_json(self, 
                      results: List[Dict[str, Any]], 
                      output_path: Path,
                      metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Generuje raport JSON.
        
        Args:
            results: Lista wyników narzędzi.
            output_path: Ścieżka do zapisania raportu.
            metadata: Dodatkowe metadane do dołączenia.
            
        Returns:
            Ścieżka do wygenerowanego raportu.
        """
        # Przygotuj metadane
        meta = metadata or {}
        if "timestamp" not in meta:
            meta["timestamp"] = datetime.now().isoformat()
            
        # Przygotuj raport
        report = {
            "metadata": meta,
            "results": results
        }
        
        # Upewnij się, że ścieżka ma rozszerzenie .json
        if not str(output_path).lower().endswith('.json'):
            output_path = output_path.with_suffix('.json')
            
        # Zapisz do pliku
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        return output_path
    
    def _generate_txt(self, 
                     results: List[Dict[str, Any]], 
                     output_path: Path,
                     metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Generuje raport tekstowy.
        
        Args:
            results: Lista wyników narzędzi.
            output_path: Ścieżka do zapisania raportu.
            metadata: Dodatkowe metadane do dołączenia.
            
        Returns:
            Ścieżka do wygenerowanego raportu.
        """
        # Upewnij się, że ścieżka ma rozszerzenie .txt
        if not str(output_path).lower().endswith('.txt'):
            output_path = output_path.with_suffix('.txt')
            
        # Przygotuj metadane
        meta = metadata or {}
        if "timestamp" not in meta:
            meta["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # Zapisz do pliku
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== OSINT Super Kombajn Report ===\n\n")
            
            # Zapisz metadane
            f.write(f"Generated: {meta.get('timestamp')}\n")
            f.write(f"Total Tools: {len(results)}\n")
            if "version" in meta:
                f.write(f"Version: {meta['version']}\n")
            if "target" in meta:
                f.write(f"Target: {meta['target']}\n")
            f.write("\n")
            
            # Zapisz analizę AI, jeśli istnieje
            if "ai_analysis" in meta:
                f.write("--- AI Analysis ---\n\n")
                
                if "summary" in meta["ai_analysis"]:
                    f.write("Summary:\n")
                    f.write(meta["ai_analysis"]["summary"] + "\n\n")
                    
                if "risks" in meta["ai_analysis"]:
                    f.write("Risks:\n")
                    f.write(meta["ai_analysis"]["risks"] + "\n\n")
                    
                if "recommendations" in meta["ai_analysis"]:
                    f.write("Recommendations:\n")
                    f.write(meta["ai_analysis"]["recommendations"] + "\n\n")
                    
                f.write("\n")
            
            # Zapisz wyniki
            for result in results:
                # Określ narzędzie i cel
                tool = result.get("tool", "Unknown Tool")
                target = result.get("username", 
                                  result.get("email", 
                                           result.get("phone_number", 
                                                     result.get("file_path", "Unknown"))))
                
                f.write(f"--- {tool} - {target} ---\n")
                f.write(f"Status: {'Success' if result.get('success') else 'Failed'}\n")
                
                if "execution_time_ms" in result:
                    f.write(f"Execution Time: {int(result['execution_time_ms'])} ms\n")
                
                if not result.get("success") and "error" in result:
                    f.write(f"Error: {result['error']}\n")
                
                if "output_path" in result:
                    f.write(f"Output File: {result['output_path']}\n")
                    
                if result.get("success") and "data" in result:
                    f.write("\nData Summary:\n")
                    # Spłaszcz i uprość dla raportu tekstowego
                    self._write_data_summary(f, result["data"])
                
                f.write("\n\n")
                
        return output_path
    
    def _write_data_summary(self, file, data, indent=0):
        """
        Zapisuje uproszczone podsumowanie danych dla raportu tekstowego.
        
        Args:
            file: Plik do zapisu.
            data: Dane do podsumowania.
            indent: Poziom wcięcia.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)) and value:
                    file.write(f"{'  ' * indent}{key}:\n")
                    self._write_data_summary(file, value, indent + 1)
                else:
                    file.write(f"{'  ' * indent}{key}: {value}\n")
        elif isinstance(data, list):
            for i, item in enumerate(data[:5]):  # Ogranicz do pierwszych 5 elementów
                if isinstance(item, dict):
                    file.write(f"{'  ' * indent}Item {i+1}:\n")
                    self._write_data_summary(file, item, indent + 1)
                else:
                    file.write(f"{'  ' * indent}- {item}\n")
            if len(data) > 5:
                file.write(f"{'  ' * indent}... ({len(data) - 5} more items)\n")
    
    def _generate_pdf(self, 
                     results: List[Dict[str, Any]], 
                     output_path: Path,
                     metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Generuje raport PDF używając HTML jako pośredniego kroku.
        
        Args:
            results: Lista wyników narzędzi.
            output_path: Ścieżka do zapisania raportu.
            metadata: Dodatkowe metadane do dołączenia.
            
        Returns:
            Ścieżka do wygenerowanego raportu.
        """
        try:
            # Sprawdź, czy WeasyPrint jest dostępny
            try:
                import weasyprint
            except ImportError:
                raise ImportError("Generowanie PDF wymaga WeasyPrint. Zainstaluj: pip install weasyprint")
                
            # Najpierw wygeneruj HTML
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
                temp_path = Path(temp.name)
                
            self._generate_html(results, temp_path, metadata)
            
            # Upewnij się, że ścieżka ma rozszerzenie .pdf
            if not str(output_path).lower().endswith('.pdf'):
                output_path = output_path.with_suffix('.pdf')
                
            # Konwertuj HTML na PDF
            weasyprint.HTML(filename=str(temp_path)).write_pdf(output_path)
            
            # Usuń tymczasowy plik HTML
            os.unlink(temp_path)
            
            return output_path
        except Exception as e:
            raise RuntimeError(f"Nie udało się wygenerować raportu PDF: {str(e)}")