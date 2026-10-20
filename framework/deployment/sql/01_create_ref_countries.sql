-- =============================================================================
-- Stage 2: Despliegue del Modelo - Catálogo de Países y Regiones
-- Objeto: demo.ref_countries
-- =============================================================================

CREATE TABLE IF NOT EXISTS demo.ref_countries (
    country_code STRING NOT NULL COMMENT 'Código ISO-2 del país (PK)',
    country_name STRING NOT NULL COMMENT 'Nombre oficial del país',
    region STRING NOT NULL COMMENT 'Región geográfica',
    CONSTRAINT pk_ref_countries PRIMARY KEY (country_code)
)
USING DELTA
COMMENT 'Tabla dimensional de referencia de países y regiones';
