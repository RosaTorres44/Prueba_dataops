"""
Tests automatizados con Pytest para el Stage 1: Validación Shift-Left.
Comprueba los criterios de aceptación CA-01, CA-02 y CA-03 sobre el archivo fuente.
"""

import os
import pytest
from framework.validation.validate_contract import (
    EXPECTED_COLUMNS,
    validate_source_structure,
    analyze_source_quality,
)

CSV_PATH = "data/source/customers.csv"


def test_source_file_exists():
    """CA-01: El archivo fuente debe existir físicamente y tener tamaño mayor a cero bytes."""
    assert os.path.exists(CSV_PATH), f"El archivo fuente '{CSV_PATH}' no existe."
    size_bytes = os.path.getsize(CSV_PATH)
    assert size_bytes > 0, f"El archivo '{CSV_PATH}' está vacío (0 bytes)."


def test_source_headers():
    """CA-02: El contrato de columnas debe coincidir exactamente con las 5 cabeceras requeridas."""
    is_valid, msg, headers = validate_source_structure(CSV_PATH)
    assert is_valid, f"Fallo en contrato de cabeceras: {msg}"
    assert headers == EXPECTED_COLUMNS, f"Cabeceras incorrectas. Esperado: {EXPECTED_COLUMNS}, Encontrado: {headers}"


def test_data_anomalies_detected():
    """
    CA-03: El módulo debe detectar y cuantificar las anomalías conocidas en el dataset de origen
    sin arrojar excepciones no controladas.
    """
    report = analyze_source_quality(CSV_PATH)
    assert isinstance(report, dict), "El reporte de calidad debe ser un diccionario estructurado."
    assert report["total_rows"] > 0, "El dataset analizado debe contener al menos una fila."
    # Comprobar que detecta las anomalías existentes en customers.csv
    assert report["rows_with_field_anomalies"] > 0, "Se esperaba detectar anomalías conocidas en el dataset de origen."
    assert "exact_duplicates_count" in report
    assert "conflicting_duplicates_count" in report
    print(f"\n[Shift-Left Diagnostic] Total filas: {report['total_rows']}, Anómalas: {report['rows_with_field_anomalies']}")
