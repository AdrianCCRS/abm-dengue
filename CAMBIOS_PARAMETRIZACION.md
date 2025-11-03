# Resumen de Cambios - Parametrización Configurable

## 🎯 Objetivo
Hacer que todos los parámetros ajustables del modelo sean fácilmente modificables desde el archivo de configuración YAML sin necesidad de editar código Python.

## ✅ Cambios Realizados

### 1. Archivo de Configuración Actualizado (`config/simulation_config.yaml`)

#### **Nuevos Parámetros Agregados:**

**Movilidad Humana (mobility):**
- `park_probability_student`: 0.3 - Probabilidad de estudiantes de visitar parques
- `park_probability_worker`: 0.1 - Probabilidad de trabajadores de visitar parques
- `park_probability_mobile`: 0.15 - Probabilidad de móviles continuos
- `park_probability_stationary`: 0.05 - Probabilidad de estacionarios
- Horarios configurables: `school_start_hour`, `school_end_hour`, `work_start_hour`, etc.
- `mobile_move_interval_hours`: 2 - Intervalo de movimiento para agentes móviles

**Enfermedad Humana (human_disease):**
- `incubation_period`: 5.0 - Período de incubación (E→I)
- `infectious_period`: 6.0 - Período infeccioso (I→R)
- `immunity_loss_rate`: 0.0 - Tasa de pérdida de inmunidad

**Enfermedad Mosquito (mosquito_disease):**
- `mortality_rate`: 0.05 - Tasa de mortalidad diaria
- `sensory_range`: 3 - Rango de detección de humanos

**Transmisión (transmission):**
- `mosquito_to_human_prob`: 0.6 - α (probabilidad M→H)
- `human_to_mosquito_prob`: 0.275 - β (probabilidad H→M)

**Reproducción de Mosquitos (mosquito_breeding):**
- `mating_probability`: 0.6 - Pm (probabilidad de apareamiento)
- `female_ratio`: 0.5 - Pf (proporción de hembras)
- Parámetros de desarrollo dependiente de temperatura:
  - `egg_maturation_base_days`: 3
  - `egg_maturation_temp_optimal`: 21.0
  - `egg_maturation_temp_sensitivity`: 5.0
  - `egg_to_adult_base_days`: 8
  - `egg_to_adult_temp_optimal`: 25.0
  - `egg_to_adult_temp_sensitivity`: 1.0
- `rainfall_threshold`: 0.0 - Umbral de precipitación para criaderos
- `breeding_site_ratio`: 0.2 - Proporción de celdas con sitios de cría

**Población (population):**
- `num_mosquitoes_adult`: 2000 - Mosquitos adultos iniciales
- `num_mosquitoes_eggs`: 500 - Huevos iniciales
- Distribución de movilidad:
  - `student`: 0.25
  - `worker`: 0.35
  - `mobile`: 0.25
  - `stationary`: 0.15

### 2. Agente Humano (`src/agents/human_agent.py`)

**Cambios:**
- ✅ Parámetros hardcodeados reemplazados por lectura desde el modelo
- ✅ `duracion_expuesto` y `duracion_infectado` ahora desde `model.incubacion_humano` y `model.infeccioso_humano`
- ✅ Probabilidades de parque específicas por tipo desde configuración
- ✅ Horarios de actividad (escuela, trabajo, parque) configurables
- ✅ Intervalo de movimiento para móviles continuos configurable

**Antes:**
```python
self.duracion_expuesto = 5  # Hardcoded
self.prob_parque = 0.3 if tipo_movilidad == TipoMovilidad.ESTUDIANTE else 0.1
```

**Después:**
```python
self.duracion_expuesto = getattr(model, 'incubacion_humano', 5)
park_probs = {
    TipoMovilidad.ESTUDIANTE: getattr(model, 'prob_parque_estudiante', 0.3),
    TipoMovilidad.TRABAJADOR: getattr(model, 'prob_parque_trabajador', 0.1),
    # ...
}
```

### 3. Agente Mosquito (`src/agents/mosquito_agent.py`)

**Cambios:**
- ✅ Constantes de clase eliminadas, reemplazadas por atributos de instancia
- ✅ Parámetros leídos desde el modelo en `__init__`
- ✅ Probabilidades de transmisión (α, β) desde configuración
- ✅ Desarrollo de huevos con fórmulas configurables
- ✅ Umbral de precipitación configurable para reproducción

**Antes:**
```python
TASA_MORTALIDAD = 0.05  # Constante de clase
PROB_APAREAMIENTO = 0.6
if self.random.random() < 0.6:  # α hardcoded
```

**Después:**
```python
self.tasa_mortalidad = getattr(model, 'mortalidad_mosquito', 0.05)
self.prob_apareamiento = getattr(model, 'prob_apareamiento_mosquito', 0.6)
alpha = getattr(self.model, 'prob_transmision_mosquito_humano', 0.6)
```

### 4. Modelo Principal (`src/model/dengue_model.py`)

