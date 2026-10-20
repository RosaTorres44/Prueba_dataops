-- =============================================================================
-- Stage 2: Despliegue del Modelo - Capa Gold (Métricas Agregadas Sin PII)
-- Objeto: demo.gold_customers_kpi
-- =============================================================================

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
