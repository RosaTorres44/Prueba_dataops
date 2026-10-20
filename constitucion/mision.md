# Constitución · Misión y Visión de Negocio

## 1. El PARA QUÉ del dato

### Problema de Negocio
Actualmente, el equipo de Marketing / CRM (liderado por Carmen) ejecuta campañas semanales por correo electrónico cada lunes dirigidas a clientes de la organización. Sin embargo, enfrentan una tasa crítica de rebotes y fallos de entrega sin visibilidad de las causas raíz.

La fuente de datos transaccional ([data/source/customers.csv](file:///Users/rosa/Proyectos/utec/sdd/data/source/customers.csv)) presenta serias deficiencias de calidad de datos:
- Correos electrónicos con formato inválido, sin dominio o nulos.
- Nombres de clientes vacíos o compuestos únicamente por espacios en blanco.
- Edades no numéricas o nulas.
- Clientes con país no registrado.
- Registros duplicados y potenciales conflictos de identidad por identificador (`customer_id`).
- Falta de identificación explícita de clientes menores de edad, lo que expone a la organización a contingencias legales y regulatorias de privacidad de datos al enviar comunicaciones comerciales a menores.

Adicionalmente, el equipo de Analítica / BI (liderado por Andrés) carece de una visión consolidada, limpia y oportuna por país y región para monitorear el desempeño del padrón antes de las 8:00 a. m. de cada lunes, mientras que Gobierno y Seguridad (liderado por Patricia) exige que los datos de contacto personal (email) no se divulguen en reportes ni se expongan credenciales en repositorios.

**ClientesConfiables** nace para transformar este origen crudo y deficiente en un producto de datos certificado, robusto y confiable, garantizando la elegibilidad de contacto, protegiendo los datos personales y asegurando trazabilidad integral de cada ejecución.

---

### Audiencia y Stakeholders
1. **Marketing / CRM (Carmen)**:
   - *Necesidad*: Disponer cada lunes de una lista depurada de clientes aptos para ser contactados por email, identificando sin cálculos adicionales si son mayores de edad y contactables.
   - *Valor recibido*: Reducción drástica de correos rebotados y foco en audiencias efectivas y legales.
2. **Analítica / BI (Andrés)**:
   - *Necesidad*: Métricas agregadas y confiables por país y región, disponibles puntualmente los lunes antes de las 8:00 a. m.
   - *Valor recibido*: Reporte ejecutivo en la capa Gold sin exposición de datos personales (PII) y alerta temprana en caso de anomalías.
3. **Gobierno de Datos y Seguridad (Patricia)**:
   - *Necesidad*: Salvaguardar los datos personales (email fuera de reportes analíticos), cumplimiento de la prohibición de contactar menores de edad, y aislamiento de registros inválidos en una tabla de rechazados con motivo explícito para corrección en origen.
   - *Valor recibido*: Trazabilidad por `execution_id`, segregación de roles y pista de auditoría completa de anomalías.
4. **Ingeniería de Datos (Raúl)**:
   - *Necesidad*: Pipeline totalmente automatizado, idempotente, gobernado por CI/CD en GitHub Actions y probado tempranamente (*shift-left*).
   - *Valor recibido*: Entregables reproducibles con código versionado, ramas protegidas y cero creación manual de objetos en Databricks.

---

## 2. Alcance del Proyecto (Scope)

### Qué queda DENTRO del proyecto (IN-SCOPE)
- **Validación Shift-Left**: Verificación automática de contrato (esquema, tipos, reglas de formato) sobre [data/source/customers.csv](file:///Users/rosa/Proyectos/utec/sdd/data/source/customers.csv) en cada Pull Request antes de interactuar con la plataforma de datos.
- **Definición y despliegue del modelo de datos**: Scripts DDL automatizados e idempotentes en Databricks SQL Warehouse (schema `demo`) para todas las capas.
- **Ingesta Bronze (`bronze_customers`)**: Almacenamiento crudo e inmutable del CSV con metadatos de auditoría (`execution_id`, timestamp de carga, archivo origen).
- **Capa dimensional de referencia (`ref_countries`)**: Tabla maestra con catálogo de países (código ISO-2: PE, CL, CO, MX, AR), nombres oficiales y regiones geográficas.
- **Capa Silver (`silver_customers`)**: Limpieza, estandarización, tipado, deduplicación y cálculo de banderas de negocio:
  - `es_mayor_edad`: `TRUE` si `age >= 18`, `FALSE` si `age < 18`.
  - `es_contactable`: `TRUE` si el cliente tiene email válido, no nulo y `es_mayor_edad = TRUE`.
- **Aislamiento de rechazados (`rejected_customers`)**: Tabla de anomalías donde se almacena el registro original, motivo específico del rechazo, `execution_id` y timestamp.
- **Capa Gold (`gold_customers_kpi`)**: Tabla agregada a nivel de país y región con indicadores de contactabilidad, volumen de clientes y distribución por edad, **100% libre de datos personales (sin nombres ni correos)**.
- **Control de calidad y alertas**: Evaluación de umbral de rechazos ($\le 20\%$). Si se excede, el pipeline detiene la carga e impide la publicación de datos corruptos.
- **Orquestación CI/CD y Monitoreo**: Workflow en GitHub Actions ejecutable mediante 3 secrets, registrando bitácora de cada ejecución.

### Qué queda FUERA del proyecto (OUT-OF-SCOPE)
- **Herramienta de envío de correos (ESP / CRM mailing engine)**: ClientesConfiables prepara y certifica el dato; la ejecución de campañas de email marketing o integraciones con HubSpot/Salesforce queda fuera.
- **Saneamiento automático del CRM de origen**: Los registros defectuosos se aíslan y documentan en `rejected_customers`, pero la corrección física de la base transaccional original corresponde a los dueños del CRM.
- **Desarrollo de tableros visuales externos**: No incluye dashboards en herramientas de visualización como Power BI, Tableau o Looker (se proporciona la capa Gold modelada y optimizada para su consumo directo).
- **Ingesta en tiempo real o streaming**: El ciclo del producto es estrictamente batch semanal.

---

## 3. Cómo se ve el éxito (KPI medible y Criterios de Aceptación)

### KPI Principal de Negocio
- **Indicador**: **Porcentaje de Clientes Contactables** ($\% \text{ Contactabilidad}$).
- **Fórmula de cálculo**:
  $$\% \text{ Clientes Contactables} = \left( \frac{\text{Total de registros en Silver con } \texttt{es\_contactable = TRUE}}{\text{Total de registros limpios en Silver}} \right) \times 100$$
- **Línea base estimada en origen**: $\sim 50\%$ (debido al impacto de formatos defectuosos, menores de edad, registros sin país y duplicados en [customers.csv](file:///Users/rosa/Proyectos/utec/sdd/data/source/customers.csv)).
- **Meta de éxito acordada**: **Alcanzar al menos un $80\%$ de clientes contactables** sobre el padrón activo procesado en Silver.

### SLAs Operacionales y de Calidad
1. **SLA de Entrega y Oportunidad**:
   - Disponibilidad garantizada de la tabla Gold actualizada **cada lunes antes de las 8:00 a. m.**
2. **SLA de Calidad de Ingesta (Umbral de Rechazo)**:
   - La tasa de registros rechazados por ejecución no debe superar el **$20\%$** del total de filas procesadas:
     $$\text{Tasa de Rechazo} = \frac{\text{Filas en } \texttt{rejected\_customers}}{\text{Filas en } \texttt{bronze\_customers}} \times 100 \le 20\%$$
   - Si la tasa de rechazo supera el 20%, el pipeline aborta la ejecución en el Stage 4, evitando la contaminación de Gold y notificando la alerta a Ingeniería y Analítica.
3. **SLA de Privacidad y Gobierno**:
   - **$0\%$ de fuga de PII**: Cero correos electrónicos o nombres personales expuestos en la capa Gold o en vistas públicas de reportería.
4. **SLA de Trazabilidad y Repetibilidad**:
   - **$100\%$ de registros auditables**: Cada fila en Bronze, Silver, Rechazados y Gold posee un identificador de corrida (`execution_id`) y fecha de procesamiento.
   - **Idempotencia total**: La reejecución del pipeline sobre el mismo lote de origen no genera registros duplicados ni altera las métricas históricas.
