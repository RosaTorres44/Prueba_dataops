-- =============================================================================
-- Stage 2: Despliegue del Modelo - Capa Silver (Limpio y Banderas)
-- Objeto: demo.silver_customers
-- =============================================================================

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
