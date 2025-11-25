# Sistema de Guardado Incremental de Experimentos

## Descripción

El sistema de experimentos paralelos ahora guarda los resultados de cada simulación **inmediatamente** después de completarse, en lugar de esperar a que todas terminen. Esto previene la pérdida de datos si el proceso falla a mitad de ejecución.

## Estructura de Carpetas

Cada experimento crea una estructura organizada:

```
results/experiments/
└── experimento_20241124_150000/          # Carpeta del experimento con timestamp
    ├── run_001_sin_control_seed42/        # Carpeta individual por simulación
    │   ├── datos_completos.csv            # Datos completos de la simulación
    │   ├── resumen.json                   # Métricas resumidas
    │   ├── parametros.yaml                # Parámetros usados
    │   └── .completado                    # Marca que terminó exitosamente
    ├── run_002_lsm_seed42/
    │   ├── datos_completos.csv
    │   ├── resumen.json
    │   ├── parametros.yaml
    │   └── .completado
    ├── run_003_itn_irs_seed42/
    │   ├── datos_completos.csv
    │   ├── resumen.json
    │   ├── parametros.yaml
    │   └── .error                         # Marca que falló (si ocurrió un error)
    ├── ...
    ├── resumen_experimentos.csv           # Resumen consolidado
    ├── datos_consolidados.csv             # Todos los datos juntos
    ├── configuracion.yaml                 # Configuración del experimento
    └── timestamp.txt                      # Timestamp de inicio
```

## Ventajas

### 1. **Sin pérdida de datos**
Si el proceso falla en la simulación #12 de 16, aún tienes los resultados de las primeras 11 simulaciones guardadas en disco.

### 2. **Recuperación fácil**
Puedes usar el script `recuperar_experimento.py` para consolidar los resultados parciales:

```bash
python recuperar_experimento.py --dir results/experiments/experimento_20241124_150000
```

### 3. **Monitoreo en tiempo real**
Puedes ver qué simulaciones se han completado mientras otras aún están corriendo:

```bash
# Ver cuántas simulaciones se han completado
ls results/experiments/experimento_20241124_150000/ | grep "run_" | wc -l

# Ver cuáles se completaron exitosamente
find results/experiments/experimento_20241124_150000/ -name ".completado"
```

### 4. **Depuración más fácil**
Cada simulación tiene su propia carpeta, facilitando encontrar y analizar problemas específicos.

## Uso Básico

### Ejecutar Experimentos

```bash
# Usar configuración por defecto
python run_parallel_experiments.py

# Usar configuración personalizada
python run_parallel_experiments.py --config config/mi_config.yaml

# Cambiar número de procesos paralelos
python run_parallel_experiments.py --processes 8

# Usar semillas específicas
python run_parallel_experiments.py --seeds 100 200 300 400

# Cambiar directorio de salida
python run_parallel_experiments.py --output-dir results/mis_experimentos
```

### Recuperar Resultados Parciales

Si el experimento se interrumpe:

```bash
python recuperar_experimento.py --dir results/experiments/experimento_20241124_150000
```

Este script:
- ✅ Identifica qué simulaciones se completaron exitosamente
- ✅ Consolida los resultados disponibles
- ✅ Genera archivos de resumen
- ✅ Muestra estadísticas por estrategia
- ✅ Crea un reporte de qué falló y qué está pendiente

## Archivos Generados por Simulación

### `datos_completos.csv`
Datos de todos los pasos de la simulación con columnas:
- Estados humanos: Susceptibles, Expuestos, Infectados, Recuperados
- Estados mosquitos: Mosquitos_S, Mosquitos_I, Mosquitos_Total
- Ambiente: Huevos, Temperatura, Precipitacion, Sitios_Temporales
- Intervenciones: LSM_Activo, ITN_IRS_Activo
- Metadatos: seed, estrategia, usar_lsm, usar_itn_irs, run_id

### `resumen.json`
Métricas agregadas:
```json
{
  "run_id": 1,
  "seed": 42,
  "estrategia": "sin_control",
  "usar_lsm": false,
  "usar_itn_irs": false,
  "total_infectados": 150,
  "total_recuperados": 145,
  "pico_infectados": 45,
  "dia_pico": 67,
  "mosquitos_finales": 8500,
  "mosquitos_infectados_finales": 120,
  "tasa_ataque": 2.95
}
```

### `parametros.yaml`
Configuración completa usada en la simulación (útil para reproducibilidad).

### `.completado`
Archivo vacío que marca que la simulación terminó exitosamente.

### `.error`
Archivo que contiene el mensaje de error si la simulación falló.

## Archivos Consolidados

### `resumen_experimentos.csv`
Una fila por simulación con todas las métricas.

### `datos_consolidados.csv`
Todos los datos de todas las simulaciones juntos (útil para análisis comparativo).

### `configuracion.yaml`
Configuración del experimento completo, incluyendo:
- Configuración del modelo
- Semillas usadas
- Número de procesos
- Estadísticas de completadas/fallidas

## Casos de Uso

### Ejemplo 1: Experimento se interrumpe
```bash
# Inicia experimento
python run_parallel_experiments.py

# ... se interrumpe en simulación 10 de 16 ...

# Recuperar lo que se completó
python recuperar_experimento.py --dir results/experiments/experimento_20241124_150000

# Genera:
# - resumen_experimentos_recuperado.csv (10 simulaciones)
# - datos_consolidados_recuperado.csv (10 simulaciones)
# - recuperacion_metadata.yaml (info de qué faltó)
```

### Ejemplo 2: Ver progreso durante ejecución
```bash
# En una terminal: ejecutar experimento
python run_parallel_experiments.py

# En otra terminal: monitorear progreso
watch -n 5 'find results/experiments/experimento_*/  -name ".completado" | wc -l'
```

### Ejemplo 3: Analizar simulación específica
```bash
# Si la simulación #5 tuvo resultados interesantes
cd results/experiments/experimento_20241124_150000/run_005_lsm_seed123/

# Ver resumen
cat resumen.json

# Analizar datos completos
python -c "
import pandas as pd
df = pd.read_csv('datos_completos.csv')
print(df.describe())
print(df[['Infectados', 'Mosquitos_I']].plot())
"
```

## Comparación con Sistema Anterior

| Aspecto | Anterior | Nuevo |
|---------|----------|-------|
| Guardado | Al final de todo | Inmediato por simulación |
| Pérdida si falla | Todo el trabajo | Solo simulaciones incompletas |
| Recuperación | Imposible | Script de recuperación |
| Organización | Archivos sueltos | Carpetas por simulación |
| Monitoreo | Solo al final | Tiempo real |
| Debugging | Difícil | Fácil (carpetas individuales) |

## Notas Técnicas

- Los procesos paralelos escriben en carpetas diferentes, evitando conflictos
- Los archivos `.completado` y `.error` permiten identificación rápida de estado
- El formato JSON para resumen facilita procesamiento automático
- Los timestamps en carpetas evitan sobrescribir experimentos anteriores
