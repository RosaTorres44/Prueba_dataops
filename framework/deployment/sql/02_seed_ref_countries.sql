-- =============================================================================
-- Stage 2: Despliegue del Modelo - Seeding de Datos Maestros de Países
-- Objeto: demo.ref_countries (PE, CL, CO, MX, AR)
-- =============================================================================

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
