"""
Stage 1: Validación Shift-Left del Contrato del Dato y Calidad del Origen.
Verifica la existencia, estructura y anomalías sintácticas de data/source/customers.csv
en el runner de CI antes de interactuar con la plataforma de datos.
"""

import csv
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

# Constantes del contrato de datos
EXPECTED_COLUMNS = ["customer_id", "name", "age", "country", "email"]
VALID_COUNTRIES = {"PE", "CL", "CO", "MX", "AR"}
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_source_structure(csv_path: str = "data/source/customers.csv") -> Tuple[bool, str, List[str]]:
    """
    Comprueba existencia física, tamaño y correspondencia exacta de columnas en el CSV.
    Retorna: (es_valido, mensaje_error, lista_columnas_encontradas)
    """
    if not os.path.exists(csv_path):
        return False, f"El archivo fuente no existe en la ruta especificada: '{csv_path}'", []

    if os.path.getsize(csv_path) == 0:
        return False, f"El archivo fuente '{csv_path}' está vacío (0 bytes)", []

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return False, "El archivo CSV no contiene ninguna fila.", []

    # Normalizar espacios en cabeceras
    cleaned_headers = [h.strip() for h in headers]
    if cleaned_headers != EXPECTED_COLUMNS:
        return (
            False,
            f"Contrato violado. Cabeceras esperadas: {EXPECTED_COLUMNS}. Encontradas: {cleaned_headers}",
            cleaned_headers,
        )

    return True, "Estructura del contrato válida", cleaned_headers


def analyze_source_quality(csv_path: str = "data/source/customers.csv") -> Dict[str, Any]:
    """
    Escanea las filas del archivo de origen para identificar y clasificar anomalías
    de calidad según las reglas definidas en la constitución.
    """
    structure_valid, msg, headers = validate_source_structure(csv_path)
    if not structure_valid:
        raise ValueError(f"Fallo estructural previo al análisis: {msg}")

    total_rows = 0
    anomalies: List[Dict[str, Any]] = []
    seen_ids: Dict[str, List[Dict[str, str]]] = {}

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):  # Fila 2 corresponde a la primera fila de datos
            total_rows += 1
            customer_id = (row.get("customer_id") or "").strip()
            name = (row.get("name") or "").strip()
            age_raw = (row.get("age") or "").strip()
            country = (row.get("country") or "").strip()
            email = (row.get("email") or "").strip()

            row_anomalies = []

            # 1. Regla customer_id
            if not customer_id:
                row_anomalies.append("customer_id nulo o vacío")

            # 2. Regla name
            if not name:
                row_anomalies.append("Nombre ausente o compuesto únicamente por espacios")

            # 3. Regla age
            is_age_valid_num = False
            if not age_raw:
                row_anomalies.append("Edad nula o vacía")
            else:
                try:
                    age_val = int(age_raw)
                    if age_val < 0 or age_val > 120:
                        row_anomalies.append(f"Edad fuera de rango: {age_val}")
                    else:
                        is_age_valid_num = True
                except ValueError:
                    row_anomalies.append(f"Edad no numérica: '{age_raw}'")

            # 4. Regla country
            if not country:
                row_anomalies.append("País nulo o vacío")
            elif country not in VALID_COUNTRIES:
                row_anomalies.append(f"País '{country}' no registrado en ref_countries")

            # 5. Regla email
            if not email:
                row_anomalies.append("Email nulo o vacío")
            elif not EMAIL_REGEX.match(email):
                row_anomalies.append(f"Email con sintaxis inválida: '{email}'")

            # Registrar duplicados para análisis
            if customer_id:
                seen_ids.setdefault(customer_id, []).append({
                    "row_num": idx,
                    "data": dict(row),
                    "anomalies": row_anomalies,
                })

            if row_anomalies:
                anomalies.append({
                    "row_num": idx,
                    "customer_id": customer_id,
                    "issues": row_anomalies,
                })

    # Detección de duplicados exactos y conflictos de identidad
    exact_duplicates = 0
    conflicting_duplicates = 0
    for cid, occurrences in seen_ids.items():
        if len(occurrences) > 1:
            first_data = occurrences[0]["data"]
            all_identical = all(occ["data"] == first_data for occ in occurrences[1:])
            if all_identical:
                exact_duplicates += (len(occurrences) - 1)
            else:
                conflicting_duplicates += len(occurrences)

    report = {
        "source_file": csv_path,
        "total_rows": total_rows,
        "rows_with_field_anomalies": len(anomalies),
        "exact_duplicates_count": exact_duplicates,
        "conflicting_duplicates_count": conflicting_duplicates,
        "anomalies_detail": anomalies,
    }
    return report


def main() -> None:
    print("=== Stage 1 · Validación Shift-Left de Contrato y Calidad ===")
    csv_path = os.environ.get("CSV_PATH", "data/source/customers.csv")
    is_valid, msg, headers = validate_source_structure(csv_path)

    if not is_valid:
        print(f"❌ ERROR BLOQUEANTE: {msg}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Estructura del contrato validada para '{csv_path}'")
    print(f"   Cabeceras verificadas: {headers}")

    report = analyze_source_quality(csv_path)
    print("\n--- Reporte Diagnóstico de Calidad Shift-Left ---")
    print(f"Total filas analizadas          : {report['total_rows']}")
    print(f"Filas con anomalías de campo    : {report['rows_with_field_anomalies']}")
    print(f"Duplicados exactos detectados   : {report['exact_duplicates_count']}")
    print(f"Conflictos de identidad         : {report['conflicting_duplicates_count']}")
    
    print("\nDetalle de anomalías detectadas en origen:")
    for item in report["anomalies_detail"]:
        print(f"  - Fila {item['row_num']} (ID: {item['customer_id']}): {', '.join(item['issues'])}")

    print("\n✅ Validación Shift-Left concluida exitosamente (Diagnóstico completado sin fallos estructurales).")


if __name__ == "__main__":
    main()
