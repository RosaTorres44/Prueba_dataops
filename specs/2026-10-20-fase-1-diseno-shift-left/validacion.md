# Criterios de Validación y Aceptación · Fase 1: Diseño y Calidad Shift-Left

**Fase**: Fase 1 · Diseño y calidad shift-left  
**Fecha**: 2026-10-20  
**Rama de Git**: `fase-1-diseno-shift-left`  
**Estado**: Borrador para aprobación  
**Documentos base**: [requerimientos.md](file:///Users/rosa/Proyectos/utec/sdd/specs/2026-10-20-fase-1-diseno-shift-left/requerimientos.md) y [plan.md](file:///Users/rosa/Proyectos/utec/sdd/specs/2026-10-20-fase-1-diseno-shift-left/plan.md)

---

## Matriz de Criterios de Aceptación

Los siguientes criterios determinan si la Fase 1 está completada con éxito y autorizada para el merge hacia la rama `main`.

| ID | Criterio de Aceptación | Cómo se comprueba | Stage del Pipeline | Resultado Exacto Esperado | Severidad |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CA-01** | Integridad del archivo fuente | Test automatizado `pytest` | Stage 1 (Shift-Left) | `test_source_file_exists` pasa en verde; archivo existe y tamaño $> 0$ bytes | **Bloqueante** |
| **CA-02** | Contrato de cabeceras en CSV | Test automatizado `pytest` | Stage 1 (Shift-Left) | `test_csv_headers` pasa en verde; cabeceras exactas: `customer_id`, `name`, `age`, `country`, `email` | **Bloqueante** |
| **CA-03** | Detección shift-left de anomalías | Test automatizado `pytest` | Stage 1 (Shift-Left) | `test_data_anomalies_detected` emite reporte cuantitativo (ej. 1 fila con edad `abc`, 1 con país vacío, etc.) sin caerse | **Advertencia** |
| **CA-04** | Creación idempotente de tablas | Ejecución de `deploy_model.py` | Stage 2 (Despliegue) | Código de salida 0; crea o verifica las 5 tablas en Databricks sin errores de sintaxis | **Bloqueante** |
| **CA-05** | Integridad de `demo.ref_countries` | Consulta SQL en Databricks | Stage 2 (Despliegue) | `SELECT COUNT(*) FROM demo.ref_countries` retorna exactamente **`5`** | **Bloqueante** |
| **CA-06** | Contenido dimensional de países | Consulta SQL en Databricks | Stage 2 (Despliegue) | `SELECT DISTINCT country_code FROM demo.ref_countries` retorna el conjunto exacto: `{'PE', 'CL', 'CO', 'MX', 'AR'}` | **Bloqueante** |
| **CA-07** | Estructuras preparadas en Bronze, Silver, Rechazados y Gold | Consulta SQL en Databricks | Stage 2 (Despliegue) | `SHOW TABLES IN demo` retorna las 5 tablas requeridas | **Bloqueante** |
| **CA-08** | Inexistencia de credenciales en código | Linter / escaneo en PR | Stage 1 (Shift-Left) | Cero tokens o contraseñas hardcodeadas en scripts o workflows | **Bloqueante** |
| **CA-09** | CI en Pull Request en verde | GitHub Actions Workflow | CI en GitHub | Todos los jobs del workflow `.github/workflows/ci-pr-phase1.yml` finalizan con check verde | **Bloqueante** |

---

## Lista de Casillas de Verificación (Checklist)

### 1. Validación Shift-Left en Local y Runner (Stage 1)
- [x] **[CA-01] Existencia del archivo fuente**:
  - *Comando*: `pytest framework/tests/test_source_contract.py::test_source_file_exists -v`
  - *Resultado esperado*: `PASSED`
  - *Efecto si falla*: **Bloquea el merge**.
- [x] **[CA-02] Conformidad del contrato de columnas**:
  - *Comando*: `pytest framework/tests/test_source_contract.py::test_source_headers -v`
  - *Resultado esperado*: `PASSED` (valida la presencia exacta de `customer_id`, `name`, `age`, `country`, `email` en la fila 1).
  - *Efecto si falla*: **Bloquea el merge**.
- [x] **[CA-03] Reporte de salud y anomalías previas a la ingesta**:
  - *Comando*: `python framework/validation/validate_contract.py`
  - *Resultado esperado*: Retorna JSON o log estructurado identificando las 21 filas analizadas y cuantificando las anomalías detectadas en origen para retroalimentar la Fase 2.
  - *Efecto si falla*: **Advertencia** (los datos sucios son esperados en origen, pero el script de escaneo debe culminar sin excepciones no controladas).

### 2. Despliegue del Modelo en Databricks SQL Warehouse (Stage 2)
- [x] **[CA-04] Ejecución DDL automatizada e idempotente**:
  - *Comando*: `python framework/deployment/deploy_model.py`
  - *Resultado esperado*: `Exit code 0`. Registra la ejecución secuencial de `01_create_ref_countries.sql`, `02_seed_ref_countries.sql`, `03_create_bronze_customers.sql`, `04_create_silver_customers.sql`, `05_create_rejected_customers.sql` y `06_create_gold_customers_kpi.sql`.
  - *Efecto si falla*: **Bloquea el merge**.
- [x] **[CA-05] Conteo exacto de países en catálogo maestro**:
  - *Comprobación*:
    ```sql
    SELECT COUNT(*) AS total_paises FROM demo.ref_countries;
    ```
  - *Resultado esperado*: `total_paises = 5`.
  - *Efecto si falla*: **Bloquea el merge**.
- [x] **[CA-06] Verificación de códigos ISO y regiones**:
  - *Comprobación*:
    ```sql
    SELECT country_code, country_name, region FROM demo.ref_countries ORDER BY country_code;
    ```
  - *Resultado esperado*:
    | `country_code` | `country_name` | `region` |
    | :--- | :--- | :--- |
    | `AR` | Argentina | Sudamérica |
    | `CL` | Chile | Sudamérica |
    | `CO` | Colombia | Sudamérica |
    | `MX` | México | Norteamérica |
    | `PE` | Perú | Sudamérica |
  - *Efecto si falla*: **Bloquea el merge**.
- [x] **[CA-07] Verificación de tablas en el schema `demo`**:
  - *Comprobación*:
    ```sql
    SHOW TABLES IN demo;
    ```
  - *Resultado esperado*: Contiene obligatoriamente:
    - `bronze_customers`
    - `gold_customers_kpi`
    - `ref_countries`
    - `rejected_customers`
    - `silver_customers`
  - *Efecto si falla*: **Bloquea el merge**.

### 3. Gobernanza y Flujo de Integración Continua
- [x] **[CA-08] Verificación de seguridad de credenciales**:
  - *Comprobación*: Inspección de git diff en el Pull Request.
  - *Resultado esperado*: Ningún token, host o path hardcodeado. Todas las conexiones utilizan `os.environ` y GitHub Secrets (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_HTTP_PATH`).
  - *Efecto si falla*: **Bloquea el merge**.
- [x] **[CA-09] Workflow de GitHub Actions en verde**:
  - *Comprobación*: Pestaña "Actions" en el Pull Request de la rama `fase-1-diseno-shift-left`.
  - *Resultado esperado*: `ci-pr-phase1` culmina con éxito total en ambos jobs (Stage 1 y Stage 2).
  - *Efecto si falla*: **Bloquea el merge**.


---

## Criterios de Aprobación para Merge
Solo se autorizará el Pull Request hacia la rama `main` cuando:
1. Las **8 casillas bloqueantes** estén verificadas en estado satisfactorio.
2. El pipeline de CI en GitHub Actions muestre un estado **verde (exitoso)**.
3. Se presente el resumen de validación documentado al arquitecto/a de datos y al equipo.
