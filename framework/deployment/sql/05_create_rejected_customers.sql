-- =============================================================================
-- Stage 2: Despliegue del Modelo - Tabla de Rechazados
-- Objeto: demo.rejected_customers
-- =============================================================================

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
