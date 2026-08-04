# Contexto del Proyecto: Material Consumption Prediction con SAP AI Core

**Fecha:** 4 de agosto de 2026  
**Proyecto:** `material-consumption-ai`  
**Objetivo:** Predecir el consumo diario de materiales usando SAP AI Core, con visualización en SAP CAP + Fiori Elements.

---

## Lo que se hizo

### 1. Activación de SAP AI Core en BTP

- Se resolvió el error `"paid service plans are not allowed for your space"` habilitando los planes de pago en el Space de Cloud Foundry:
  ```bash
  cf create-space-quota paid-quota --allow-paid-service-plans
  cf set-space-quota <SPACE_NAME> paid-quota
  ```
- La instancia `ai_core` fue creada exitosamente en el subaccount de BTP.

---

### 2. Estructura del Proyecto Generado

El archivo `material-consumption-ai.zip` contiene un proyecto completo listo para cargar en SAP Business Application Studio (BAS).

```
material-consumption-ai/
├── .aicore/
│   ├── training-pipeline.yaml     # Argo Workflow — entrena el modelo
│   └── serving-template.yaml      # KServe template — sirve predicciones
├── src/
│   ├── train.py                   # Entrena RandomForestRegressor con lag features
│   ├── serve.py                   # API Flask/KServe en puerto 9001
│   ├── utils.py                   # Helpers: feature engineering, holidays, paydays
│   └── generate_sample_data.py    # Generador de datos de prueba adicionales
├── Dockerfile.train               # Imagen Docker para entrenamiento
├── Dockerfile.serve               # Imagen Docker para serving
├── requirements-train.txt
├── requirements-serve.txt
├── cap-app/
│   ├── db/schema.cds              # Entidades: Materials, ConsumptionHistory, MaterialPredictions
│   ├── db/data/
│   │   ├── consumption-Materials.csv         # 5 materiales de muestra
│   │   └── consumption-ConsumptionHistory.csv # 3,655 registros (2 años, 5 materiales)
│   ├── srv/consumption-service.cds           # OData service definition
│   ├── srv/consumption-service.js            # Lógica del service + acción refreshPredictions
│   ├── srv/aicore-client.js                  # Cliente HTTP para llamar al endpoint de AI Core
│   ├── .env.example                          # Plantilla de variables de entorno
│   ├── app/consumption-history/              # List Report: histórico de consumo
│   │   ├── annotations.cds
│   │   └── webapp/manifest.json
│   └── app/predictions/                      # List Report: predicciones del día actual
│       ├── annotations.cds
│       └── webapp/manifest.json
└── notebooks/
    └── 01_setup_aicore.ipynb      # Setup completo paso a paso con AI Core SDK
```

---

### 3. Modelo de Machine Learning

- **Algoritmo:** `RandomForestRegressor` (scikit-learn)
- **Target:** Cantidad de consumo de material por día
- **Features del modelo:**

| Feature | Descripción |
|---|---|
| `material_encoded` | Material ID codificado (LabelEncoder) |
| `day_of_week` | 0 = Lunes … 6 = Domingo |
| `month` | 1 – 12 |
| `week_of_year` | 1 – 53 |
| `day_of_month` | 1 – 31 |
| `is_holiday` | Día feriado (0/1) |
| `is_weekend` | Sábado o domingo (0/1) |
| `is_payday` | Día de pago — 1ro y 15 del mes (0/1) |
| `lag_7d` | Consumo hace 7 días (mismo material) |
| `lag_14d` | Consumo hace 14 días |
| `lag_28d` | Consumo hace 28 días |
| `rolling_4w_avg` | Promedio del mismo día de semana en las últimas 4 semanas |

---

### 4. Aplicación CAP + Fiori Elements

- **Servicio OData v4:** `ConsumptionService` en `/odata/v4/consumption/`
- **Entidades:**
  - `Materials` — maestro de materiales
  - `ConsumptionHistory` — histórico de consumo
  - `MaterialPredictions` — predicciones generadas por AI Core
- **Acción:** `POST /consumption/refreshPredictions` — llama al endpoint de AI Core y almacena las predicciones del día actual
- **List Reports:**
  - `/consumption-history/` — Comportamiento histórico con filtros por material, fecha, feriado, fin de semana, día de pago
  - `/predictions/` — Predicciones del día actual por material

---

## Próximos Pasos

### Paso 1 — Preparar y publicar la imagen Docker

