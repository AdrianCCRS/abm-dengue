# Modelo Basado en Agentes (ABM) para Transmisión del Dengue en Bucaramanga

**Autores:** Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez  
**Institución:** Universidad Industrial de Santander - Simulación Digital F1  
**Framework:** Mesa 2.3.4 (Python)

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#-resumen-ejecutivo)
2. [Conceptualización del Modelo](#-conceptualización-del-modelo)
3. [Arquitectura del Sistema](#-arquitectura-del-sistema)
4. [Agentes del Modelo](#-agentes-del-modelo)
5. [Entorno de Simulación](#-entorno-de-simulación)
6. [Dinámica Temporal](#-dinámica-temporal)
7. [Parámetros del Modelo](#-parámetros-del-modelo)
8. [Interacciones y Flujos de Transmisión](#-interacciones-y-flujos-de-transmisión)
9. [Implementación Técnica](#-implementación-técnica)
10. [Instalación y Uso](#-instalación-y-uso)
11. [Referencias](#-referencias)

---

## 🎯 Resumen Ejecutivo

Este modelo basado en agentes (Agent-Based Model, ABM) simula la dinámica de transmisión del dengue en el área urbana de Bucaramanga, Colombia, considerando:

- **Población humana heterogénea** con patrones de movilidad diferenciados (estudiantes, trabajadores, móviles, estacionarios)
- **Población vectorial** de *Aedes aegypti* con ciclo de vida completo (huevo → adulto)
- **Entorno urbano realista** basado en el POT 2014-2027 (33.28 km², 150×150 celdas de ~38.5m)
- **Clima dinámico** con precipitación que afecta la formación de criaderos temporales
- **Escala temporal diaria** (1 step = 1 día) para simulaciones anuales (365 días)

El modelo integra datos demográficos, entomológicos, epidemiológicos y urbanos del contexto local, permitiendo evaluar escenarios de transmisión y estrategias de control en un entorno computacionalmente eficiente.

---

## 🧠 Conceptualización del Modelo

### Paradigma de Modelado

El modelo se fundamenta en el paradigma de **simulación basada en agentes** (ABM), donde:

1. **Agentes autónomos**: Humanos y mosquitos son entidades independientes con estado interno y comportamiento
2. **Interacciones locales**: La transmisión ocurre por contacto espacial directo (picaduras)
3. **Emergencia**: Patrones epidémicos emergen de interacciones individuales, no se programan explícitamente
4. **Heterogeneidad**: Cada agente puede tener características únicas (ubicación, estado de salud, movilidad)

### Modelo Epidemiológico

#### Humanos: SEIR (Susceptible-Expuesto-Infectado-Recuperado)

```
S → E → I → R
    ↑
    α (mosquito infectado pica humano susceptible)
```

- **S (Susceptible)**: Puede infectarse al ser picado por mosquito infectado
- **E (Expuesto)**: Período de incubación de 5 días [8, 9, 10]
- **I (Infectado)**: Período infeccioso de 6 días, puede transmitir a mosquitos [8, 9, 10]
- **R (Recuperado)**: Inmunidad permanente (no re-susceptibilidad)

#### Mosquitos: SI (Susceptible-Infectado)

```
S → I (permanente)
    ↑
    β (mosquito pica humano infectado)
```

- **S (Susceptible)**: Puede infectarse al picar humano infectado
- **I (Infectado)**: Infección permanente, transmite virus de por vida
- **No recuperación**: Los mosquitos no se recuperan del virus

### Escala Espacial

**Grid 150 × 150 = 22,500 celdas**

- **Celda**: ~38.5 m × 38.5 m (~1,480 m² ≈ 0.15 ha)
- **Área total**: ~33.3 km² (suelo urbano de Bucaramanga según POT [1])
- **Resolución**: Escala de manzana/microzona urbana
- **Rango mosquito**: 5 celdas (~190 m diarios) [12]

**Justificación**: Bucaramanga tiene 33.28 km² de suelo urbano consolidado [1]. Con 150×150 celdas, cada una representa ~38.5m × 38.5m, permitiendo capturar interacciones vector-huésped a nivel de manzana sin sobredimensionar el territorio computacionalmente.

### Escala Temporal

⚠️ **CRÍTICO: 1 step = 1 día (NO horas)**

El modelo opera en **escala diaria**:
- **1 paso de simulación = 1 día completo**
- **365 pasos = 1 año**
- **Movilidad humana**: Probabilidades diarias de ubicación (NO horarios)
- **Desarrollo mosquitos**: Grados-día acumulados diariamente

**Justificación biológica**:
- Período de incubación humano: 5 **días** [8, 9, 10]
- Período infeccioso humano: 6 **días** [8, 9, 10]
- Ciclo gonotrófico mosquito: 3 **días** [3]
- Desarrollo inmaduro: ~10-14 **días** a 26°C [14, 15]

Modelar en horas sobrecomplicaría sin aportar precisión epidemiológica relevante.

### Factor de Escala Poblacional

**1 agente humano = 200 personas reales**

- **Población simulada**: 3,000 agentes
- **Población real representada**: ~600,000 habitantes
- **Población urbana Bucaramanga**: 608,947 habitantes (ASIS 2022 [2])
- **Error**: < 1.5%

**Beneficios**:
- Mantiene densidad urbana realista (~18,000 hab/km²)
- Computacionalmente manejable
- Preserva proporciones epidemiológicas

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Clases UML

```
┌─────────────────────────────────────────────────────────────────┐
│                        DengueModel                               │
├─────────────────────────────────────────────────────────────────┤
│ - grid: MultiGrid                                                │
│ - agents: AgentSet                                               │
│ - schedule: SimultaneousActivation                               │
│ - datacollector: DataCollector                                   │
│ - climate_loader: ClimateDataLoader                              │
│ - sitios_cria: List[Tuple[int,int]]                             │
│ - sitios_cria_temporales: Dict[Tuple[int,int], int]             │
│ - temperatura_actual: float                                      │
│ - precipitacion_actual: float                                    │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(width, height, num_humanos, ...)                     │
│ + step()                                                         │
│ + _inicializar_grid()                                            │
│ + _inicializar_humanos()                                         │
│ + _inicializar_mosquitos()                                       │
│ + _actualizar_clima()                                            │
│ + _actualizar_sitios_cria_temporales()                          │
│ + _aplicar_control() [DESHABILITADO]                            │
└─────────────────────────────────────────────────────────────────┘
          │                              │
          │ contiene                     │ contiene
          ▼                              ▼
┌──────────────────────┐     ┌──────────────────────┐
│    HumanAgent        │     │   MosquitoAgent      │
├──────────────────────┤     ├──────────────────────┤
│ - estado: EstadoSalud│     │ - estado: EstadoMosq │
│ - tipo: TipoMovilidad│     │ - etapa: EtapaVida   │
│ - pos_hogar: Tuple   │     │ - sitio_cria: Tuple  │
│ - pos_destino: Tuple │     │ - edad: int          │
│ - dias_en_estado: int│     │ - grados_acum: float │
│ - en_aislamiento:bool│     │ - ha_picado_hoy:bool │
├──────────────────────┤     ├──────────────────────┤
│ + step()             │     │ + step()             │
│ + get_exposed()      │     │ + eclosionar()       │
│ + ejecutar_mov_diaria│     │ + mover()            │
│ + mover_a(pos)       │     │ + intentar_picar()   │
│ + es_susceptible()   │     │ + intentar_reprodu() │
│ + es_infeccioso()    │     │ + buscar_humano_cerc │
└──────────────────────┘     └──────────────────────┘
          │                              │
          │ usa                          │ usa
          ▼                              ▼
┌──────────────────────────────────────────────────┐
│                  Celda                            │
├──────────────────────────────────────────────────┤
│ - tipo: TipoCelda (URBANA, PARQUE, AGUA)        │
│ - es_sitio_cria: bool                            │
├──────────────────────────────────────────────────┤
│ + __init__(x, y, tipo)                           │
│ + __repr__()                                      │
└──────────────────────────────────────────────────┘
```

### Diagrama de Secuencia: Paso de Simulación Diario

```
┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
│Modelo│    │Clima │    │Humano│    │Mosqui│    │Grid  │
└──┬───┘    └──┬───┘    └──┬───┘    └──┬───┘    └──┬───┘
   │           │           │           │           │
   │ step()    │           │           │           │
   ├──────────>│           │           │           │
   │actualizar_│           │           │           │
   │  clima()  │           │           │           │
   │<──────────┤           │           │           │
   │(temp,prcp)│           │           │           │
   │           │           │           │           │
   │_actualizar_sitios_temp()          │           │
   ├───────────────────────────────────────────────>│
   │           │           │           │ crear/    │
   │           │           │           │ remover   │
   │           │           │           │ charcos   │
   │<───────────────────────────────────────────────┤
   │           │           │           │           │
   │agents.shuffle().do("step")        │           │
   ├──────────────────────>│           │           │
   │           │  step()   │           │           │
   │           │           │actualizar_│           │
   │           │           │  SEIR()   │           │
   │           │           │           │           │
   │           │           │ejecutar_  │           │
   │           │           │ movilidad │           │
   │           ├───────────┼───────────┼──────────>│
   │           │           │  mover()  │  move_   │
   │           │<───────────────────────  agent()  │
   │           │           │           │           │
   ├───────────────────────────────────>│           │
   │           │           │  step()   │           │
   │           │           │           │procesar_  │
   │           │           │           │ huevo() / │
   │           │           │           │ adulto()  │
   │           │           │           │           │
   │           │           │           │mover()    │
   │           │           │<──────────┤buscar_    │
   │           │           │           │ humano()  │
   │           │           │           │           │
   │           │           │<──────────┤intentar_  │
   │           │           │ picar()   │ picar()   │
   │           │           │  ┌─────┐  │           │
   │           │           │  │α o β│  │  (transmisión)
   │           │           │  └─────┘  │           │
   │           │           │           │           │
   │datacollector.collect()│           │           │
   ├──────────>│           │           │           │
   │<──────────┤(métricas) │           │           │
   │           │           │           │           │
```

---

## 👥 Agentes del Modelo

### 1. Agente Humano (`HumanAgent`)

#### Estados Epidemiológicos (SEIR)

```python
class EstadoSalud(Enum):
    SUSCEPTIBLE = "S"  # Puede infectarse
    EXPUESTO = "E"     # Incubando (5 días)
    INFECTADO = "I"    # Infeccioso (6 días)
    RECUPERADO = "R"   # Inmune permanente
```

#### Tipos de Movilidad

```python
class TipoMovilidad(Enum):
    ESTUDIANTE = 1      # Hogar ⇄ Escuela (+parque)
    TRABAJADOR = 2      # Hogar ⇄ Oficina (+parque)
    MOVIL_CONTINUO = 3  # Movimiento constante
    ESTACIONARIO = 4    # Permanece en hogar
```

#### Distribución Poblacional (Implementación Real)

**NOTA**: Existe una discrepancia entre `sources.txt` y la implementación real. **Se prioriza lo implementado**:

| Tipo | sources.txt | Implementación | Justificación |
|------|-------------|----------------|---------------|
| Estudiante | 25% | **30%** | Mayor representación demográfica <25 años (33.8%) [2] |
| Trabajador | 40% | **40%** | Concordante con tasa de participación laboral (61%) [13] |
| Móvil | 20% | **20%** | Representa informalidad (~47%) [13] |
| Estacionario | 15% | **10%** | Ajustado para mantener suma = 100% |

**Configuración real** (`default_config.yaml`):
```yaml
mobility_distribution:
  student: 0.30      # 30%
  worker: 0.40       # 40%
  mobile: 0.20       # 20%
  stationary: 0.10   # 10%
```

#### Comportamiento de Movilidad (Probabilidades Diarias)

⚠️ **CAMBIO CRÍTICO: Modelo horario → Modelo de probabilidades diarias**

**Anterior** (incorrecto): Asumía pasos horarios (6-14h escuela, 7-18h trabajo)  
**Actual** (correcto): Probabilidades diarias de ubicación

**Estudiantes**:
```yaml
home: 0.55       # 55% del día en casa
destination: 0.35 # 35% en escuela
park: 0.10       # 10% en parque
```

**Trabajadores**:
```yaml
home: 0.60       # 60% del día en casa
destination: 0.35 # 35% en oficina
park: 0.05       # 5% en parque
```

**Móviles** (vendedores, mensajeros):
```yaml
home: 0.40       # 40% en casa
destination: 0.0  # Sin destino fijo
park: 0.20       # 20% en parque
random: 0.40     # 40% ubicación aleatoria
```

**Estacionarios** (adultos mayores, hogar):
```yaml
home: 0.95       # 95% en casa
destination: 0.0
park: 0.05       # 5% salidas ocasionales
random: 0.0
```

**Validación**: El modelo valida automáticamente que cada distribución sume 1.0 ± 0.01

#### Comportamiento Especial: Agentes Infectados

Los agentes en estado **INFECTADO** tienen comportamiento modificado:

1. **Decisión de aislamiento** (única vez al infectarse):
   - Probabilidad: 70% (`isolation_probability = 0.7`)
   
2. **Con aislamiento**:
   - Permanecen en `pos_hogar` (100% del tiempo)
   
3. **Sin aislamiento**:
   - **Fase 1**: Si están lejos de casa (distancia > `infected_mobility_radius = 1`):
     - Se mueven **directamente** a `pos_hogar` (retorno inmediato)
   - **Fase 2**: Una vez en casa o cerca:
     - Movilidad local reducida (radio = 1 celda desde posición actual)
   
**Justificación**: Simula comportamiento realista donde personas infectadas:
- Reducen actividades fuera del hogar
- Regresan a casa para descansar
- Mantienen movilidad mínima local (vecindario inmediato)

#### Atributos Clave

```python
self.estado: EstadoSalud           # S, E, I, R
self.dias_en_estado: int           # Contador de progresión SEIR
self.tipo: TipoMovilidad           # Tipo de movilidad
self.pos_hogar: Tuple[int, int]    # Coordenadas del hogar
self.pos_destino: Tuple[int, int]  # Escuela/oficina (si aplica)
self.en_aislamiento: bool          # Flag de aislamiento
self.num_picaduras: int            # Métrica de exposición
```

---

### 2. Agente Mosquito (`MosquitoAgent`)

#### Estados Epidemiológicos (SI)

```python
class EstadoMosquito(Enum):
    SUSCEPTIBLE = "S"  # Puede infectarse
    INFECTADO = "I"    # Infeccioso (permanente)
```

#### Etapas del Ciclo de Vida

```python
class EtapaVida(Enum):
    HUEVO = "egg"      # En sitio de cría (pos=None)
    ADULTO = "adult"   # Volando (pos en grid)
```

**OPTIMIZACIÓN**: Solo se modelan **hembras**
- Los machos no pican ni transmiten
- Su única función (apareamiento) se modela con `mating_probability = 0.6`
- Reduce población de agentes en ~50% sin pérdida de información epidemiológica

#### Desarrollo Inmaduro (Huevo → Adulto)

**Modelo de Grados-Día Acumulados (GDD)** [14, 15, 16, 17]

```
GD_día = max(T_día - T_base, 0)

Donde:
- T_día = (T_max + T_min) / 2  (temperatura media diaria)
- T_base = 8.3°C  (umbral térmico mínimo) [15]
- K = 181.2°C·día (constante térmica total) [15]

Eclosión cuando: Σ GD_día ≥ K
```

**Justificación**: Basado en experimentos de Tun-Lin et al. (2000) para *Aedes aegypti* en Australia tropical [15]. A 26°C (temperatura media Bucaramanga), el desarrollo toma ~10-12 días.

#### Ciclo Reproductivo

**Ciclo Gonotrófico** [3]:
```
Apareamiento → Alimentación Sanguínea → Maduración Huevos → Oviposición
      ↓              ↓                        ↓                   ↓
  (probabilística) (picar humano)        (3 días)         (100 huevos)
```

**Parámetros**:
- `gonotrophic_cycle_days = 3` días mínimos entre puestas [3]
- `eggs_per_female = 100` huevos por oviposición [3]
- `female_ratio = 0.52` (levemente sesgado hacia hembras)

**Requisitos para reproducir**:
1. ✅ Estar apareada (`mating_probability = 0.6`)
2. ✅ Haber picado humano (ingesta de sangre)
3. ✅ Encontrar sitio de cría (agua o charco temporal)
4. ✅ Esperar cooldown gonotrófico (3 días)

#### Comportamiento de Búsqueda

**Sensado de humanos**:
- Rango sensorial: 3 celdas (~115 m) [12]
- Si detecta humano: moverse hacia él
- Si no: caminata aleatoria (Moore neighborhood, radio=5)

**Búsqueda de sitios de cría**:
- Busca dentro de `max_range = 5` celdas (~190 m) [12]
- Prefiere el más cercano
- Considera sitios permanentes (AGUA) y temporales (charcos)

#### Atributos Clave

```python
self.estado: EstadoMosquito        # S, I
self.etapa: EtapaVida              # HUEVO, ADULTO
self.grados_acumulados: float      # Para desarrollo GDD
self.dias_como_huevo: int          # Contador de edad
self.edad: int                     # Edad desde emergencia adulta
self.ha_picado_hoy: bool           # Flag de picadura diaria
self.esta_apareado: bool           # Flag de apareamiento
self.sitio_cria: Tuple[int,int]    # Ubicación de eclosión
self.dias_desde_ultima_puesta: int # Cooldown gonotrófico
```

---

## 🌍 Entorno de Simulación

### Grid Espacial

**Tipo**: `MultiGrid` (múltiples agentes por celda)
- Permite co-localización: humanos y mosquitos en misma celda → picadura

**Dimensiones**: 150 × 150 = 22,500 celdas

### Tipos de Celdas

```python
class TipoCelda(Enum):
    URBANA = "urbana"  # ~85% - Residencial/comercial
    PARQUE = "parque"  # ~10% - Áreas verdes [1]
    AGUA = "agua"      # ~5% - Quebradas, drenajes [1]
```

#### Distribución Real (Implementación)

```yaml
cell_types:
  water_ratio: 0.05   # 5% celdas de agua
  park_ratio: 0.10    # 10% celdas de parque
  # Restante: 85% urbana (implícito)
```

**Justificación**: Basado en POT Bucaramanga 2014-2027 [1]:
- ~10% áreas verdes y parques (reconocida como "Ciudad de los Parques")
- ~5% zonas hídricas (quebradas menores, drenajes)

#### Generación del Grid

**Algoritmo de colocación de zonas**:
1. Calcular número de celdas objetivo por tipo
2. Generar zonas rectangulares aleatorias:
   - Agua: 2-4 celdas (~80-150m)
   - Parque: 3-6 celdas (~0.4-0.9 ha)
3. Intentar colocar con validación de superposición
4. Límites de seguridad:
   - `max_placement_failures = 50` (fallos consecutivos)
   - `max_total_attempts = 500` (intentos totales)

### Sitios de Cría

#### Permanentes (Celdas AGUA)

- **Ubicación**: Todas las celdas tipo AGUA
- **Persistencia**: Permanente durante simulación
- **Capacidad**: Ilimitada (múltiples huevos por sitio)

#### Temporales (Charcos Post-Lluvia)

**NUEVO**: Sistema dinámico de criaderos temporales

**Parámetros**:
```yaml
temporary_sites:
  min_rainfall: 5.0 mm        # Lluvia mínima para crear charcos
  sites_per_mm: 0.5           # Charcos por mm (10mm → 5 charcos)
  duration_days: 7            # Persistencia sin lluvia
  max_sites: 100              # Límite máximo simultáneo
```

**Lógica de actualización diaria**:
1. Si `precipitación >= 5mm`:
   - Crear `int(precipitación × 0.5)` charcos nuevos
   - Ubicaciones aleatorias uniformes en grid
   - Renovar duración de charcos existentes a 7 días
2. Si `precipitación < 5mm`:
   - Decrementar días restantes de cada charco
   - Eliminar charcos con días = 0

**Justificación**: Bucaramanga tiene régimen pluviométrico bimodal (~1,200 mm/año, ~130 días lluviosos) [2]. Los charcos temporales (techos, llantas, recipientes expuestos) son fuente crítica de criaderos en contextos urbanos [3].

---

## ⏰ Dinámica Temporal

### Escala de Simulación

```
1 paso = 1 día completo
365 pasos = 1 año de simulación
```

### Secuencia de Ejecución Diaria (`step()`)

```python
def step(self):
    """Ejecuta un paso de simulación (1 día)."""
    
    # 1. Actualizar fecha calendario
    self.fecha_actual += timedelta(days=1)
    
    # 2. Actualizar clima diario
    temperatura, precipitación = self._actualizar_clima()
    
    # 3. Actualizar sitios de cría temporales (charcos)
    self._actualizar_sitios_cria_temporales()
    
    # 4. Activar agentes en orden aleatorio
    self.agents.shuffle().do("step")
    # Nota: Mesa 2.3.4 usa AgentSet.shuffle().do() 
    #       NO RandomActivation (versiones antiguas)
    
    # 5. Recolectar métricas diarias
    self.datacollector.collect(self)
```

### Activación de Agentes

**Método**: `SimultaneousActivation` (Mesa 2.3.4)

```python
self.agents.shuffle().do("step")
```

- **Orden aleatorio**: Previene sesgos por orden de ejecución
- **Simultáneo conceptual**: Todos los agentes "deciden" antes de "actuar"
- **Sin scheduler explícito**: Mesa 2.3.4 usa `AgentSet` directamente

### Ciclos Temporales Importantes

| Proceso | Duración | Unidad | Referencia |
|---------|----------|--------|------------|
| Incubación humana (E→I) | 5 | días | [8, 9, 10] |
| Infección humana (I→R) | 6 | días | [8, 9, 10] |
| Desarrollo huevo→adulto | ~10-12 | días (26°C) | [15] |
| Ciclo gonotrófico | 3 | días | [3] |
| Mortalidad mosquito | 0.05 | prob/día | [11] |
| Persistencia charco | 7 | días | [Calibrado] |

---

## 🎛️ Parámetros del Modelo

### Tabla Completa de Parámetros

| Categoría | Parámetro | Valor | Unidad | Justificación |
|-----------|-----------|-------|--------|---------------|
| **Simulación** | | | | |
| | `steps` | 365 | días | Simulación anual |
| | `width` × `height` | 150 × 150 | celdas | ~33.3 km² [1] |
| | `num_humanos` | 3,000 | agentes | Factor escala 1:200 |
| | `num_mosquitos` | 1,500 | agentes | 0.51 hembras/hab [4] |
| | `num_huevos` | 50 | agentes | 279 huevos/km² [3] |
| | `infectados_iniciales` | 5 | agentes | 0.3% población [5] |
| | `mosquitos_infectados_iniciales` | 2 | agentes | 0.4% población |
| **Enfermedad Humana** | | | | |
| | `incubation_period` | 5.0 | días | Promedio 5-6 días [8,9,10] |
| | `infectious_period` | 6.0 | días | Fase virémica [8,9] |
| **Enfermedad Mosquito** | | | | |
| | `mortality_rate` | 0.05 | prob/día | 15-25 días vida [11] |
| | `sensory_range` | 3 | celdas | ~115 m [12] |
| **Transmisión** | | | | |
| | `mosquito_to_human_prob` (α) | 0.6 | prob | Calibrado [12] |
| | `human_to_mosquito_prob` (β) | 0.275 | prob | Calibrado [12] |
| **Movilidad** | | | | |
| | Ver sección [Agentes](#-agentes-del-modelo) | | | |
| **Reproducción Mosquito** | | | | |
| | `eggs_per_female` | 100 | huevos | 60-120 [3] |
| | `mating_probability` | 0.6 | prob | [12] |
| | `female_ratio` | 0.52 | fracción | Levemente sesgado |
| | `gonotrophic_cycle_days` | 3 | días | Ciclo gonotrófico [3] |
| | `immature_development_threshold` | 8.3 | °C | T_base [15] |
| | `immature_thermal_constant` | 181.2 | °C·día | K inmaduro [15] |
| **Criaderos Temporales** | | | | |
| | `min_rainfall` | 5.0 | mm | Umbral formación |
| | `sites_per_mm` | 0.5 | charcos/mm | 10mm → 5 charcos |
| | `duration_days` | 7 | días | Persistencia |
| | `max_sites` | 100 | charcos | Límite simultáneo |
| **Población** | | | | |
| | `student` | 0.30 | fracción | 30% población |
| | `worker` | 0.40 | fracción | 40% población |
| | `mobile` | 0.20 | fracción | 20% población |
| | `stationary` | 0.10 | fracción | 10% población |
| **Entorno** | | | | |
| | `water_ratio` | 0.05 | fracción | 5% celdas [1] |
| | `park_ratio` | 0.10 | fracción | 10% celdas [1] |
| | `water_min/max` | 2-4 | celdas | 80-150m |
| | `park_min/max` | 3-6 | celdas | 0.4-0.9 ha |
| | `max_range` | 5 | celdas | ~190m vuelo [12] |
| **Comportamiento Humano** | | | | |
| | `isolation_probability` | 0.7 | prob | 70% se aíslan |
| | `infected_mobility_radius` | 1 | celda | Movilidad reducida |
| **Generación Grid** | | | | |
| | `max_placement_failures` | 50 | intentos | Seguridad algoritmo |
| | `max_total_attempts` | 500 | intentos | Límite total |

### Archivos de Configuración

**Configuración por defecto**: `config/default_config.yaml`

**Uso**:
```python
model = DengueModel(
    width=150, 
    height=150, 
    num_humanos=3000,
    num_mosquitos=1500,
    climate_data_path='data/climate_bucaramanga_2022.csv'
    # Usa config por defecto
)

# O con configuración personalizada:
import yaml
with open('mi_config.yaml') as f:
    config = yaml.safe_load(f)
    
model = DengueModel(
    width=150, 
    height=150, 
    num_humanos=3000,
    num_mosquitos=1500,
    climate_data_path='data/climate_bucaramanga_2022.csv',
    config=config
)
```

---

## 🔄 Interacciones y Flujos de Transmisión

### Diagrama de Interacciones

```
┌─────────────────────────────────────────────────────────────┐
│                      INTERACCIONES                           │
└─────────────────────────────────────────────────────────────┘

    ┌──────────┐                           ┌──────────┐
    │  Humano  │                           │ Mosquito │
    │    (S)   │                           │   (I)    │
    └────┬─────┘                           └────┬─────┘
         │                                      │
         │  1. Mosquito busca humanos          │
         │     dentro de sensory_range=3       │
         │<────────────────────────────────────│
         │                                      │
         │  2. Se mueve hacia humano           │
         │<────────────────────────────────────│
         │                                      │
         │  3. Ambos en misma celda            │
         │  ┌────────────────────────────────┐ │
         │  │  intentar_picar()              │ │
         │  │  - Humano seleccionado random  │ │
         │  │  - Transmisión: α = 0.6        │ │
         │  └────────────────────────────────┘ │
         │                                      │
    ┌────▼─────┐                                │
    │  Humano  │                                │
    │    (E)   │                                │
    └──────────┘                                │
         │ 5 días (incubation_period)           │
         ▼                                      │
    ┌──────────┐                                │
    │  Humano  │                                │
    │    (I)   │                                │
    └────┬─────┘                                │
         │                           ┌──────────┤
         │  4. Mosquito pica humano  │ Mosquito │
         │     infectado             │   (S)    │
         │  ┌─────────────────────┐  └────┬─────┘
         │  │ intentar_picar()    │       │
         │  │ Transmisión: β=0.275│       │
         │  └─────────────────────┘       │
         │                                │
         │                           ┌────▼─────┐
         │                           │ Mosquito │
         │                           │   (I)    │
         │                           └──────────┘
         │ 6 días (infectious_period)   │ Permanente
         ▼                                │
    ┌──────────┐                          │
    │  Humano  │                          │
    │    (R)   │                          │
    └──────────┘                          │
     (Inmune permanente)       (Infectado de por vida)
```

### Flujo Detallado de Transmisión

#### Mosquito → Humano (α = 0.6)

```python
# En MosquitoAgent.intentar_picar()

# 1. Verificar co-localización
if self.pos == humano.pos:
    
    # 2. Verificar estados
    if self.estado == INFECTADO and humano.es_susceptible():
        
        # 3. Transmisión probabilística
        if random() < α:  # α = 0.6
            humano.get_exposed()  # S → E
```

**Probabilidad efectiva de infección**:
```
P(infección) = P(picadura) × α
             = (contacto espacial) × 0.6
```

#### Humano → Mosquito (β = 0.275)

```python
# En MosquitoAgent.intentar_picar()

# 1. Misma verificación de co-localización
if self.pos == humano.pos:
    
    # 2. Verificar estados
    if self.estado == SUSCEPTIBLE and humano.es_infeccioso():
        
        # 3. Transmisión probabilística
        if random() < β:  # β = 0.275
            self.estado = INFECTADO  # S → I (permanente)
```

### Factores que Afectan la Transmisión

1. **Movilidad humana**: Mayor movilidad → más co-localizaciones → más picaduras
2. **Densidad vectorial**: Más mosquitos → más oportunidades de contacto
3. **Sitios de cría**: Más criaderos → más mosquitos emergiendo
4. **Precipitación**: Lluvia → charcos temporales → más criaderos
5. **Temperatura**: Afecta desarrollo mosquitos (GDD) y mortalidad
6. **Aislamiento infectados**: 70% reducen movilidad → menos transmisión

---

## 💻 Implementación Técnica

### Stack Tecnológico

- **Lenguaje**: Python 3.13.7
- **Framework ABM**: Mesa 2.3.4
- **Análisis**: NumPy, Pandas
- **Visualización**: Matplotlib, Seaborn
- **Configuración**: PyYAML

### Estructura del Proyecto

```
abm-dengue/
├── src/
│   ├── model/
│   │   ├── __init__.py
│   │   ├── dengue_model.py      # Modelo principal
│   │   └── celda.py             # Clase Celda
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── human_agent.py       # Agente humano
│   │   └── mosquito_agent.py    # Agente mosquito
│   ├── utils/
│   │   ├── __init__.py
│   │   └── climate_data.py      # Carga datos climáticos
│   └── visualization/
│       └── ...                   # (Futura visualización)
├── config/
│   └── default_config.yaml       # Configuración por defecto
├── data/
│   ├── climate/
│   │   └── *.csv                 # Datos climáticos (temp, prcp)
│   └── output/
│       └── *.csv                 # Resultados simulación
├── docs/
│   └── sources.txt               # Justificación parámetros
├── tests/
│   └── ...                       # (Futuro: tests unitarios)
├── requirements.txt
├── .gitignore
└── README.md                     # Esta documentación
```

### Características de Implementación

#### Optimizaciones

1. **Solo hembras mosquitos**: Reduce población vectorial ~50%
2. **Caché de parámetros**: Agentes cachean valores del modelo
3. **Lista precomputada de sitios**: `sitios_cria` calculada una vez
4. **Grid urbano cacheado**: 85% de celdas URBANA no se recalcula
5. **AgentSet de Mesa 2.3.4**: Activación eficiente sin scheduler explícito

#### Validaciones

- **Suma de probabilidades**: Valida movilidad ± 0.01
- **Bounds de coordenadas**: Documenta fuentes validadas
- **Errores de configuración**: ValueError descriptivos

#### Datos Climáticos

**Formato CSV requerido**:
```csv
date,tavg,prcp
2022-01-01,25.5,0.0
2022-01-02,26.1,12.3
...
```

- `date`: Fecha (YYYY-MM-DD)
- `tavg`: Temperatura media diaria (°C)
- `prcp`: Precipitación diaria (mm)

**Fuente recomendada**: [IDEAM](https://www.ideam.gov.co/) (Instituto de Hidrología, Meteorología y Estudios Ambientales de Colombia)

---

## 🚀 Instalación y Uso

### Requisitos

- Python 3.8+
- Virtual environment (recomendado)

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/AdrianCCRS/abm-dengue.git
cd abm-dengue

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Uso Básico

```python
from src.model.dengue_model import DengueModel
import pandas as pd

# Crear modelo
model = DengueModel(
    width=150,
    height=150,
    num_humanos=3000,
    num_mosquitos=1500,
    num_huevos=50,
    climate_data_path='data/climate/bucaramanga_2022.csv',
    seed=42  # Para reproducibilidad
)

# Ejecutar simulación (1 año = 365 días)
for i in range(365):
    model.step()
    
    if i % 30 == 0:  # Progreso mensual
        print(f"Día {i}: S={model.contar_susceptibles()}, "
              f"E={model.contar_expuestos()}, "
              f"I={model.contar_infectados()}, "
              f"R={model.contar_recuperados()}")

# Obtener resultados
df = model.datacollector.get_model_vars_dataframe()
df.to_csv('data/output/simulacion_resultado.csv')

# Análisis básico
print(f"\nPico epidémico: {df['Infectados'].max()} casos")
print(f"Día del pico: {df['Infectados'].idxmax()}")
print(f"Casos totales: {df['Recuperados'].iloc[-1]}")
```

### Configuración Personalizada

```yaml
# mi_config.yaml
simulation:
  infectados_iniciales: 10  # Más casos iniciales
  
human_behavior:
  isolation_probability: 0.9  # Mayor aislamiento

mosquito_breeding:
  gonotrophic_cycle_days: 2   # Reproducción más rápida
```

```python
import yaml

with open('mi_config.yaml') as f:
    config = yaml.safe_load(f)

model = DengueModel(
    width=150, height=150, 
    num_humanos=3000, num_mosquitos=1500,
    climate_data_path='data/climate/bucaramanga_2022.csv',
    config=config
)
```

### Análisis de Sensibilidad

```python
import numpy as np
import matplotlib.pyplot as plt

# Variar probabilidad de aislamiento
resultados = []

for p_iso in np.linspace(0, 1, 11):
    config = {'human_behavior': {'isolation_probability': p_iso}}
    
    model = DengueModel(
        width=150, height=150,
        num_humanos=3000, num_mosquitos=1500,
        climate_data_path='data/climate/bucaramanga_2022.csv',
        config=config, seed=42
    )
    
    for _ in range(365):
        model.step()
    
    df = model.datacollector.get_model_vars_dataframe()
    pico = df['Infectados'].max()
    resultados.append({'p_aislamiento': p_iso, 'pico_casos': pico})

# Visualizar
df_sens = pd.DataFrame(resultados)
plt.plot(df_sens['p_aislamiento'], df_sens['pico_casos'])
plt.xlabel('Probabilidad de Aislamiento')
plt.ylabel('Pico de Casos')
plt.title('Análisis de Sensibilidad: Aislamiento')
plt.grid(True)
plt.show()
```

---

## 📚 Referencias

[1] Alcaldía de Bucaramanga, "Revisión General del Plan de Ordenamiento Territorial (POT) 2014–2027," Acuerdo 011 de 2014, Bucaramanga, Colombia, 2014.

[2] Secretaría de Salud y Ambiente de Bucaramanga, "Análisis de Situación de Salud – ASIS Bucaramanga 2022," Bucaramanga, Colombia, 2022.

[3] N. Ruiz et al., "Dinámica de oviposición de Aedes aegypti, estado gonadotrófico y coexistencia con otros culícidos en el área Metropolitana de Bucaramanga, Colombia," Rev. Univ. Ind. Santander Salud, vol. 50, no. 4, pp. 308–319, 2018.

[4] W. Gómez-Vargas et al., "Density of Aedes aegypti and dengue virus transmission risk in two municipalities of Northwestern Antioquia, Colombia," PLoS ONE, vol. 19, no. 1, e0295317, 2024.

[5] Ministerio de Salud y Protección Social – Instituto Nacional de Salud, "Dengue, Dengue grave y mortalidad por dengue, municipio de Bucaramanga," Datos Abiertos Colombia, 2015–2025.

[6] V. H. Peña-García et al., "Infection rates by dengue virus in mosquitoes and humans in two Colombian cities," Am. J. Trop. Med. Hyg., vol. 94, no. 5, pp. 1066–1074, 2016.

[7] R. Pérez-Castro et al., "Detection of all four dengue serotypes in Aedes aegypti female mosquitoes from Medellín, Colombia," Mem. Inst. Oswaldo Cruz, vol. 111, no. 4, pp. 233–240, 2016.

[8] Organización Mundial de la Salud, "Dengue y dengue grave," Nota descriptiva, 2024.

[9] Instituto Nacional de Salud, "Protocolo de Vigilancia en Salud Pública: Dengue," Bogotá, Colombia, 2024.

[10] H. Nishiura and S. B. Halstead, "Natural history of dengue virus infections," J. Infect. Dis., vol. 195, no. 7, pp. 1007–1013, 2007.

[11] J. Arévalo-Cortés et al., "Life tables and longevity of Aedes aegypti under laboratory conditions from different Colombian populations," Insects, vol. 13, no. 6, p. 536, 2022.

[12] A. Jindal and S. Rao, "Agent-Based Modeling and Simulation of Mosquito-Borne Disease Transmission," Int. J. Simul. Model., vol. 16, no. 3, pp. 422–432, 2017.

[13] Observatorio Laboral de Santander, Informe del Mercado Laboral del Área Metropolitana de Bucaramanga 2022, Bucaramanga, Colombia, 2022.

[14] R. Focks et al., "Dynamic life table model for Aedes aegypti: analysis and development," J. Med. Entomol., vol. 30, no. 6, pp. 1003–1017, 1993.

[15] W. Tun-Lin et al., "Effects of temperature and larval diet on development rates of Aedes aegypti in north Queensland," Med. Vet. Entomol., vol. 14, no. 1, pp. 31–37, 2000.

[16] Iowa State University Extension, "Growing Degree Days for Insect Pests," 2023.

[17] The Ohio State University, "Growing Degree Days (GDD) Glossary," 2023.

---

## 📄 Licencia

Este proyecto es parte de un trabajo académico para la Universidad Industrial de Santander.

**Contacto**: [adrian.caceres@saber.uis.edu.co](mailto:adrian.caceres@saber.uis.edu.co)

---

## 🙏 Agradecimientos

- **Mesa Development Team**: Por el framework ABM
- **IDEAM**: Por los datos climáticos de Colombia
- **Secretaría de Salud de Bucaramanga**: Por el ASIS 2022
- **Investigadores citados**: Por fundamentación científica del modelo

---

**Última actualización**: Noviembre 2025  
**Versión del modelo**: 1.0.0  
**Mesa version**: 2.3.4
