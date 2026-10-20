# Especificación de Requerimientos · Fase 1: Diseño y Calidad Shift-Left

**Fase**: Fase 1 · Diseño y calidad shift-left  
**Fecha**: 2026-10-20  
**Rama de Git**: `fase-1-diseno-shift-left`  
**Estado**: Borrador para aprobación  
**Documentos de referencia**: [constitucion/mision.md](file:///Users/rosa/Proyectos/utec/sdd/constitucion/mision.md) y [constitucion/stack-tecnologico.md](file:///Users/rosa/Proyectos/utec/sdd/constitucion/stack-tecnologico.md)

---

## 1. Scope (Alcance)

### 1.1 Qué construye esta fase (IN-SCOPE)
1. **Scripts DDL del Modelo de Datos (Stage 2)**:
   - Definición formal en archivos SQL de las 5 tablas que componen la arquitectura en Databricks SQL Warehouse (schema `demo`):
     - `demo.ref_countries`: Catálogo maestro de países y regiones.
     - `demo.bronze_customers`: Tabla cruda de ingesta con metadatos de auditoría.
     - `demo.silver_customers`: Tabla limpia y tipada con banderas de contacto y mayoría de edad.
     - `demo.rejected_customers`: Tabla de anomalías para aislamiento de datos inválidos y auditoría.
     - `demo.gold_customers_kpi`: Tabla agregada analítica sin PII para consumo de BI.
   - Script SQL de inserción y seeding de datos maestros en `demo.ref_countries` para los países de operación (PE, CL, CO, MX, AR).
2. **Suite de Validación Shift-Left (Stage 1)**:
   - Script en Python ejecutable localmente y en el runner de CI de GitHub Actions.
   - Verificación de contrato y calidad del archivo fuente [data/source/customers.csv](file:///Users/rosa/Proyectos/utec/sdd/data/source/customers.csv) antes de cualquier interacción con Databricks:
     - Validación de estructura de cabecera y presencia de las 5 columnas requeridas.
     - Detección sintáctica de formatos defectuosos, valores nulos y tipos no conformes.
3. **Módulo de Despliegue Automatizado (Stage 2)**:
   - Script en Python (`deploy_model.py`) que se conecta a Databricks SQL Warehouse mediante el conector oficial `databricks-sql-connector` usando los 3 secrets de GitHub, ejecuta los DDL de manera idempotente (`CREATE TABLE IF NOT EXISTS`) y siembra los datos de `ref_countries`.
4. **Workflow de Integración Continua (CI en PR)**:
   - Pipeline de GitHub Actions que corre ante cada Pull Request hacia `main`, ejecutando secuencialmente el Stage 1 y el Stage 2.

### 1.2 Qué NO construye esta fase (OUT-OF-SCOPE - Reservado para Fase 2)
- Ingesta de datos de clientes a `demo.bronze_customers` (Stage 3).
- Lógica de transformación, filtrado de calidad, deduplicación y poblado de `demo.silver_customers` y `demo.rejected_customers` (Stage 4).
- Cálculo y poblado de métricas analíticas agregadas en `demo.gold_customers_kpi` (Stage 5).
- Monitoreo consolidado de ejecuciones de producción de los días lunes (Stage 6).

---

## 2. Datos de Entrada y Salida (Contrato del Dato)

### 2.1 Entrada: Archivo Fuente de CRM
- **Ruta**: `data/source/customers.csv`
- **Formato**: CSV delimitado por comas, codificación UTF-8.
- **Columnas y Contrato de Entrada**:
  | Columna | Tipo Esperado | Nulable | Descripción |
  | :--- | :--- | :--- | :--- |
  | `customer_id` | Alfanumérico (ej. `C001`) | No | Identificador asignado por el CRM |
  | `name` | Texto | No | Nombre completo del cliente |
  | `age` | Numérico entero ($\ge 0$) | No | Edad en años cumplidos |
  | `country` | Texto (2 letras ISO) | No | Código de país (PE, CL, CO, MX, AR) |
  | `email` | Texto con formato de correo | No | Dirección de correo electrónico |

### 2.2 Salida: Tablas y Objetos en Databricks (Schema `demo`)
- Tablas creadas e inicializadas en Databricks:
  - `demo.ref_countries` (con 5 filas maestras de referencia).
  - `demo.bronze_customers` (estructura lista para recibir datos en Fase 2).
  - `demo.silver_customers` (estructura lista para recibir datos en Fase 2).
  - `demo.rejected_customers` (estructura lista para recibir datos en Fase 2).
  - `demo.gold_customers_kpi` (estructura lista para recibir métricas en Fase 2).

---

## 3. Modelo de Datos y Scripts DDL de Databricks

### 3.1 DDL: Catálogo de Referencia Geográfica (`demo.ref_countries`)
```sql
CREATE TABLE IF NOT EXISTS demo.ref_countries (
    country_code STRING NOT NULL COMMENT 'Código ISO-2 del país (PK)',
    country_name STRING NOT NULL COMMENT 'Nombre oficial del país',
    region STRING NOT NULL COMMENT 'Región geográfica',
    CONSTRAINT pk_ref_countries PRIMARY KEY (country_code)
)
USING DELTA
COMMENT 'Tabla dimensional de referencia de países y regiones';
```

**Script de Seeding de Datos Maestros**:
```sql
MERGE INTO demo.ref_countries AS target
USING (
    SELECT 'PE' AS country_code, 'Perú' AS country_name, 'Sudamérica' AS region UNION ALL
    SELECT 'CL', 'Chile', 'Sudamérica' UNION ALL
    SELECT 'CO', 'Colombia', 'Sudamérica' UNION ALL
    SELECT 'MX', 'México', 'Norteamérica' UNION ALL
    SELECT 'AR', 'Argentina', 'Sudamérica'
) AS source
ON target.country_code = source.country_code
WHEN NOT MATCHED THEN
    INSERT (country_code, country_name, region)
    VALUES (source.country_code, source.country_name, source.region);
```

### 3.2 DDL: Capa Bronze (`demo.bronze_customers`)
```sql
CREATE TABLE IF NOT EXISTS demo.bronze_customers (
    customer_id STRING COMMENT 'Identificador de cliente original',
    name STRING COMMENT 'Nombre original del cliente',
    age STRING COMMENT 'Edad original como texto',
    country STRING COMMENT 'Código de país original',
    email STRING COMMENT 'Correo electrónico original',
    source_file STRING NOT NULL COMMENT 'Nombre del archivo fuente',
    execution_id STRING NOT NULL COMMENT 'UUID identificador de la ejecución',
    ingested_at TIMESTAMP NOT NULL COMMENT 'Timestamp UTC de ingesta'
)
USING DELTA
COMMENT 'Capa Bronze: Almacenamiento crudo del lote de clientes';
```

### 3.3 DDL: Capa Silver (`demo.silver_customers`)
```sql
CREATE TABLE IF NOT EXISTS demo.silver_customers (
    customer_id STRING NOT NULL COMMENT 'Identificador único verificado (PK)',
    name STRING NOT NULL COMMENT 'Nombre normalizado',
    age INT NOT NULL COMMENT 'Edad validada como entero',
    country STRING NOT NULL COMMENT 'Código de país validado contra ref_countries',
    email STRING NOT NULL COMMENT 'Correo electrónico validado sintácticamente',
    es_mayor_edad BOOLEAN NOT NULL COMMENT 'TRUE si age >= 18, FALSE si age < 18',
    es_contactable BOOLEAN NOT NULL COMMENT 'TRUE si email es válido y es_mayor_edad = TRUE',
    execution_id STRING NOT NULL COMMENT 'UUID de la ejecución procesadora',
    processed_at TIMESTAMP NOT NULL COMMENT 'Timestamp UTC del procesamiento',
    CONSTRAINT pk_silver_customers PRIMARY KEY (customer_id)
)
USING DELTA
COMMENT 'Capa Silver: Clientes limpios, deduplicados y con banderas de contacto';
```

### 3.4 DDL: Tabla de Rechazados (`demo.rejected_customers`)
```sql
CREATE TABLE IF NOT EXISTS demo.rejected_customers (
    rejection_id STRING NOT NULL COMMENT 'UUID único del registro rechazado',
    customer_id STRING COMMENT 'customer_id si existía en origen',
    raw_record STRING NOT NULL COMMENT 'Fila original serializada en formato JSON',
    motivo_rechazo STRING NOT NULL COMMENT 'Motivo técnico/negocio del rechazo',
    execution_id STRING NOT NULL COMMENT 'UUID de la ejecución evaluadora',
    rejected_at TIMESTAMP NOT NULL COMMENT 'Timestamp UTC del descarte'
)
USING DELTA
COMMENT 'Tabla de Rechazados: Aislamiento de anomalías de calidad y auditoría';
```

### 3.5 DDL: Capa Gold (`demo.gold_customers_kpi`)
```sql
CREATE TABLE IF NOT EXISTS demo.gold_customers_kpi (
    country_code STRING NOT NULL COMMENT 'Código ISO de país',
    country_name STRING NOT NULL COMMENT 'Nombre del país obtenido de ref_countries',
    region STRING NOT NULL COMMENT 'Región geográfica obtenida de ref_countries',
    total_clientes BIGINT NOT NULL COMMENT 'Total de clientes limpios en Silver',
    total_contactables BIGINT NOT NULL COMMENT 'Total con es_contactable = TRUE',
    total_no_contactables BIGINT NOT NULL COMMENT 'Total con es_contactable = FALSE',
    total_mayores_edad BIGINT NOT NULL COMMENT 'Total con es_mayor_edad = TRUE',
    total_menores_edad BIGINT NOT NULL COMMENT 'Total con es_mayor_edad = FALSE',
    pct_contactabilidad DOUBLE NOT NULL COMMENT 'Porcentaje de contactabilidad (0-100)',
    execution_id STRING NOT NULL COMMENT 'UUID de la corrida de métricas',
    calculated_at TIMESTAMP NOT NULL COMMENT 'Timestamp UTC de generación'
)
USING DELTA
COMMENT 'Capa Gold: Resumen analítico por país y región sin exposición de PII';
```

---

## 4. Reglas de Calidad y Clasificación de Datos

Las reglas que determinan si una fila es admitida en Silver o desviada a Rechazados se definen con rigor en esta especificación para ser implementadas en la Fase 2 y pre-validadas sintácticamente en la suite shift-left de la Fase 1:

| Campo | Regla de Calidad | Acción si incumple | Motivo asignado en `rejected_customers` |
| :--- | :--- | :--- | :--- |
| `customer_id` | No nulo, no vacío, longitud $\ge 2$ | Rechazar | `"customer_id nulo o vacío"` |
| `name` | No nulo, longitud con `TRIM` $\ge 2$ caracteres | Rechazar | `"Nombre ausente o compuesto únicamente por espacios"` |
| `age` | Numérico entero, $0 \le \text{age} \le 120$ | Rechazar | `"Edad ausente o con formato no numérico"` |
| `age < 18` | Regla de negocio de elegibilidad | **Admitir en Silver** | **No se rechaza**. Se asigna `es_mayor_edad = FALSE` y `es_contactable = FALSE` |
| `country` | No nulo, código de 2 letras presente en `ref_countries` | Rechazar | `"País no registrado en catálogo de referencia"` |
| `email` | No nulo, sintaxis estándar RFC (`^[\w\.-]+@[\w\.-]+\.\w{2,}$`) | Rechazar | `"Email con formato inválido o dominio ausente"` |
| Duplicado Exacto | Fila idéntica en todos sus campos | Conservar 1 en Silver, rechazar duplicados | `"Duplicado exacto"` |
| Conflicto de Identidad | Mismo `customer_id` con discrepancia en nombre, edad, país o email | Rechazar **todas** las filas involucradas | `"Conflicto de identidad: customer_id duplicado con datos divergentes"` |

### Política de Umbral de Calidad
- **Tasa de Rechazo Tolerada**: $\le 20\%$.
- En Fase 2, si la proporción de filas en `rejected_customers` excede el 20% del total de filas procesadas en el lote, el Stage 4 fallará con error crítico, interrumpiendo la propagación hacia Gold y emitiendo una alerta para Analítica e Ingeniería.

---

## 5. Restricciones Técnicas y de Gobierno

1. **Seguridad y Credenciales**:
   - Cero tokens o cadenas de conexión en el repositorio.
   - Solo se usarán los 3 secrets de GitHub: `DATABRICKS_HOST`, `DATABRICKS_TOKEN` y `DATABRICKS_HTTP_PATH`.
2. **Protección de Datos Personales (PII)**:
   - La tabla `gold_customers_kpi` está diseñada sin columnas de nombre o email.
   - Los logs generados por la validación shift-left y por el script de despliegue no deben volcar correos electrónicos a la consola de GitHub Actions.
3. **Idempotencia**:
   - Los scripts DDL son estrictamente idempotentes mediante `CREATE TABLE IF NOT EXISTS` y `MERGE INTO`. Ejecutar el pipeline N veces produce el mismo estado del catálogo.
4. **Costo y Eficiencia**:
   - La validación shift-left corre íntegramente en Python local / runner de GitHub Actions sin encender clusters de Databricks, ahorrando unidades DBU.

---

## 6. Decisiones Tomadas y Justificación

| Decisión Tomada | Alternativa Descartada | Motivo / Justificación |
| :--- | :--- | :--- |
| **Creación anticipada de las 5 tablas en Fase 1** | Crear tablas incrementalmente por fase | Garantiza la integridad del catálogo completo en Databricks y valida permisos y tipos antes de escribir lógica ETL en Fase 2. |
| **Población inmediata de `ref_countries`** | Dejar la tabla vacía hasta la Fase 2 | Permite verificar de inmediato la integridad referencial y las pruebas de cruce geográfico requeridas por Analítica. |
| **Rechazo estricto de nombres vacíos** | Asignar valor por defecto ("Sin Nombre") | Marketing no puede enviar correos comerciales con saludos vacíos o defectuosos ("Hola, "); exige corrección en el CRM de origen. |
| **Rechazo estricto de países no registrados** | Asignar país comodín "XX" | BI necesita reportes geográficos limpios por país y región; los datos huérfanos distorsionan el indicador por región. |
| **Bloqueo de PR ante fallos estructurales** | Aceptar con advertencia | Principio Shift-Left: ningún código o contrato que no compile o presente defectos graves debe mezclarse en la rama `main`. |
