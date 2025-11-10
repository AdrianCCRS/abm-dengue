# Guía de Configuración de Parámetros

Este documento explica cómo modificar los parámetros ajustables del modelo ABM del Dengue.

## 📋 Archivo de Configuración Principal

Todos los parámetros ajustables se encuentran en:
```
config/simulation_config.yaml
```

Este archivo YAML contiene todas las variables que puedes modificar sin necesidad de editar el código Python.

## 🎯 Categorías de Parámetros

### 1. Parámetros del Modelo (model)
```yaml
model:
  grid_width: 50              # Ancho del grid espacial (celdas)
  grid_height: 50             # Alto del grid espacial (celdas)
  simulation_days: 180        # Duración de la simulación (días)
  seed: 42                    # Semilla para reproducibilidad (null = aleatorio)
```

### 2. Población (population)
```yaml
population:
  num_humans: 1000                    # Número de agentes humanos
  num_mosquitoes_adult: 2000          # Mosquitos adultos iniciales
  num_mosquitoes_eggs: 500            # Huevos iniciales
  initial_infected_humans: 10         # Humanos infectados al inicio
  initial_infected_mosquitoes: 5      # Mosquitos infectados al inicio
  
  # Distribución de tipos de movilidad (deben sumar 1.0)
  mobility_distribution:
    student: 0.25        # Estudiantes - van a escuela
    worker: 0.35         # Trabajadores - van a oficina
    mobile: 0.25         # Móviles continuos - cambian ubicación frecuentemente
    stationary: 0.15     # Estacionarios - permanecen en casa
```

**💡 Tip:** Modifica `mobility_distribution` para simular diferentes composiciones demográficas (más estudiantes, más trabajadores remotos, etc.)

### 3. Enfermedad Humana - Modelo SEIR (human_disease)
```yaml
human_disease:
  incubation_period: 5.0       # Ne - días en estado Expuesto (E) antes de ser Infectado (I)
  infectious_period: 6.0       # Ni - días en estado Infectado (I) antes de Recuperarse (R)
  recovery_rate: 0.167         # 1/infectious_period
  mortality_rate: 0.001        # Tasa de mortalidad por dengue
  immunity_loss_rate: 0.0      # Prc = 0 (inmunidad permanente)
```

**🔬 Uso:** 
- Aumenta `incubation_period` para simular variantes con incubación más larga
- Aumenta `infectious_period` para modelar casos más graves

### 4. Enfermedad Mosquito - Modelo SI (mosquito_disease)
```yaml
mosquito_disease:
  incubation_period: 10.0      # (No usado en SI simple)
  mortality_rate: 0.05         # Mr = tasa de mortalidad diaria (5% diario)
  lifespan_mean: 20.0          # Vida promedio = 1/mortality_rate
  lifespan_std: 5.0            # Desviación estándar
  sensory_range: 3             # Sr = rango de detección de humanos (celdas)
```

**🦟 Explicación:**
- `mortality_rate: 0.05` significa que cada día, un mosquito tiene 5% de probabilidad de morir
- `sensory_range: 3` significa que un mosquito puede detectar humanos a 3 celdas de distancia

### 5. Transmisión (transmission)
```yaml
transmission:
  mosquito_to_human_prob: 0.6   # α = probabilidad de transmisión M→H por picadura
  human_to_mosquito_prob: 0.275 # β = probabilidad de transmisión H→M por picadura
  biting_rate: 1.0              # Picaduras por mosquito hembra por día
  contact_radius: 1             # Radio de contacto (0 = misma celda)
```

**⚠️ Parámetros Clave:**
- `mosquito_to_human_prob` (α): Probabilidad de que un mosquito infectado transmita dengue al picar un humano susceptible
- `human_to_mosquito_prob` (β): Probabilidad de que un mosquito susceptible se infecte al picar un humano infectado

**Ejemplo de calibración:**
- Para simular dengue más contagioso: aumenta α y β
- Para simular cepa menos virulenta: disminuye α y β

### 6. Movilidad Humana (mobility) ⭐ AJUSTABLES