**Nuevos Métodos:**
- ✅ `_cargar_configuracion(config: Dict)` - Carga todos los parámetros desde YAML
- ✅ `_cargar_configuracion_default()` - Valores por defecto si no hay config
- ✅ Constructor acepta parámetro `config: Optional[Dict]`

**Parámetros Expuestos como Atributos del Modelo:**
```python
# Enfermedad humana
self.incubacion_humano
self.infeccioso_humano

# Enfermedad mosquito
self.mortalidad_mosquito
self.rango_sensorial_mosquito

# Transmisión
self.prob_transmision_mosquito_humano  # α
self.prob_transmision_humano_mosquito  # β

# Movilidad
self.prob_parque_estudiante
self.prob_parque_trabajador
self.hora_inicio_escuela
self.hora_fin_escuela
# ... etc

# Reproducción
self.huevos_por_hembra
self.prob_apareamiento_mosquito
self.proporcion_hembras
self.dias_base_desarrollo_huevo
# ... etc

# Distribución de tipos
self.dist_estudiantes
self.dist_trabajadores
# ... etc
```

### 5. Documentación (`docs/CONFIGURACION_PARAMETROS.md`)

**Nuevo Documento Creado:**
- ✅ Guía completa de todos los parámetros configurables
- ✅ Explicación de cada parámetro con ejemplos
- ✅ Escenarios de ejemplo (cuarentena, vacaciones, cambio climático)
- ✅ Fórmulas matemáticas explicadas
- ✅ Ejemplos de cómo modificar el YAML
- ✅ Casos de uso prácticos

## 📊 Ejemplos de Uso

### Ejemplo 1: Modificar Comportamiento Social

**Editar `config/simulation_config.yaml`:**
```yaml
mobility:
  park_probability_student: 0.5  # Aumentar salidas a parques
  park_probability_worker: 0.3
  work_probability: 0.4           # Más trabajo remoto
```

### Ejemplo 2: Simular Cepa Más Contagiosa

```yaml
transmission:
  mosquito_to_human_prob: 0.8   # α aumentado
  human_to_mosquito_prob: 0.4   # β aumentado

human_disease:
  infectious_period: 8.0         # Período infeccioso más largo
```

### Ejemplo 3: Cambio Climático

```yaml
mosquito_breeding:
  temperature_opt: 30.0          # Temperatura óptima más alta
  egg_to_adult_base_days: 6      # Desarrollo más rápido
  eggs_per_female: 120           # Más huevos por hembra
```

### Ejemplo 4: Población Estacionaria (Confinamiento)

```yaml
population:
  mobility_distribution:
    student: 0.05                # Casi sin estudiantes activos
    worker: 0.10
    mobile: 0.05
    stationary: 0.80             # 80% permanece en casa

mobility:
  park_probability_student: 0.01
  park_probability_worker: 0.01
```

## 🔄 Compatibilidad hacia Atrás

- ✅ El código funciona sin configuración YAML (usa valores por defecto)
- ✅ Parámetros antiguos del constructor siguen funcionando
- ✅ `getattr()` con valores por defecto previene errores si falta configuración

## 🧪 Testing

Para probar los cambios:
```bash
# Con configuración personalizada
python main.py --config config/simulation_config.yaml --steps 30

# Con valores por defecto
python test_quick.py
```

## 📝 Archivos Modificados

1. ✅ `config/simulation_config.yaml` - Parámetros expandidos
2. ✅ `src/agents/human_agent.py` - Lectura de configuración
3. ✅ `src/agents/mosquito_agent.py` - Lectura de configuración
4. ✅ `src/model/dengue_model.py` - Métodos de carga de config
5. ✅ `docs/CONFIGURACION_PARAMETROS.md` - Nueva documentación

## 🎓 Beneficios

1. **Facilidad de Experimentación**: Cambiar parámetros sin tocar código
2. **Reproducibilidad**: Archivos YAML versionables con Git
3. **Comparación de Escenarios**: Múltiples archivos de configuración
4. **Claridad**: Todos los parámetros en un solo lugar
5. **Documentación**: Guía completa de cada parámetro
6. **Calibración**: Fácil ajuste de parámetros durante calibración

## 🚀 Próximos Pasos Sugeridos

1. Crear configuraciones de escenarios predefinidos:
   - `config/baseline.yaml`
   - `config/cuarentena.yaml`
   - `config/cambio_climatico.yaml`
   - `config/intervencion_agresiva.yaml`

2. Validación automática de parámetros:
   - Rangos válidos (0-1 para probabilidades)
   - Distribuciones que sumen 1.0
   - Horarios coherentes

3. Interfaz de comparación de escenarios:
   - Script para ejecutar múltiples configuraciones
   - Comparación automática de resultados

## ✨ Conclusión

Todos los parámetros ajustables ahora son fácilmente modificables desde `config/simulation_config.yaml`. Los agentes leen estos valores del modelo, permitiendo experimentación rápida sin editar código Python.
