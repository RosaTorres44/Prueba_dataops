-- =============================================================================
-- Stage 2: Despliegue del Modelo - Capa Bronze (Crudo)
-- Objeto: demo.bronze_customers
-- =============================================================================

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
COMMENT 'Capa Bronze: Almacenamiento crudo del lote de clientes con metadatos de auditoría';
