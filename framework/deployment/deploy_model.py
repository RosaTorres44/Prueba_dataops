"""
Stage 2: Despliegue Automatizado del Modelo en Databricks SQL Warehouse.
Ejecuta scripts DDL idempotentes para inicializar el catálogo demo y verifica
la integridad de las tablas y del catálogo maestro de referencia.
"""

import glob
import os
import sys
from typing import List, Tuple

try:
    # pyrefly: ignore[missing-import]
    from databricks import sql
except ImportError:
    sql = None


def get_required_env(name: str) -> str:
    """Obtiene una variable de entorno requerida o lanza un error descriptivo."""
    val = os.environ.get(name)
    if not val:
        raise ValueError(
            f"Falta la variable de entorno obligatoria '{name}'. "
            "Asegúrate de configurar los secrets en GitHub Actions o en tu entorno local."
        )
    return val


def read_sql_files(sql_dir: str) -> List[Tuple[str, str]]:
    """Lee y ordena alfabéticamente todos los archivos .sql del directorio indicado."""
    pattern = os.path.join(sql_dir, "*.sql")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No se encontraron scripts SQL en el directorio '{sql_dir}'")

    scripts = []
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            scripts.append((os.path.basename(fpath), content))
    return scripts


def deploy_model(sql_dir: str = "framework/deployment/sql") -> None:
    """Se conecta a Databricks SQL y ejecuta en orden todos los DDLs."""
    print("=== Stage 2 · Despliegue del Modelo en Databricks SQL Warehouse ===")
    
    host = get_required_env("DATABRICKS_HOST")
    http_path = get_required_env("DATABRICKS_HTTP_PATH")
    token = get_required_env("DATABRICKS_TOKEN")

    print(f"Databricks Host: {host}")
    print(f"HTTP Path      : {http_path}")
    print("Token          : [REDACTED - GOBIERNO DE SEGURIDAD]")

    if sql is None:
        raise ImportError("La librería 'databricks-sql-connector' no está instalada.")

    scripts = read_sql_files(sql_dir)
    print(f"Scripts SQL encontrados para ejecución ({len(scripts)}):")
    for fname, _ in scripts:
        print(f"  - {fname}")

    print("\nIniciando conexión con Databricks SQL Warehouse...")
    with sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    ) as connection:
        with connection.cursor() as cursor:
            # 1. Asegurar existencia del schema demo
            print("Verificando existencia del schema 'demo'...")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS demo COMMENT 'Schema para producto ClientesConfiables'")
            print("✅ Schema 'demo' disponible.")

            # 2. Ejecutar cada script DDL en orden
            for fname, statement in scripts:
                print(f"Ejecutando script: {fname}...")
                cursor.execute(statement)
                print(f"  -> {fname} aplicado con éxito.")

            # 3. Verificaciones de integridad post-despliegue
            print("\n--- Ejecutando Verificaciones de Integridad (Criterios de Aceptación) ---")
            
            # CA-07: Tablas existentes en schema demo
            cursor.execute("SHOW TABLES IN demo")
            tables = [row[1] for row in cursor.fetchall()]
            print(f"Tablas detectadas en 'demo': {tables}")
            required_tables = {
                "ref_countries",
                "bronze_customers",
                "silver_customers",
                "rejected_customers",
                "gold_customers_kpi",
            }
            missing = required_tables - set(tables)
            if missing:
                raise RuntimeError(f"Faltan tablas requeridas en el schema demo: {missing}")
            print("✅ CA-07 Cumplido: Las 5 tablas existen en el catálogo demo.")

            # CA-05 & CA-06: Verificación de demo.ref_countries
            cursor.execute("SELECT COUNT(*) FROM demo.ref_countries")
            count_result = cursor.fetchone()
            total_countries = count_result[0] if count_result else 0
            print(f"Total registros en demo.ref_countries: {total_countries}")
            if total_countries != 5:
                raise ValueError(
                    f"CA-05 Fallido: Se esperaban exactamente 5 países en ref_countries, pero se encontraron {total_countries}."
                )
            print("✅ CA-05 Cumplido: demo.ref_countries contiene exactamente 5 registros.")

            cursor.execute("SELECT country_code, country_name, region FROM demo.ref_countries ORDER BY country_code")
            rows = cursor.fetchall()
            codes = {row[0] for row in rows}
            expected_codes = {"PE", "CL", "CO", "MX", "AR"}
            if codes != expected_codes:
                raise ValueError(
                    f"CA-06 Fallido: Códigos encontrados {codes} no coinciden con los esperados {expected_codes}."
                )
            print(f"✅ CA-06 Cumplido: Catálogo verificado con los 5 países esperados: {sorted(list(codes))}")

    print("\n=== Stage 2 · Despliegue y Verificación completados con éxito en VERDE ===")


if __name__ == "__main__":
    try:
        deploy_model()
    except Exception as exc:
        print(f"❌ Error durante el despliegue del modelo: {exc}", file=sys.stderr)
        sys.exit(1)
