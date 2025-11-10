# Guía de Experimentos en Paralelo (Batch Runner)

Esta guía explica cómo ejecutar múltiples simulaciones en paralelo usando el sistema de batch runner basado en Mesa 2.3.4.

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Instalación y Requisitos](#instalación-y-requisitos)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Configuración de Experimentos](#configuración-de-experimentos)
5. [Ejecución](#ejecución)
6. [Análisis de Resultados](#análisis-de-resultados)
7. [Ejemplos de Escenarios](#ejemplos-de-escenarios)
8. [Optimización de Performance](#optimización-de-performance)

---

## Introducción

El batch runner permite ejecutar múltiples simulaciones en paralelo con diferentes combinaciones de parámetros. Esto es útil para:

- **Análisis de sensibilidad**: ¿Cómo afecta cada parámetro a los resultados?
- **Comparación de estrategias**: ¿Cuál intervención es más efectiva?
- **Calibración del modelo**: Ajustar parámetros a datos reales
- **Estudios de incertidumbre**: Evaluar variabilidad en resultados

### Características

✅ **Paralelización**: Ejecuta múltiples simulaciones simultáneamente usando todos los cores del CPU  
✅ **Flexibilidad**: Define barridos de parámetros en archivos YAML  
✅ **Reproducibilidad**: Cada corrida usa seeds diferentes pero controladas  
✅ **Métricas completas**: Registra 10+ métricas por paso de simulación  
✅ **Exportación**: Resultados en CSV + configuración en YAML

---

## Instalación y Requisitos

### Requisitos del Sistema

- Python 3.10+
- Mesa 2.3.4+
- pandas
- PyYAML
- 4+ GB RAM (depende del tamaño de simulaciones)
- CPU multi-core (recomendado 4+ cores)

### Instalación

```bash
# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias (si no están instaladas)
pip install mesa pandas pyyaml
```

### Verificar Instalación

```bash
python -c "import mesa; print(f'Mesa version: {mesa.__version__}')"
# Output esperado: Mesa version: 2.3.4
```

---

## Estructura de Archivos

```
amb-dengue/
├── config/
│   ├── default_config.yaml           # Configuración base del modelo
│   └── experiments/                   # 📂 Configuraciones de experimentos
│       ├── example_batch.yaml         # Ejemplo básico
│       ├── sensitivity_analysis.yaml  # Análisis de sensibilidad
│       └── control_comparison.yaml    # Comparación de estrategias
├── scripts/
│   └── batch_run.py                   # 🚀 Script principal de batch runner
├── results/                           # 📊 Resultados de experimentos
│   └── [experiment_name]/
│       ├── batch_results_TIMESTAMP.csv   # Datos de simulaciones
│       └── experiment_config_TIMESTAMP.yaml  # Config usada
└── docs/
    └── BATCH_EXPERIMENTS.md           # 📖 Esta guía
```

---

## Configuración de Experimentos

### Estructura del Archivo YAML

Los experimentos se definen en archivos YAML con la siguiente estructura:

```yaml
experiment:
  name: "nombre_experimento"
  description: "Descripción breve del objetivo"
  
  # Número de réplicas por combinación de parámetros
  iterations: 3
  
  # Duración de cada simulación en pasos (días)
  max_steps: 365
  
  # Parámetros que NO varían entre simulaciones
  fixed_params:
    width: 150
    height: 150
    fecha_inicio: "2022-01-01"
    climate_data_path: "data/raw/datos_climaticos_2022.csv"
    config_file: "config/default_config.yaml"
  
  # Parámetros que varían (barrido paramétrico)
  variable_params:
    num_humanos: [1000, 2000, 3000]
    num_mosquitos: [500, 1000, 1500]
    infectados_iniciales: [5, 10, 20]
    usar_lsm: [false, true]

# Configuración de paralelización
parallel:
  processes: 4  # Número de procesos paralelos (recomendado: CPU cores - 1)

# Configuración de salida
output:
  directory: "results/batch_experiments"
  prefix: "dengue_batch"
```

### Parámetros Importantes

#### `iterations` (réplicas)
Número de veces que se repite cada combinación de parámetros con diferentes seeds aleatorias.

- **Mínimo recomendado**: 3 (para estadísticas básicas)
- **Recomendado**: 10-30 (para análisis robusto)
- **Alto**: 50+ (para estudios de incertidumbre)

#### `max_steps` (duración)
Número de pasos (días) que dura cada simulación.

- **Pruebas rápidas**: 30-90 días
- **Análisis estándar**: 180-365 días
- **Estudios largos**: 730+ días (2 años)

#### `fixed_params`
Parámetros constantes en todas las simulaciones:

- `width`, `height`: Dimensiones del grid espacial
- `fecha_inicio`: Fecha de inicio (debe estar en rango del CSV climático)
- `climate_data_path`: Ruta al archivo CSV con datos climáticos
- `config_file`: Ruta al archivo YAML de configuración base

**⚠️ IMPORTANTE**: `fecha_inicio` debe estar en formato `"YYYY-MM-DD"` y dentro del rango de datos disponibles en el CSV climático.

#### `variable_params`
Parámetros que varían para crear barridos:

**Ejemplo: Población**
```yaml
variable_params:
  num_humanos: [500, 1000, 2000, 5000]
  num_mosquitos: [200, 500, 1000, 2000]
```

**Ejemplo: Transmisión**
```yaml
variable_params:
  # Estas requieren modificar config_file o pasarlas directamente
  transmission_mosquito_to_human: [0.4, 0.6, 0.8]
  transmission_human_to_mosquito: [0.2, 0.275, 0.35]
```

**Ejemplo: Estrategias de Control**
```yaml
variable_params:
  usar_lsm: [false, true]
  usar_itn_irs: [false, true]
  # Esto genera 4 combinaciones: (F,F), (F,T), (T,F), (T,T)
```

### Cálculo de Combinaciones

**Total de simulaciones = Combinaciones × Iterations**

Ejemplo:
```yaml
iterations: 3
variable_params:
  num_humanos: [1000, 3000]        # 2 valores
  num_mosquitos: [500, 1500]       # 2 valores
  infectados_iniciales: [5, 10]    # 2 valores
  usar_lsm: [false, true]          # 2 valores
```

**Combinaciones** = 2 × 2 × 2 × 2 = **16**  
**Total simulaciones** = 16 × 3 = **48**

⏱️ **Tiempo estimado**: Si cada simulación toma 30 segundos y usas 4 procesos paralelos:
- Tiempo = (48 simulaciones / 4 procesos) × 30 seg = **6 minutos**

---

## Ejecución

### Comando Básico

```bash
python scripts/batch_run.py \
  --experiment config/experiments/example_batch.yaml \
  --out results/my_experiment \
  --processes 4
```

### Parámetros de Línea de Comandos

| Parámetro | Descripción | Valor por Defecto |
|-----------|-------------|-------------------|
| `--experiment` | Ruta al archivo YAML de experimento | **(requerido)** |
| `--out` | Directorio de salida para resultados | `results` |
| `--processes` | Número de procesos paralelos | CPU cores - 1 |

### Ejemplos de Ejecución

#### 1. Experimento de Prueba Rápida (2 procesos)
```bash
python scripts/batch_run.py \
  --experiment config/experiments/example_batch.yaml \
  --out results/test_batch \
  --processes 2
```

#### 2. Experimento Completo (máxima paralelización)
```bash
python scripts/batch_run.py \
  --experiment config/experiments/sensitivity_analysis.yaml \
  --out results/sensitivity_2025 \
  --processes $(nproc --ignore=1)  # Usa todos los cores menos 1
```

#### 3. Experimento en Servidor (background)
```bash
nohup python scripts/batch_run.py \
  --experiment config/experiments/large_study.yaml \
  --out results/large_study \
  --processes 8 > batch_run.log 2>&1 &
```

### Salida del Script

Durante la ejecución verás:

```
🚀 Running batch_run with Mesa 2.3.4
   Iterations: 3
   Max steps: 90
   Processes: 4
   Fixed params: ['width', 'height', 'fecha_inicio', 'climate_data_path', 'config_file']
   Variable params: ['num_humanos', 'num_mosquitos', 'infectados_iniciales', 'usar_lsm']
   Total runs: 48

⏳ Ejecutando simulaciones en paralelo...
✓ Datos climáticos cargados desde: data/raw/datos_climaticos_2022.csv
  Rango de fechas: 2022-01-01 a 2022-12-31

100%|████████████████████████████████████████| 48/48 [03:24<00:00,  4.27s/it]

✅ Batch run completado!
   Resultados guardados en: results/my_experiment/batch_results_20250110_112345.csv
   Configuración guardada en: results/my_experiment/experiment_config_20250110_112345.yaml
   Total simulaciones: 48
   Tiempo total: 3m 24s
```

---

## Análisis de Resultados

### Estructura del CSV de Resultados

El archivo `batch_results_TIMESTAMP.csv` contiene una fila por cada paso de cada simulación:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `RunId` | int | ID único de la corrida (0 a N-1) |
| `iteration` | int | Número de réplica (0 a iterations-1) |
| `Step` | int | Paso de tiempo (día) de la simulación |
| `num_humanos` | int | Valor del parámetro (varía entre corridas) |
| `num_mosquitos` | int | Valor del parámetro (varía entre corridas) |
| `infectados_iniciales` | int | Valor del parámetro (varía entre corridas) |
| `usar_lsm` | bool | Valor del parámetro (varía entre corridas) |
| `Susceptibles` | int | Humanos susceptibles en este paso |
| `Expuestos` | int | Humanos expuestos en este paso |
| `Infectados` | int | Humanos infectados en este paso |
| `Recuperados` | int | Humanos recuperados en este paso |
| `Mosquitos_S` | int | Mosquitos susceptibles |
| `Mosquitos_I` | int | Mosquitos infectados |
| `Mosquitos_Total` | int | Total mosquitos adultos |
| `Huevos` | int | Total huevos |
| `Temperatura` | float | Temperatura actual (°C) |
| `Precipitacion` | float | Precipitación actual (mm) |

### Ejemplo de Análisis con Pandas

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar resultados
df = pd.read_csv('results/my_experiment/batch_results_20250110_112345.csv')

# 1. Calcular estadísticas por paso (promediando réplicas)
df_avg = df.groupby(['Step', 'num_humanos', 'num_mosquitos', 'usar_lsm']).agg({
    'Infectados': ['mean', 'std', 'min', 'max'],
    'Mosquitos_I': ['mean', 'std']
}).reset_index()

# 2. Comparar estrategias de control
df_final = df[df['Step'] == df['Step'].max()]  # Último paso
control_comparison = df_final.groupby('usar_lsm').agg({
    'Infectados': 'mean',
    'Recuperados': 'mean'
})
print(control_comparison)

# 3. Visualizar series temporales
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Infectados humanos por tamaño de población
for num_h in df['num_humanos'].unique():
    data = df[df['num_humanos'] == num_h].groupby('Step')['Infectados'].mean()
    axes[0, 0].plot(data, label=f'Humanos={num_h}')
axes[0, 0].set_title('Infectados por Tamaño de Población')
axes[0, 0].legend()

# Efecto de LSM
for lsm in [False, True]:
    data = df[df['usar_lsm'] == lsm].groupby('Step')['Infectados'].mean()
    axes[0, 1].plot(data, label=f'LSM={lsm}')
axes[0, 1].set_title('Efecto de Control Larvario (LSM)')
axes[0, 1].legend()

# Mosquitos infectados
sns.boxplot(data=df_final, x='num_mosquitos', y='Mosquitos_I', ax=axes[1, 0])
axes[1, 0].set_title('Mosquitos Infectados (Final)')

# Correlación temperatura-infectados
axes[1, 1].scatter(df['Temperatura'], df['Infectados'], alpha=0.1)
axes[1, 1].set_xlabel('Temperatura (°C)')
axes[1, 1].set_ylabel('Infectados')
axes[1, 1].set_title('Temperatura vs Infectados')

plt.tight_layout()
plt.savefig('results/my_experiment/analysis.png', dpi=300)
plt.show()

# 4. Análisis de sensibilidad (Pico de infectados)
df_peak = df.groupby(['RunId', 'num_humanos', 'num_mosquitos', 'usar_lsm'])['Infectados'].max().reset_index()
print("\nPico promedio de infectados por configuración:")
print(df_peak.groupby(['usar_lsm', 'num_humanos'])['Infectados'].mean())
```

### Métricas Clave a Analizar

1. **Pico de infección**: `max(Infectados)` por corrida
2. **Tiempo al pico**: `argmax(Infectados)` 
3. **Ataque total**: `max(Recuperados)` (casos acumulados)
4. **Duración del brote**: Días con `Infectados > 0`
5. **Efectividad de control**: Reducción % en pico al activar LSM/ITN

---

## Ejemplos de Escenarios

### 1. Análisis de Sensibilidad de Población

**Objetivo**: ¿Cómo afecta el tamaño de la población al brote?

```yaml
experiment:
  name: "sensitivity_population"
  description: "Análisis de sensibilidad a tamaño de población"
  iterations: 10
  max_steps: 180
  
  fixed_params:
    width: 150
    height: 150
    fecha_inicio: "2022-01-01"
    climate_data_path: "data/raw/datos_climaticos_2022.csv"
    config_file: "config/default_config.yaml"
    infectados_iniciales: 10
  
  variable_params:
    num_humanos: [500, 1000, 2000, 5000]
    num_mosquitos: [250, 500, 1000, 2500]  # Mantener ratio 2:1

parallel:
  processes: 4
```

**Total**: 4 × 4 × 10 = **160 simulaciones**

### 2. Comparación de Estrategias de Control

**Objetivo**: ¿Cuál estrategia reduce más las infecciones?

```yaml
experiment:
  name: "control_strategies"
  description: "Comparación LSM vs ITN/IRS vs Ambas"
  iterations: 20
  max_steps: 365
  
  fixed_params:
    width: 150
    height: 150
    fecha_inicio: "2022-01-01"
    climate_data_path: "data/raw/datos_climaticos_2022.csv"
    config_file: "config/default_config.yaml"
    num_humanos: 3000
    num_mosquitos: 1500
    infectados_iniciales: 10
  
  variable_params:
    usar_lsm: [false, true]
    usar_itn_irs: [false, true]
    # Genera 4 escenarios:
    # 1. Sin control (F, F)
    # 2. Solo LSM (T, F)
    # 3. Solo ITN/IRS (F, T)
    # 4. Ambos (T, T)

parallel:
  processes: 4
```

**Total**: 4 × 20 = **80 simulaciones**

### 3. Efecto del Clima (Estacional)

**Objetivo**: ¿Cuándo es más probable un brote según la época del año?

```yaml
experiment:
  name: "seasonal_effect"
  description: "Efecto de la época del año en transmisión"
  iterations: 15
  max_steps: 180  # 6 meses
  
  fixed_params:
    width: 150
    height: 150
    climate_data_path: "data/raw/datos_climaticos_2022.csv"
    config_file: "config/default_config.yaml"
    num_humanos: 2000
    num_mosquitos: 1000
    infectados_iniciales: 5
  
  variable_params:
    # Iniciar en diferentes épocas
    fecha_inicio: 
      - "2022-01-01"  # Verano
      - "2022-04-01"  # Otoño
      - "2022-07-01"  # Invierno
      - "2022-10-01"  # Primavera

parallel:
  processes: 4
```

**Total**: 4 × 15 = **60 simulaciones**

### 4. Calibración con Datos Reales

**Objetivo**: Ajustar parámetros de transmisión a casos observados

```yaml
experiment:
  name: "calibration_transmission"
  description: "Calibración de tasas de transmisión"
  iterations: 30
  max_steps: 365
  
  fixed_params:
    width: 150
    height: 150
    fecha_inicio: "2022-01-01"
    climate_data_path: "data/raw/datos_climaticos_2022.csv"
    num_humanos: 3000
    num_mosquitos: 1500
    infectados_iniciales: 10
    # Necesita config files personalizados con diferentes tasas
  
  variable_params:
    config_file:
      - "config/calibration/transmission_low.yaml"    # α=0.4, β=0.2
      - "config/calibration/transmission_med.yaml"    # α=0.6, β=0.275
      - "config/calibration/transmission_high.yaml"   # α=0.8, β=0.35

parallel:
  processes: 4
```

**Total**: 3 × 30 = **90 simulaciones**

---

## Optimización de Performance

### Recomendaciones para Acelerar Simulaciones

#### 1. Ajustar Número de Procesos

```bash
# Ver número de cores disponibles
nproc

# Usar todos menos 1 (dejar 1 para el sistema)
python scripts/batch_run.py ... --processes $(($(nproc)-1))
```

**⚠️ No usar más procesos que cores físicos**: Puede ralentizar por context switching.

#### 2. Reducir Tamaño del Grid

Simulaciones con grids grandes son más lentas:

```yaml
# Lento (22,500 celdas)
fixed_params:
  width: 150
  height: 150

# Más rápido (10,000 celdas, ~2x más rápido)
fixed_params:
  width: 100
  height: 100

# Muy rápido (2,500 celdas, ~5x más rápido)
fixed_params:
  width: 50
  height: 50
```

#### 3. Reducir Población

```yaml
# Lento (5,000 agentes)
num_humanos: 5000
num_mosquitos: 2500

# Más rápido (2,000 agentes, ~2x más rápido)
num_humanos: 2000
num_mosquitos: 1000

# Para pruebas (400 agentes, ~10x más rápido)
num_humanos: 400
num_mosquitos: 200
```

#### 4. Reducir `max_steps` para Pruebas

```yaml
# Producción (1 año)
max_steps: 365

# Desarrollo (3 meses, ~4x más rápido)
max_steps: 90

# Tests rápidos (1 mes, ~12x más rápido)
max_steps: 30
```

#### 5. Reducir `iterations` Inicialmente

```yaml
# Producción (estadísticas robustas)
iterations: 30

# Análisis exploratório
iterations: 10

# Pruebas de código (solo verificar que corre)
iterations: 2
```

### Benchmarks Aproximados

Tiempos estimados por simulación (1 core, max_steps=365):

| Config | Grid | Humanos | Mosquitos | Tiempo/sim |
|--------|------|---------|-----------|------------|
| Pequeña | 50×50 | 500 | 250 | ~10 seg |
| Mediana | 100×100 | 2000 | 1000 | ~45 seg |
| Grande | 150×150 | 5000 | 2500 | ~2 min |
| Muy Grande | 200×200 | 10000 | 5000 | ~5 min |

**Con 4 procesos paralelos y 10 iterations**:
- Pequeña: 10×10/4 = **25 segundos**
- Mediana: 45×10/4 = **1.9 minutos**
- Grande: 120×10/4 = **5 minutos**

### Estrategia de Desarrollo Iterativo

1. **Fase 1 - Pruebas de Código** (minutos)
   ```yaml
   iterations: 2
   max_steps: 30
   grid: 50×50
   población: 500 humanos, 250 mosquitos
   ```

2. **Fase 2 - Exploración** (1-2 horas)
   ```yaml
   iterations: 5
   max_steps: 90
   grid: 100×100
   población: 2000 humanos, 1000 mosquitos
   ```

3. **Fase 3 - Análisis Final** (4-8 horas, ejecutar overnight)
   ```yaml
   iterations: 30
   max_steps: 365
   grid: 150×150
   población: 5000 humanos, 2500 mosquitos
   ```

---

## Solución de Problemas Comunes

### Error: "La fecha de inicio no está en el rango de datos disponibles"

**Causa**: `fecha_inicio` está fuera del rango del CSV climático.

**Solución**: Verificar el rango de fechas en el CSV:

```python
import pandas as pd
df = pd.read_csv('data/raw/datos_climaticos_2022.csv')
print(f"Rango: {df['date'].min()} a {df['date'].max()}")
```

Luego ajustar `fecha_inicio` en el YAML.

### Error: "ModuleNotFoundError: No module named 'pandas'"

**Causa**: Dependencias no instaladas o entorno virtual no activado.

**Solución**:
```bash
source .venv/bin/activate
pip install pandas pyyaml
```

### Simulaciones Muy Lentas

**Causa**: Grid o población muy grandes, o muchas iterations.

**Solución**: Ver sección [Optimización de Performance](#optimización-de-performance).

### Memoria Insuficiente

**Síntoma**: Proceso termina abruptamente sin mensaje de error.

**Causa**: Demasiadas simulaciones simultáneas o simulaciones muy grandes.

**Solución**:
1. Reducir `--processes`
2. Reducir tamaño de grid/población
3. Ejecutar en lotes más pequeños

### Resultados Inconsistentes entre Réplicas

**Causa**: Variabilidad estocástica normal del modelo.

**Solución**: Aumentar `iterations` (recomendado: ≥10) y analizar promedios/medianas en lugar de valores individuales.

---

## Referencias y Recursos

- **Mesa Documentation**: https://mesa.readthedocs.io/
- **batch_run API**: https://mesa.readthedocs.io/en/latest/apis/batchrunner.html
- **Pandas Tutorial**: https://pandas.pydata.org/docs/user_guide/index.html
- **Modelo ABM-Dengue**: `docs/PARAMETROS_MODELO.md`
- **Configuración de Parámetros**: `docs/CONFIGURACION_PARAMETROS.md`

---

## Resumen de Comandos Útiles

```bash
# Ejecutar experimento básico
python scripts/batch_run.py \
  --experiment config/experiments/example_batch.yaml \
  --out results/test

# Usar todos los cores menos 1
python scripts/batch_run.py \
  --experiment config/experiments/my_experiment.yaml \
  --processes $(($(nproc)-1))

# Ejecutar en background
nohup python scripts/batch_run.py \
  --experiment config/experiments/large_study.yaml \
  --out results/large_study > batch.log 2>&1 &

# Ver progreso del batch en background
tail -f batch.log

# Ver procesos de Python corriendo
ps aux | grep python

# Matar batch runner si es necesario
pkill -f batch_run.py
```

---

## Próximos Pasos

1. ✅ **Ejecutar ejemplo básico**: `example_batch.yaml` (5 minutos)
2. 📊 **Analizar resultados**: Cargar CSV en pandas/Excel
3. 🔬 **Diseñar experimento propio**: Copiar y modificar YAML
4. 🚀 **Ejecutar estudio completo**: Experimento overnight con 30+ iterations
5. 📈 **Publicar resultados**: Generar figuras y tablas

---

**Última actualización**: Noviembre 2025  
**Autor**: Equipo ABM-Dengue  
**Versión**: 1.0 (Mesa 2.3.4)
