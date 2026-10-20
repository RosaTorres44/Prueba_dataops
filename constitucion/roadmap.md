# Constitución · Roadmap de Implementación

El proyecto **ClientesConfiables** se estructura en exactamente **DOS fases secuenciales** que abarcan el ciclo de vida completo del producto de datos: desde el modelado y la prevención temprana de errores (*shift-left*), hasta la ingesta, transformación, agregación y monitoreo continuo en producción.

---

## Fase 1 · Diseño y Calidad Shift-Left

### Objetivo en una línea
Formalizar el modelo lógico y físico de datos, desplegar las tablas en Databricks SQL Warehouse e implementar la validación automatizada del archivo de origen en el Pull Request antes de cualquier ingesta.

### Dependencia
**Ninguna**. Es la fase inicial y base fundamental del producto.

### Qué entrega
1. **Modelado y Scripts DDL Versionados**:
   - Scripts SQL de creación idempotente (`CREATE TABLE IF NOT EXISTS`) para todas las entidades en el schema `demo` de Databricks:
     - `demo.ref_countries`: Catálogo de países (PE, CL, CO, MX, AR) y regiones.
     - `demo.bronze_customers`: Tabla cruda de ingesta con metadatos de auditoría.
     - `demo.silver_customers`: Tabla limpia y tipada con columnas derivadas (`es_mayor_edad`, `es_contactable`).
     - `demo.rejected_customers`: Tabla de aislamiento de anomalías con motivo de rechazo y trazabilidad.
     - `demo.gold_customers_kpi`: Tabla agregada analítica sin datos personales (PII).
   - Script de población inicial de la tabla dimensional `ref_countries`.
2. **Suite de Calidad Shift-Left (Stage 1)**:
   - Script en Python con suite de pruebas (`pytest` o validador de contrato) que se ejecuta en el runner de CI de GitHub Actions.
   - Valida la integridad física del archivo [data/source/customers.csv](file:///Users/rosa/Proyectos/utec/sdd/data/source/customers.csv):
     - Existencia de cabeceras requeridas (`customer_id`, `name`, `age`, `country`, `email`).
     - Tipos sintácticos básicos y ausencia de archivos corruptos o vacíos.
     - Detección temprana de registros no procesables antes de tocar Databricks.
3. **Workflow Inicial de CI/CD**:
   - Flujo de GitHub Actions activado en Pull Requests hacia la rama `main`.
   - Ejecuta el Stage 1 (calidad shift-left) y el Stage 2 (despliegue/verificación del DDL en Databricks con los 3 secrets).
   - Rama de trabajo dedicada (`fase-1-diseno-shift-left`) con Pull Request validado en verde.

---

## Fase 2 · Pipeline de Punta a Punta

### Objetivo en una línea
Construir y orquestar el pipeline automatizado end-to-end desde la ingesta cruda en Bronze hasta las métricas analíticas en Gold, aplicando reglas de calidad, aislamiento de rechazados y monitoreo con merge condicionado a pruebas en verde.

### Dependencia
**Depende de la Fase 1** (requiere las tablas creadas en Databricks, las credenciales configuradas y las validaciones shift-left operativas).

### Qué entrega
1. **Stage 3 · Ingesta a Bronze**:
   - Script de ingesta idempotente que carga el lote de [data/source/customers.csv](file:///Users/rosa/Proyectos/utec/sdd/data/source/customers.csv) en `demo.bronze_customers`.
   - Inyección de metadatos de trazabilidad: `execution_id`, `source_file` e `ingested_at`.
2. **Stage 4 · Calidad de Datos (Silver + Rechazados)**:
   - Lógica de validación, filtrado y deduplicación:
     - Separación de duplicados exactos (1 registro a Silver, duplicados adicionales a `rejected_customers`).
     - Rechazo total de conflictos de identidad (mismo `customer_id` con datos divergentes van a `rejected_customers`).
     - Tratamiento de menores de edad como registros válidos en Silver (`es_mayor_edad = FALSE` y `es_contactable = FALSE`).
     - Clasificación y desvío de registros con errores (nombres vacíos, correos mal formados, edades no numéricas, países ausentes) hacia `rejected_customers` documentando el motivo exacto.
   - Evaluación del umbral de calidad: si la tasa de rechazo supera el $20\%$, el pipeline falla inmediatamente y detiene la carga.
3. **Stage 5 · Agregación Analítica Gold**:
   - Cálculo de métricas de negocio para BI (Andrés): total de clientes, total de contactables, porcentaje de contactabilidad y distribución por país y región.
   - Garantía de $0\%$ de fuga de PII (sin nombres ni correos en Gold).
4. **Stage 6 · Monitoreo, Auditoría y Alertas**:
   - Generación de bitácora consolidada de ejecución con métricas operativas (filas leídas, rechazadas, contactables, estado final).
   - Mecanismo de alerta temprana ante fallos o retrasos que puedan comprometer el SLA de las 8:00 a. m.
5. **Pipeline Completo Listo para Ejecutar**:
   - Workflow integral de GitHub Actions que ejecuta los 6 stages secuenciales.
   - Operativo de punta a punta con la sola configuración de los 3 secrets (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_HTTP_PATH`).
   - Documentación exhaustiva en el README sobre la función y stage de cada script.
   - Merge a `main` únicamente tras ejecución exitosa en verde.
