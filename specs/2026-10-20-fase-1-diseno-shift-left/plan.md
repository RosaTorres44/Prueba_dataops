# Plan de Implementación · Fase 1: Diseño y Calidad Shift-Left

**Fase**: Fase 1 · Diseño y calidad shift-left  
**Fecha**: 2026-10-20  
**Rama de Git**: `fase-1-diseno-shift-left`  
**Estado**: Borrador para aprobación  
**Documento base**: [specs/2026-10-20-fase-1-diseno-shift-left/requerimientos.md](file:///Users/rosa/Proyectos/utec/sdd/specs/2026-10-20-fase-1-diseno-shift-left/requerimientos.md)

---

## Resumen del Plan

El plan de trabajo se organiza en **5 grupos de tareas secuenciales y atómicas**. Cada tarea especifica con exactitud los archivos que crea o modifica, garantizando que el diseño del modelo, los scripts DDL, la validación shift-left y la automatización CI/CD queden completamente articulados sin escribir aún código de ingesta o transformaciones de negocio (reservados para la Fase 2).

---

## Grupo 1: Scripts DDL del Modelo de Datos y Catálogo Maestro (Stage 2)
> **Objetivo**: Escribir los archivos SQL idempotentes que definen el schema `demo` y las 5 tablas en Databricks.

- [x] **Tarea 1.1 · Catálogo de Referencia Geográfica**:
  - Crear `framework/deployment/sql/01_create_ref_countries.sql`: Sentencia DDL idempotente para `demo.ref_countries` con clave primaria `country_code`.
  - Crear `framework/deployment/sql/02_seed_ref_countries.sql`: Sentencia `MERGE INTO` para sembrar los 5 países iniciales (PE, CL, CO, MX, AR) con nombre y región.
- [x] **Tarea 1.2 · Capa Cruda Bronze**:
  - Crear `framework/deployment/sql/03_create_bronze_customers.sql`: Sentencia DDL idempotente para `demo.bronze_customers` con metadatos de auditoría (`source_file`, `execution_id`, `ingested_at`).
- [x] **Tarea 1.3 · Capas Silver y Rechazados**:
  - Crear `framework/deployment/sql/04_create_silver_customers.sql`: Sentencia DDL idempotente para `demo.silver_customers` con tipos estrictos, PK `customer_id` y banderas booleanas (`es_mayor_edad`, `es_contactable`).
  - Crear `framework/deployment/sql/05_create_rejected_customers.sql`: Sentencia DDL idempotente para `demo.rejected_customers` con campos para `rejection_id`, `raw_record` en JSON, `motivo_rechazo`, `execution_id` y `rejected_at`.
- [x] **Tarea 1.4 · Capa Analítica Gold**:
  - Crear `framework/deployment/sql/06_create_gold_customers_kpi.sql`: Sentencia DDL idempotente para `demo.gold_customers_kpi` con métricas agregadas por país y región, estrictamente sin columnas PII.

---

## Grupo 2: Automatización de Despliegue en Databricks (Stage 2)
> **Objetivo**: Desarrollar el script de despliegue en Python que ejecuta los DDLs contra Databricks SQL Warehouse mediante credenciales seguras.

- [x] **Tarea 2.1 · Módulo de Despliegue de Esquemas (`deploy_model.py`)**:
  - Crear `framework/deployment/deploy_model.py`: Script en Python que:
    1. Lee las variables de entorno `DATABRICKS_HOST`, `DATABRICKS_TOKEN` y `DATABRICKS_HTTP_PATH`.
    2. Se conecta al SQL Warehouse usando `databricks-sql-connector`.
    3. Ejecuta en orden los 6 scripts SQL del directorio `framework/deployment/sql/`.
    4. Garantiza idempotencia y registra en consola el resultado de cada sentencia.
- [x] **Tarea 2.2 · Verificación Post-Despliegue de Tablas**:
  - Modificar `framework/deployment/deploy_model.py` para incluir una función de verificación que ejecute `SHOW TABLES IN demo` y compruebe que `demo.ref_countries` contiene exactamente 5 registros activos.

---

## Grupo 3: Suite de Validación Shift-Left (Stage 1)
> **Objetivo**: Implementar la suite de pruebas automáticas en Python que evalúa el archivo fuente en el Pull Request antes de tocar Databricks.

- [x] **Tarea 3.1 · Dependencias de Desarrollo y Validación**:
  - Crear `requirements-dev.txt`: Especificar librerías mínimas necesarias (`pytest>=8.0.0`, `databricks-sql-connector>=3.0.0`).
- [x] **Tarea 3.2 · Validador de Contrato de Datos (`validate_contract.py`)**:
  - Crear `framework/validation/validate_contract.py`: Módulo en Python con funciones para:
    - Verificar existencia del archivo [data/source/customers.csv](file:///Users/rosa/Proyectos/utec/sdd/data/source/customers.csv).
    - Verificar que la cabecera contenga exactamente las 5 columnas requeridas (`customer_id`, `name`, `age`, `country`, `email`).
    - Detectar y cuantificar anomalías sintácticas en el archivo (filas con edades no numéricas, nombres vacíos, emails inválidos y duplicados).
- [x] **Tarea 3.3 · Tests Automatizados con Pytest (`test_source_contract.py`)**:
  - Crear `framework/tests/test_source_contract.py`: Suite de tests `pytest` que:
    - Test 1: Comprueba que el archivo fuente existe y no está vacío.
    - Test 2: Comprueba la presencia exacta de las 5 columnas en la cabecera.
    - Test 3: Comprueba que el identificador `customer_id` no contenga nulos.
    - Test 4: Emite advertencias estructuradas sobre las anomalías conocidas que serán saneadas en la Fase 2.

---

## Grupo 4: Orquestación CI/CD en GitHub Actions
> **Objetivo**: Configurar el workflow de Pull Request para ejecutar los Stages 1 y 2 de forma automatizada.

- [x] **Tarea 4.1 · Workflow de Pull Request (`ci-pr-phase1.yml`)**:
  - Crear `.github/workflows/ci-pr-phase1.yml`:
    - Trigger: `pull_request` con destino a `main`.
    - Job 1 (`stage-1-shift-left-validation`):
      - Configura Python 3.11, instala `requirements-dev.txt` y ejecuta `pytest framework/tests/test_source_contract.py`.
    - Job 2 (`stage-2-deploy-model`):
      - Depende de Job 1 (solo corre si el Stage 1 pasa en verde).
      - Configura secretos de Databricks (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_HTTP_PATH`).
      - Ejecuta `python framework/deployment/deploy_model.py`.
      - Falla si no se pueden crear las tablas o si `ref_countries` no tiene los 5 registros.

---

## Grupo 5: Documentación y Verificación
> **Objetivo**: Documentar los componentes creados en el README y verificar los criterios de aceptación.

- [x] **Tarea 5.1 · Documentación en README**:
  - Modificar [README.md](file:///Users/rosa/Proyectos/utec/sdd/README.md): Añadir sección de la Fase 1 detallando qué hace cada script, en qué stage corre y cómo ejecutar las pruebas localmente.
- [x] **Tarea 5.2 · Comprobación contra Criterios de Aceptación**:
  - Validar exhaustivamente cada casilla de [specs/2026-10-20-fase-1-diseno-shift-left/validacion.md](file:///Users/rosa/Proyectos/utec/sdd/specs/2026-10-20-fase-1-diseno-shift-left/validacion.md).