```yaml
mobility:
  move_probability: 0.3         # Probabilidad general de moverse
  work_probability: 0.7         # Probabilidad de ir al trabajo
  
  # 🎯 PROBABILIDADES DE VISITA A PARQUE (fácilmente modificables)
  park_probability_student: 0.3      # Estudiantes (más activos socialmente)
  park_probability_worker: 0.1       # Trabajadores (menos tiempo libre)
  park_probability_mobile: 0.15      # Móviles continuos
  park_probability_stationary: 0.05  # Estacionarios (rara vez salen)
  
  # ⏰ HORARIOS DE ACTIVIDAD
  school_start_hour: 7          # Entrada a escuela
  school_end_hour: 15           # Salida de escuela (3 PM)
  work_start_hour: 7            # Entrada al trabajo
  work_end_hour: 17             # Salida del trabajo (5 PM)
  park_start_hour: 16           # Ventana de parque inicio (4 PM)
  park_end_hour: 19             # Ventana de parque fin (7 PM)
  
  # Movilidad continua (Tipo 3)
  mobile_move_interval_hours: 2      # Cada cuántas horas cambian ubicación
  mobile_active_start_hour: 7        # Inicio movilidad activa
  mobile_active_end_hour: 19         # Fin movilidad activa (7 PM)
  
  home_return_probability: 0.9  # Probabilidad de regresar a casa
```

**📊 Ejemplos de Escenarios:**

#### Escenario 1: Cuarentena/Confinamiento
```yaml
park_probability_student: 0.05      # Reducir salidas recreativas
park_probability_worker: 0.02
work_probability: 0.3               # Trabajo remoto
school_start_hour: 0                # Escuelas cerradas (desactivar)
school_end_hour: 0
```

#### Escenario 2: Vacaciones Escolares
```yaml
park_probability_student: 0.6       # Más tiempo en parques
school_start_hour: 0                # Sin clases
school_end_hour: 0
```

#### Escenario 3: Población Muy Móvil (turismo, eventos)
```yaml
mobile_move_interval_hours: 1       # Movimiento cada hora
park_probability_student: 0.5
park_probability_worker: 0.4
```

### 7. Clima (climate)
```yaml
climate:
  use_csv: true                    # Usar datos climáticos desde CSV
  csv_path: "data/raw/datos_climaticos_2022.csv"  # Ruta al archivo CSV
  location:
    latitude: 7.1193               # Bucaramanga
    longitude: -73.1227
  default_temperature: 24.0        # °C si falla API
  default_precipitation: 3.0       # mm si falla API
  temperature_effect_on_breeding: true
  rain_effect_on_breeding: true
```

**🌡️ Nota:** Si `use_api: false`, el modelo usa un generador sintético de clima.

### 8. Reproducción de Mosquitos (mosquito_breeding) ⭐ AJUSTABLES

```yaml
mosquito_breeding:
  eggs_per_female: 100          # Huevos por puesta
  mating_probability: 0.6       # Pm = probabilidad de apareamiento exitoso
  female_ratio: 0.5             # Pf = proporción de hembras (0.5 = 50%)
  
  # 🌡️ DESARROLLO DEPENDIENTE DE TEMPERATURA
  # Fórmula maduración: τ = base_days + |θ - temp_optimal| / sensitivity
  egg_maturation_base_days: 3
  egg_maturation_temp_optimal: 21.0
  egg_maturation_temp_sensitivity: 5.0
  
  # Fórmula desarrollo huevo-adulto: μ = base_days + |θ - temp_optimal| * sensitivity
  egg_to_adult_base_days: 8
  egg_to_adult_temp_optimal: 25.0
  egg_to_adult_temp_sensitivity: 1.0
  
  # Límites de temperatura
  temperature_min: 15.0         # °C mínima para desarrollo
  temperature_opt: 28.0         # °C óptima
  temperature_max: 35.0         # °C máxima
  
  # Precipitación
  rainfall_threshold: 0.0       # mm mínimos para activar criaderos
  breeding_site_ratio: 0.2      # 20% de celdas tienen sitios de cría
```

**📐 Entender las Fórmulas:**

**Maduración del huevo (días hasta que puede desarrollarse):**
```
τ = 3 + |temperatura - 21| / 5
```
- A 21°C (óptima): τ = 3 días
- A 26°C: τ = 3 + 5/5 = 4 días
- A 16°C: τ = 3 + 5/5 = 4 días