```bash
# Imagen de entrenamiento
docker build -f Dockerfile.train -t <TU_REGISTRY>/consumption-train:latest .
docker push <TU_REGISTRY>/consumption-train:latest

# Imagen de serving
docker build -f Dockerfile.serve -t <TU_REGISTRY>/consumption-serve:latest .
docker push <TU_REGISTRY>/consumption-serve:latest
```

> Reemplaza `<TU_REGISTRY>` en ambos archivos `.aicore/*.yaml` antes de hacer push.

---

### Paso 2 — Subir los datos de entrenamiento al Object Store

1. Sube `cap-app/db/data/consumption-ConsumptionHistory.csv` a tu bucket (S3, Azure Blob o SAP BTP Object Store Service) con el path:
   ```
   consumption-ai/data/consumption.csv
   ```
2. Asegúrate de que el nombre del archivo sea exactamente `consumption.csv` (el script `train.py` lo espera en `/app/data/consumption.csv`).

---

### Paso 3 — Hacer push del repositorio a Git

AI Core lee los workflow templates desde un repositorio Git. El folder `.aicore/` debe estar en la raíz del repo.

```bash
git init
git add .
git commit -m "Initial commit - material consumption AI project"
git remote add origin https://github.com/<tu-org>/<tu-repo>.git
git push -u origin main
```

---

### Paso 4 — Ejecutar el notebook de setup

Abre `notebooks/01_setup_aicore.ipynb` en BAS o Jupyter y ejecuta las celdas en orden:

1. Instalar dependencias (`ai-core-sdk`)
2. Conectar con AI Core (credenciales del Service Key)
3. Crear el Resource Group
4. Registrar el repositorio Git
5. Registrar el Object Store Secret
6. Registrar el Docker Registry Secret
7. Registrar el artifact (datos de entrenamiento)
8. Crear la configuración de entrenamiento
9. Lanzar la ejecución (`POST /lm/executions`)
10. Monitorear hasta estado `COMPLETED`
11. Registrar el modelo resultante como artifact
12. Crear configuración de serving
13. Crear deployment (`POST /lm/deployments`)
14. Probar el endpoint de predicción

---

### Paso 5 — Configurar y ejecutar la aplicación CAP

```bash
cd cap-app
cp .env.example .env
```

Editar `.env` con las credenciales del Service Key de AI Core:

```env
AICORE_URL=https://<...>.ai.ml.hana.ondemand.com
AICORE_TOKEN_URL=https://<...>.authentication.sap.hana.ondemand.com
AICORE_CLIENT_ID=<clientid>
AICORE_CLIENT_SECRET=<clientsecret>
AICORE_RESOURCE_GROUP=material-consumption
AICORE_DEPLOYMENT_URL=https://<...>.inference.ml.hana.ondemand.com
```

```bash
npm install
npm run dev
```

---

### Paso 6 — Conectar a datos reales (opcional)

Reemplaza los CSV de muestra con datos reales de tu sistema SAP:
- Exporta el histórico de movimientos de materiales (p. ej. desde SAP S/4HANA vía transacción `MB51` o API de inventario)
- Ajusta las columnas del CSV para que coincidan con el schema de `ConsumptionHistory`
- Actualiza `HOLIDAYS` en `src/utils.py` con el calendario de feriados de tu país/región

---

### Paso 7 — Ajuste del modelo (cuando tengas datos reales)

- Evalúa las métricas `MAE` y `R²` que se imprimen al final del entrenamiento
- Si el desempeño no es suficiente, ajusta los hiperparámetros en la configuración de AI Core (`n_estimators`, `max_depth`) o reemplaza el algoritmo por XGBoost o LightGBM en `src/train.py`
- Para un modelo por material (en vez de uno global), modifica el loop en `train.py` para separar los datos por `material_id`

---

## Notas importantes

- Los datos de muestra incluidos son **sintéticos** (generados con patrones realistas). Deben reemplazarse con datos reales antes de ir a producción.
- El día de pago está definido como el **1ro y 15 de cada mes**. Ajusta `PAYDAY_DAYS` en `src/utils.py` según tu política.
- La acción `refreshPredictions` calcula automáticamente `is_weekend` e `is_holiday` para el día actual. Para `is_payday`, usa la misma lógica o intégrala con tu sistema de RRHH/nómina.
- El endpoint de predicción de AI Core requiere que el deployment esté en estado `RUNNING`. Verifica el estado antes de llamar `refreshPredictions`.