**Desarrollo huevo→adulto (días para eclosionar):**
```
μ = 8 + |temperatura - 25|
```
- A 25°C (óptima): μ = 8 días
- A 30°C: μ = 8 + 5 = 13 días
- A 20°C: μ = 8 + 5 = 13 días

**💡 Para simular cambio climático:**
```yaml
temperature_opt: 30.0           # Temperatura óptima más alta
egg_to_adult_base_days: 6       # Desarrollo más rápido
rainfall_threshold: 10.0        # Más lluvia necesaria para criaderos
```

### 9. Estrategias de Control (control_strategies)

#### LSM - Larval Source Management (Control Larvario)
```yaml
lsm:
  enabled: false               # Activar/desactivar
  start_day: 30                # Día de inicio de la intervención
  coverage: 0.7                # 70% de cobertura espacial
  effectiveness: 0.8           # 80% de reducción de larvas
  frequency_days: 7            # Aplicar cada 7 días
```

#### ITN/IRS - Mosquiteros e Insecticidas
```yaml
itn_irs:
  enabled: false               # Activar/desactivar
  start_day: 30                # Día de inicio
  coverage: 0.6                # 60% de hogares protegidos
  bite_reduction: 0.7          # 70% de reducción de picaduras
  duration_days: 90            # Duración del efecto
```

**🎯 Comparar Estrategias:**

**Solo LSM:**
```yaml
lsm:
  enabled: true
  coverage: 0.7
itn_irs:
  enabled: false
```

**Solo ITN/IRS:**
```yaml
lsm:
  enabled: false
itn_irs:
  enabled: true
  coverage: 0.6
```

**Combinadas:**
```yaml
lsm:
  enabled: true
  start_day: 30
itn_irs:
  enabled: true
  start_day: 60              # Aplicar más tarde
```

## 🚀 Cómo Usar la Configuración

### Opción 1: Usar archivo YAML directamente
```bash
python main.py --config config/simulation_config.yaml
```

### Opción 2: Crear configuraciones personalizadas
```bash
# Copiar configuración base
cp config/simulation_config.yaml config/escenario_cuarentena.yaml

# Editar escenario_cuarentena.yaml con tus parámetros

# Ejecutar
python main.py --config config/escenario_cuarentena.yaml
```

### Opción 3: Sobrescribir parámetros desde CLI
```bash
python main.py --steps 365 --humanos 2000 --lsm --itn-irs
```

## 📝 Ejemplos de Configuraciones Completas

### Ejemplo 1: Escenario Baseline (Sin Intervención)
```yaml
model:
  simulation_days: 365
  
population:
  num_humans: 1000
  initial_infected_humans: 10

control_strategies:
  lsm:
    enabled: false
  itn_irs:
    enabled: false
```

### Ejemplo 2: Intervención Agresiva
```yaml
model:
  simulation_days: 365

population:
  num_humans: 1000
  initial_infected_humans: 20        # Brote inicial más grande

transmission:
  mosquito_to_human_prob: 0.7        # Cepa más contagiosa

control_strategies:
  lsm:
    enabled: true
    start_day: 15                    # Respuesta rápida
    coverage: 0.9                    # Alta cobertura
    frequency_days: 3                # Cada 3 días
  itn_irs:
    enabled: true
    start_day: 15
    coverage: 0.8
```

### Ejemplo 3: Cambio de Comportamiento Social
```yaml
mobility:
  park_probability_student: 0.1     # Menos reuniones sociales
  park_probability_worker: 0.05
  work_probability: 0.5             # Más trabajo remoto
  
transmission:
  mosquito_to_human_prob: 0.6
  human_to_mosquito_prob: 0.275
```

## 🔧 Validación de Parámetros

El modelo valida automáticamente que:
- Las probabilidades estén entre 0 y 1
- Los días sean positivos
- Las distribuciones de movilidad sumen 1.0
- Las temperaturas estén en rangos realistas

## 📖 Referencias

- **Jindal & Rao (2017)**: Paper base con fórmulas y parámetros originales
- **docs/PARAMETROS_MODELO.md**: Lista completa de parámetros del modelo
- **README.md**: Información general del proyecto

## 💬 Soporte

Para dudas sobre qué parámetros modificar para tu experimento, consulta:
1. Este documento
2. `docs/PARAMETROS_MODELO.md` - Explicación científica de cada parámetro
3. `GUIA_DESARROLLO.md` - Fases de desarrollo y calibración
