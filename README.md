# Modelo Basado en Agentes (ABM) para Transmisión del Dengue en Bucaramanga

**Autores:** Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez  
**Institución:** Universidad Industrial de Santander - Simulación Digital F1  
**Framework:** Mesa 2.3.4 (Python)

---

## 📋 Índice

1. [Descripción General](#-descripción-general)
2. [Características Principales](#-características-principales)
3. [Estructura del Proyecto](#-estructura-del-proyecto)
4. [Instalación](#-instalación)
5. [Uso](#-uso)
6. [Arquitectura del Modelo](#-arquitectura-del-modelo)
7. [Documentación Adicional](#-documentación-adicional)

---

## 🎯 Descripción General

Modelo basado en agentes que simula la dinámica de transmisión del dengue en Bucaramanga, Colombia, utilizando un **enfoque metapoblacional** para representar las poblaciones de mosquitos de manera computacionalmente eficiente.

### Características Principales

- **10,000 agentes humanos** con modelo epidemiológico SEIR y 4 patrones de movilidad
- **Modelo metapoblacional de mosquitos** (poblaciones por celda en arrays numpy)
- **Transmisión vertical** del virus (30% de huevos infectados de hembras infectadas)
- **Datos climáticos reales** (temperatura y precipitación) que afectan desarrollo vectorial
- **Grid urbano 50×50** (~100m × 100m por celda = 25 km²)
- **Simulaciones de 364 días** con escala temporal diaria


---

## 🔧 Estructura del Proyecto

```
abm-dengue/
├── config/                      # Archivos de configuración
│   ├── default_config.yaml      # Configuración por defecto
│   └── experiments/             # Configuraciones de experimentos
├── data/
│   └── raw/                     # Datos climáticos históricos
├── src/                         # Código fuente del modelo
│   ├── agents/                  # Agentes (humanos y mosquitos)
│   ├── model/                   # Modelo principal y componentes
│   │   ├── dengue_model.py      # Modelo principal
│   │   ├── mosquito_population.py  # Grid metapoblacional
│   │   ├── egg_manager.py       # Gestión de huevos
│   │   └── celda.py             # Tipos de celdas urbanas
│   ├── strategies/              # Estrategias de control (futuro)
│   └── utils/                   # Utilidades (carga de clima)
├── main.py                      # Script principal de ejecución
├── run_parallel_experiments.py # Ejecución paralela de experimentos
└── requirements.txt             # Dependencias Python
```

---

## 🚀 Instalación

### Requisitos

- Python 3.8+
- pip

### Pasos de instalación

```bash
# Clonar el repositorio
git clone https://github.com/AdrianCCRS/abm-dengue.git
cd abm-dengue

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias principales

- `mesa==2.3.4` - Framework ABM
- `numpy==1.26.4` - Computación numérica
- `pandas==2.2.2` - Manejo de datos
- `matplotlib==3.8.4` - Visualización
- `PyYAML==6.0.1` - Configuración

---

## 💻 Uso

### Ejecución básica

```bash
# Ejecutar simulación con configuración por defecto
python main.py

# Ejecutar con configuración personalizada
python main.py --config config/mi_config.yaml

# Especificar parámetros por línea de comandos
python main.py --steps 365 --humanos 10000 --seed 42
```

### Ejecución de experimentos paralelos

```bash
# Ejecutar 16 simulaciones en paralelo (4 semillas × 4 condiciones)
python run_parallel_experiments.py --config config/experiments/example_batch.yaml
```

### Argumentos disponibles

- `--config`: Ruta al archivo de configuración YAML
- `--steps`: Número de días a simular (default: 364)
- `--humanos`: Número de agentes humanos (default: 10000)
- `--mosquitos`: Población inicial de mosquitos (default: 5000)
- `--seed`: Semilla para reproducibilidad
- `--output`: Directorio de salida para resultados

---

## 🏗️ Arquitectura del Modelo

### Modelo Epidemiológico

#### Humanos: SEIR

```
S → E → I → R
```

- **S (Susceptible)**: Puede infectarse por picadura de mosquito infectado
- **E (Expuesto)**: Período de incubación de 5 días
- **I (Infectado)**: Período infeccioso de 8 días
- **R (Recuperado)**: Inmunidad permanente

#### Mosquitos: SEI (Metapoblacional)

```
S_m → E_m → I_m
```

Cada celda del grid mantiene contadores de mosquitos por estado:
- **S_m**: Mosquitos susceptibles (pueden infectarse)
- **E_m**: Mosquitos expuestos (incubando virus, 7 días)
- **I_m**: Mosquitos infectados (transmiten virus de por vida)

### Transmisión del Virus

1. **Horizontal (mosquito ↔ humano)**:
   - Mosquito infectado pica humano susceptible → probabilidad α
   - Mosquito susceptible pica humano infectado → probabilidad β

2. **Vertical (hembra → huevos)**:
   - 30% de huevos de hembras infectadas nacen infectados
   - Permite persistencia viral entre generaciones

### Efectos Climáticos

**Temperatura afecta**:
- Desarrollo de huevos (grados-día acumulados, umbral 8.3°C)
- Período de incubación extrínseca (7-20 días)
- Mortalidad de adultos (aumenta en extremos)
- Actividad de picadura (óptima 25-30°C)

**Precipitación afecta**:
- Creación de criaderos temporales (>5mm)
- Brotes epidémicos por lluvia intensa (>15mm)
- Mortalidad larvaria por sequía prolongada

### Patrones de Movilidad Humana

- **Estudiantes (25%)**: Casa → Escuela → Parque
- **Trabajadores (50%)**: Casa → Oficina → (ocasional parque)
- **Móviles (15%)**: Movimiento aleatorio continuo
- **Estacionarios (10%)**: Principalmente en casa

---

## 📚 Documentación Adicional

- **[LOGICA_MODELO.md](LOGICA_MODELO.md)**: Descripción detallada de la lógica del modelo
- **[docs/GUARDADO_INCREMENTAL.md](docs/GUARDADO_INCREMENTAL.md)**: Sistema de guardado de resultados
- **[config/default_config.yaml](config/default_config.yaml)**: Parámetros configurables con comentarios

### Resultados de Simulación

Los resultados se guardan en el directorio `experimento_YYYYMMDD_HHMMSS/`:
- `configuracion.yaml`: Parámetros utilizados
- `datos_consolidados.csv`: Datos agregados de todas las corridas
- `resumen_experimentos.csv`: Métricas resumen por corrida
- `run_XXX_*/`: Resultados individuales de cada simulación
  - `datos_completos.csv`: Series temporales completas
  - `parametros.yaml`: Parámetros específicos
  - `resumen.json`: Métricas finales

### Análisis en R

El proyecto incluye scripts de R para análisis estadístico avanzado:
- `r_analysis/Procesamiento de Datos Simulados.Rmd`: Análisis de resultados de simulaciones

---

## 🔬 Referencias Científicas

1. Jindal, A., & Rao, S. (2017). Agent-based model of dengue transmission. *IIIT Delhi*.
2. Keeling, M. J., & Rohani, P. (2008). *Modeling infectious diseases in humans and animals*. Princeton University Press.
3. Tun-Lin, W., Burkot, T. R., & Kay, B. H. (2000). Effects of temperature and larval diet on development rates of *Aedes aegypti*. *Medical and Veterinary Entomology*, 14(1), 31-37.
4. Scott, T. W., & Morrison, A. C. (2003). Aedes aegypti density and the risk of dengue virus transmission. *Ecological Aspects for Application of Genetically Modified Mosquitoes*, 187-206.
5. Gunther, J., et al. (2007). Vertical transmission of dengue virus in *Aedes aegypti*. *PLOS Neglected Tropical Diseases*.
6. Alcaldía de Bucaramanga (2014). Revisión General del Plan de Ordenamiento Territorial (POT) 2014–2027.
7. Secretaría de Salud y Ambiente de Bucaramanga (2022). Análisis de Situación de Salud – ASIS Bucaramanga 2022.

---

## 📝 Licencia

Este proyecto es parte de un trabajo académico de la Universidad Industrial de Santander.

## 👥 Contacto

Para preguntas o colaboraciones, contactar a los autores a través de la Universidad Industrial de Santander.

---

**Última actualización:** 25 de noviembre de 2025  
**Versión:** 2.0 (Modelo Metapoblacional)  
**Repositorio:** [github.com/AdrianCCRS/abm-dengue](https://github.com/AdrianCCRS/abm-dengue)


- **S (Susceptible)**: Puede infectarse al picar humano infectado
- **I (Infectado)**: Infección permanente, transmite virus de por vida
- **No recuperación**: Los mosquitos no se recuperan del virus

### Escala Espacial

**Grid 50 × 50 = 2,500 celdas**

- **Celda**: ~100 m × 100 m (~10,000 m² = 1 hectárea)
- **Área total**: ~25 km² (zona urbana consolidada de Bucaramanga)
- **Resolución**: Escala de barrio/cuadrante urbano
- **Rango mosquito**: 5 celdas (~500 m diarios) [12]

**Justificación**: Bucaramanga tiene 33.28 km² de suelo urbano consolidado [1]. Con 50×50 celdas de ~100m × 100m, se capturan interacciones vector-huésped a nivel de barrio sin sobredimensionar computacionalmente. El área de 25 km² cubre las zonas de mayor densidad urbana donde ocurre la mayor transmisión de dengue.

### Escala Temporal

⚠️ **CRÍTICO: 1 step = 1 día (NO horas)**

El modelo opera en **escala diaria**:
- **1 paso de simulación = 1 día completo**
- **200 pasos = ~6.5 meses** (duración típica de simulación)
- **Movilidad humana**: Probabilidades diarias de ubicación (NO horarios)
- **Desarrollo mosquitos**: Grados-día acumulados diariamente

**Justificación biológica**:
- Período de incubación humano: 5 **días** [8, 9, 10]
- Período infeccioso humano: 6 **días** [8, 9, 10]
- Ciclo gonotrófico mosquito: 3 **días** [3]
- Desarrollo inmaduro: ~10-14 **días** a 26°C [14, 15]

Modelar en horas sobrecomplicaría sin aportar precisión epidemiológica relevante.

### Factor de Escala Poblacional

**1 agente humano = 60 personas reales**

- **Población simulada**: 10,000 agentes
- **Población real representada**: ~600,000 habitantes
- **Población urbana Bucaramanga**: 608,947 habitantes (ASIS 2022 [2])
- **Error**: < 1.5%

**Beneficios**:
- Mantiene densidad urbana realista (~24,000 hab/km²)
- Computacionalmente manejable
- Preserva proporciones epidemiológicas

---

## 🦟 Modelo Metapoblacional de Mosquitos

### ¿Por qué Metapoblacional?

**Problema con agentes individuales**:
```
100,000 mosquitos × 50 bytes/agente = 5 MB memoria
100,000 iteraciones por paso = computacionalmente prohibitivo
```

**Solución metapoblacional**:
```python
# Arrays numpy por celda (50×50)
S_m = np.zeros((50, 50), dtype=int)  # Susceptibles
E_m = np.zeros((50, 50), dtype=int)  # Expuestos (incubando virus)
I_m = np.zeros((50, 50), dtype=int)  # Infectados

# 2,500 celdas × 12 bytes = 30 KB memoria (166× menos)
# 2,500 iteraciones por paso (40× más rápido)
```

### Estados Epidemiológicos de Mosquitos

```
S (Susceptible) → E (Expuesto) → I (Infectado)
                    ↑
                    β (pica humano infectado)
```

**Diferencias con humanos**:
- **NO hay recuperación**: Una vez infectado, permanece así de por vida
- **Estado E**: Período de incubación extrínseca (EIP) del virus en el mosquito
- **EIP variable**: 7-20 días según temperatura (10 días a 26°C)

### Procesos Metapoblacionales

#### 1. Desarrollo de Huevos (GDD)

**Manager centralizado** con cohortes independientes:
```python
class LoteHuevos:
    pos: Tuple[int, int]      # Ubicación criadero
    sanos: int                # Huevos no infectados
    infectados: int           # Huevos con transmisión vertical
    grados_acumulados: float  # Suma de GDD
    dias_edad: int           # Edad del lote
```

**Desarrollo diario**:
```python
GD = max(temperatura - 8.3, 0.0)
lote.grados_acumulados += GD
if lote.grados_acumulados >= 181.2:  # Constante térmica
    # Eclosión
    S_m[pos] += lote.sanos
    I_m[pos] += lote.infectados  # Nacen infectados (transmisión vertical)
```

#### 2. Mortalidad Adultos

**Proceso binomial estocástico**:
```python
tasa_base = 0.05  # 5% diario (vida media ~20 días)
multiplicador = temperatura_mortality_factor(temp)
tasa_efectiva = tasa_base * multiplicador

muertos_S = np.random.binomial(S_m[x,y], tasa_efectiva)
muertos_E = np.random.binomial(E_m[x,y], tasa_efectiva)
muertos_I = np.random.binomial(I_m[x,y], tasa_efectiva)

S_m[x,y] -= muertos_S
E_m[x,y] -= muertos_E
I_m[x,y] -= muertos_I
```

**Multiplicador por temperatura**:
| Temperatura | Multiplicador | Tasa Efectiva | Vida Media |
|-------------|---------------|---------------|------------|
| <10°C       | 2.5×          | 12.5%         | 8 días     |
| 10-15°C     | 1.5×          | 7.5%          | 13 días    |
| 15-32°C     | 1.0×          | 5.0%          | 20 días    |
| 32-37°C     | 1.5×          | 7.5%          | 13 días    |
| >37°C       | 2.5×          | 12.5%         | 8 días     |

#### 3. Incubación Extrínseca (E → I)

**Progresión binomial con probabilidad temperatura-dependiente**:
```python
eip_dias = extrinsic_incubation_period(temp)  # 7-20 días
prob_transicion = 1.0 / eip_dias

nuevos_infectados = np.random.binomial(E_m[x,y], prob_transicion)
E_m[x,y] -= nuevos_infectados
I_m[x,y] += nuevos_infectados
```

| Temperatura | EIP (días) | Prob. Diaria |
|-------------|------------|--------------|
| 18°C        | 20         | 5.0%         |
| 22°C        | 15         | 6.7%         |
| 26°C        | 10         | 10.0%        |
| 30°C        | 8          | 12.5%        |
| 35°C        | 7          | 14.3%        |

#### 4. Reproducción

**Solo hembras** con ciclo gonotrófico:
```python
# Por cada celda con mosquitos
total_adultos = S_m[x,y] + E_m[x,y] + I_m[x,y]
hembras = total_adultos * 0.52  # 52% son hembras

if cooldown_gonotrofico >= 3:  # 3 días desde última puesta
    huevos_totales = int(hembras * 50)  # 50 huevos/hembra
    
    # Transmisión vertical de hembras infectadas
    prop_infectadas = I_m[x,y] / total_adultos
    huevos_infectados = int(huevos_totales * prop_infectadas * 0.05)
    huevos_sanos = huevos_totales - huevos_infectados
    
    # Depositar en sitio de cría cercano
    egg_manager.add_eggs(sitio, huevos_sanos, huevos_infectados)
```

### Sitios de Cría

#### Permanentes (Celdas AGUA)
- ~5% del grid (125 celdas)
- Persistencia indefinida
- Capacidad ilimitada

#### Temporales (Charcos Post-Lluvia)
```python
if precipitacion >= 5.0:
    charcos_nuevos = int(precipitacion * 0.5)  # 10mm → 5 charcos
    duracion = 7  # días sin lluvia
```

**Dinámica de charcos**:
- Se crean con lluvia >5mm
- Persisten 7 días sin lluvia
- Se renuevan con nueva lluvia
- Máximo 100 charcos simultáneos

### Lluvia Intensa → Brotes Epidémicos

**Mecanismo de emergencia masiva**:
```python
if precipitacion >= 15.0:  # Lluvia intensa
    # Crear charcos
    charcos = int(precipitacion / 2.0)
    
    # Calcular emergencia de mosquitos
    factor = (precipitacion - 15.0) / 10.0
    mosquitos_emergentes = min(int(23.2 * factor), 100)
    
    # Distribuir en charcos nuevos (INFECTADOS)
    for charco in random.sample(charcos, len(charcos)):
        I_m[charco] += mosquitos_emergentes // len(charcos)
```

**Ejemplo real**:
- Día 37: 50mm lluvia → 25 charcos, **100 mosquitos infectados** insertados
- Día 57: 49mm lluvia → 24 charcos, **94 mosquitos infectados**
- Día 78: 50mm lluvia → 25 charcos, **100 mosquitos infectados**

**Resultado epidemiológico**: Picos de mosquitos infectados 2-3 días después de lluvias intensas, simulando brotes observados en Bucaramanga.

---

## 👥 Agentes del Modelo

### Solo Agentes Humanos (v2.0)

⚠️ **IMPORTANTE**: En v2.0, **solo humanos son agentes individuales**. Los mosquitos se manejan mediante el modelo metapoblacional descrito arriba.

### 1. Agente Humano (`HumanAgent`)

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

### 2. Interacción Humano-Mosquito (Transmisión)

Aunque los mosquitos NO son agentes individuales en v2.0, la **transmisión** sigue siendo un proceso de interacción espacial entre humanos y poblaciones vectoriales.

#### Proceso de Picadura

**Ubicación espacial**:
```python
# Humano en celda (x, y)
mosquitos_I_en_celda = I_m[x, y]  # Mosquitos infectados presentes

# Probabilidad de picadura
num_picaduras = np.random.poisson(mosquitos_I_en_celda * bite_rate)

# Transmisión por cada picadura
for _ in range(num_picaduras):
    if random() < α:  # α = 0.6 (mosquito→humano)
        humano.get_exposed()  # S → E
        break  # Una infección es suficiente
```

#### Adquisición del Virus por Mosquitos

```python
# Humano infectado en celda (x, y)
mosquitos_S_en_celda = S_m[x, y]

# Picaduras recibidas
num_picaduras = np.random.poisson(mosquitos_S_en_celda * bite_rate)

# Transmisión humano→mosquito
nuevos_infectados = 0
for _ in range(num_picaduras):
    if random() < β:  # β = 0.275 (humano→mosquito)
        nuevos_infectados += 1

# Actualizar poblaciones
S_m[x, y] -= nuevos_infectados
E_m[x, y] += nuevos_infectados  # Entran en incubación
```

**Tasa de picadura (`bite_rate`)**:
- Base: 0.5 picaduras/mosquito/día
- Modificada por:
  * Temperatura (<18°C o >32°C reduce actividad)
  * Precipitación (>10mm reduce en 50%)
  * Hora del día (implícito en modelo diario)

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

## 🌡️ Efectos Climáticos

El modelo integra **7 efectos de temperatura** y **4 efectos de precipitación** que modulan la dinámica vectorial de manera realista.

### Efectos de la Temperatura

#### 1. Desarrollo de Huevos (GDD)

**Modelo de Grados-Día Acumulados**:
```python
GD = max(temperatura - 8.3, 0.0)  # T_base = 8.3°C
acumulado += GD
if acumulado >= 181.2:  # K = 181.2°C·día
    eclosión()
```

| Temperatura | GD/día | Días hasta eclosión |
|-------------|--------|---------------------|
| 15°C        | 6.7    | 27 días             |
| 20°C        | 11.7   | 15 días             |
| 25°C        | 16.7   | 11 días             |
| 30°C        | 21.7   | 8 días              |
| 35°C        | 26.7   | 7 días              |

#### 2. Mortalidad de Adultos

**Multiplicador de mortalidad base (5% diario)**:
```python
if temp < 10:      multiplicador = 2.5  # Extremo frío
elif temp < 15:    multiplicador = 1.5  # Subóptimo
elif temp < 32:    multiplicador = 1.0  # Óptimo
elif temp < 37:    multiplicador = 1.5  # Subóptimo
else:              multiplicador = 2.5  # Extremo calor
```

| Temperatura | Mortalidad | Vida Media |
|-------------|------------|------------|
| <10°C       | 12.5%      | 8 días     |
| 10-15°C     | 7.5%       | 13 días    |
| 15-32°C     | 5.0%       | 20 días    |
| 32-37°C     | 7.5%       | 13 días    |
| >37°C       | 12.5%      | 8 días     |

#### 3. Período de Incubación Extrínseca (EIP)

**Duración del EIP modulada por temperatura**:
```python
if temp < 18:      eip = 20  # Muy lento
elif temp < 22:    eip = 15
elif temp < 26:    eip = 10  # Óptimo
elif temp < 30:    eip = 8
elif temp < 35:    eip = 7   # Muy rápido
else:              eip = 20  # Calor extremo inhibe
```

**Impacto epidemiológico**: EIP más corto → mosquitos infectados más rápido → mayor transmisión

#### 4. Actividad de Picadura

**Factor de reducción**:
```python
if temp < 18 or temp > 32:
    bite_rate *= 0.3  # 70% reducción
```

**Justificación**: *Aedes aegypti* tiene actividad óptima 18-32°C

#### 5. Actividad Reproductiva

**Inhibición en extremos**:
```python
if temp < 15 or temp > 35:
    reproducción_pausada = True
```

#### 6. Mortalidad de Larvas (Huevos)

**Incrementada en rangos subóptimos**:
```python
if temp < 15 or temp > 32:
    mortalidad_huevos *= 1.5  # 50% más mortalidad
```

#### 7. Longevidad General

Resultado combinado de todos los efectos anteriores.

### Efectos de la Precipitación

#### 1. Creación de Criaderos Temporales

```python
if precipitacion >= 5.0:
    charcos = int(precipitacion * 0.5)
    duracion = 7  # días
```

**Ejemplo**: 20mm → 10 charcos nuevos

#### 2. Reducción de Actividad de Picadura

```python
if precipitacion > 10.0:
    bite_rate *= 0.5  # Mosquitos refugiados
```

#### 3. Sequía Prolongada

```python
dias_sin_lluvia += 1
if dias_sin_lluvia > 7:
    mortalidad_larvas *= 1.3  # Charcos secándose
```

#### 4. Lluvia Intensa → Brotes Epidémicos

```python
if precipitacion >= 15.0:
    factor = (precipitacion - 15.0) / 10.0
    mosquitos_emergentes = min(int(23.2 * factor), 100)
    # Insertar en I_m (infectados)
```

**Casos reales observados en simulación**:
- 20mm → 5 mosquitos infectados insertados
- 50mm → 100 mosquitos infectados (límite)
- 80mm → 100 mosquitos infectados (límite)

**Mecanismo biológico**: Huevos de *Aedes* en diapausa (meses secos) eclosionan simultáneamente con lluvia intensa, generando picos vectoriales 2-3 días después, consistente con brotes post-tormenta observados epidemiológicamente.

### Datos Climáticos

**Formato CSV requerido**:
```csv
date,tavg,prcp
2022-01-01,25.5,0.0
2022-01-02,26.1,12.3
2022-01-03,24.8,0.5
```

- `date`: Fecha (YYYY-MM-DD)
- `tavg`: Temperatura media diaria (°C)
- `prcp`: Precipitación diaria (mm)

**Fuente**: IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales de Colombia)

**Archivo actual**: `data/raw/datos_climaticos_2022.csv`

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

**Simulación estándar con v2.0**:

```python
from src.model.dengue_model import DengueModel
import pandas as pd
import matplotlib.pyplot as plt

# Crear modelo (v2.0 con metapoblación)
model = DengueModel(
    width=50,               # Grid 50×50 (v2.0)
    height=50,
    num_humanos=10000,      # 10,000 humanos (escala 1:60)
    num_mosquitos=5000,     # Mosquitos iniciales (metapoblación)
    num_huevos=500,         # Huevos iniciales
    infectados_iniciales=5, # Humanos infectados iniciales
    mosquitos_infectados_iniciales=2,
    climate_data_path='data/raw/datos_climaticos_2022.csv',
    fecha_inicio=datetime(2022, 1, 1),
    seed=42  # Reproducibilidad
)

# Ejecutar simulación (200 días ~6.5 meses)
print("Iniciando simulación...")
for i in range(200):
    model.step()
    
    if (i + 1) % 10 == 0:  # Progreso cada 10 días
        S = model.contar_susceptibles()
        E = model.contar_expuestos()
        I = model.contar_infectados()
        R = model.contar_recuperados()
        mosq_total = model.S_m.sum() + model.E_m.sum() + model.I_m.sum()
        mosq_inf = model.I_m.sum()
        huevos = model.egg_manager.contar_total_huevos()
        
        print(f"Día {i+1:3d}: H[S:{S:5d} E:{E:3d} I:{I:3d} R:{R:3d}] "
              f"M[Total:{mosq_total:6d} I:{mosq_inf:4d}] "
              f"Huevos:{huevos:7d}")

# Obtener resultados
df = model.datacollector.get_model_vars_dataframe()
df.to_csv('results/simulacion_v2_resultado.csv', index=False)

# Análisis básico
print(f"\n{'='*60}")
print(f"RESUMEN ESTADÍSTICO:")
print(f"{'='*60}")
print(f"Pico de infectados: {df['Infectados'].max()} casos")
print(f"Día del pico: {df['Infectados'].idxmax()}")
print(f"Total recuperados: {df['Recuperados'].iloc[-1]}")
print(f"Tasa de ataque: {df['Recuperados'].iloc[-1] / 10000 * 100:.2f}%")
print(f"Mosquitos al final: {df['Mosquitos_Adultos'].iloc[-1]}")
print(f"Mosquitos infectados al final: {df['Mosquitos_Infectados'].iloc[-1]}")
print(f"Temperatura promedio: {df['Temperatura'].mean():.2f}°C")
print(f"Precipitación total: {df['Precipitacion'].sum():.2f}mm")
print(f"{'='*60}")

# Visualización
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Epidemia humana (SEIR)
axes[0, 0].plot(df.index, df['Susceptibles'], label='S', color='blue')
axes[0, 0].plot(df.index, df['Expuestos'], label='E', color='orange')
axes[0, 0].plot(df.index, df['Infectados'], label='I', color='red', linewidth=2)
axes[0, 0].plot(df.index, df['Recuperados'], label='R', color='green')
axes[0, 0].set_xlabel('Día')
axes[0, 0].set_ylabel('Población Humana')
axes[0, 0].set_title('Dinámica SEIR Humanos')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Mosquitos
axes[0, 1].plot(df.index, df['Mosquitos_Adultos'], label='Total', color='brown')
axes[0, 1].plot(df.index, df['Mosquitos_Infectados'], label='Infectados', 
                color='darkred', linewidth=2)
axes[0, 1].set_xlabel('Día')
axes[0, 1].set_ylabel('Población Mosquitos')
axes[0, 1].set_title('Dinámica Mosquitos (Metapoblación)')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Clima
ax_temp = axes[1, 0]
ax_prcp = ax_temp.twinx()
ax_temp.plot(df.index, df['Temperatura'], color='red', label='Temperatura')
ax_prcp.bar(df.index, df['Precipitacion'], alpha=0.3, color='blue', label='Precipitación')
ax_temp.set_xlabel('Día')
ax_temp.set_ylabel('Temperatura (°C)', color='red')
ax_prcp.set_ylabel('Precipitación (mm)', color='blue')
ax_temp.set_title('Clima Diario')
ax_temp.tick_params(axis='y', labelcolor='red')
ax_prcp.tick_params(axis='y', labelcolor='blue')
ax_temp.grid(True, alpha=0.3)

# Huevos y criaderos
axes[1, 1].plot(df.index, df['Huevos_Totales'], label='Huevos Totales', color='brown')
axes[1, 1].plot(df.index, df['Huevos_Infectados'], label='Huevos Infectados', 
                color='darkred', linewidth=2)
ax_charcos = axes[1, 1].twinx()
ax_charcos.plot(df.index, df['Charcos'], color='blue', alpha=0.5, 
                label='Charcos', linestyle='--')
axes[1, 1].set_xlabel('Día')
axes[1, 1].set_ylabel('Número de Huevos', color='brown')
ax_charcos.set_ylabel('Charcos Activos', color='blue')
axes[1, 1].set_title('Huevos y Sitios de Cría')
axes[1, 1].tick_params(axis='y', labelcolor='brown')
ax_charcos.tick_params(axis='y', labelcolor='blue')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/graficas_v2_resultado.png', dpi=150)
print(f"\nGráficas guardadas en: results/graficas_v2_resultado.png")
```

**Salida esperada**:
```
Día  10: H[S: 9995 E:  0 I:  0 R:  5] M[Total:  4823 I: 147] Huevos:   4256
Día  20: H[S: 9995 E:  0 I:  0 R:  5] M[Total:  3654 I: 125] Huevos:   5489
Día  30: H[S: 9997 E:  0 I:  0 R:  3] M[Total:   315 I: 109] Huevos:   6574
...
Día 200: H[S: 9995 E:  0 I:  1 R:  4] M[Total:460114 I: 307] Huevos:6694554

============================================================
RESUMEN ESTADÍSTICO:
============================================================
Pico de infectados: 3 casos
Día del pico: 5
Total recuperados: 4
Tasa de ataque: 0.04%
Mosquitos al final: 460114
Mosquitos infectados al final: 307
Temperatura promedio: 21.47°C
Precipitación total: 1345.90mm
============================================================
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

## 📖 Documentación Adicional

Este README proporciona una **visión general técnica** del modelo. Para documentación más detallada, consulte:

### LOGICA_MODELO.md

**Descripción completa de la lógica del modelo** con:
- Explicaciones paso a paso de cada componente
- Ejemplos numéricos concretos con cálculos detallados
- Diagramas ASCII de procesos temporales y espaciales
- Justificación biológica de cada mecanismo
- Casos de uso con personajes ejemplo (María, Pedro, Juan, Ana)

**Secciones principales**:
1. **Arquitectura General**: Explicación del paradigma ABM y componentes
2. **Flujo de Simulación Diaria**: 10 pasos detallados con ejemplos
3. **Modelo Metapoblacional**: Eficiencia, desarrollo GDD, reproducción, sitios de cría
4. **Población Humana**: Tipos de movilidad, progresión SEIR, aislamiento
5. **Efectos Climáticos**: 7 efectos de temperatura, 4 de precipitación
6. **Estrategias de Control**: LSM, ITN/IRS (actualmente deshabilitadas)
7. **Transmisión del Virus**: Ciclo completo, probabilidades α y β, R₀

**Nivel de detalle**: **Máximo**. Diseñado para:
- Programadores que implementan el modelo
- Biólogos/epidemiólogos sin experiencia en modelado
- Secciones de métodos de artículos científicos
- Material educativo sobre ABM y epidemiología

**Cómo usar**: Leer sección por sección según necesidad. Cada sección es autocontenida con ejemplos completos.

### TRANSMISION_VERTICAL.md

**Documentación específica** sobre el mecanismo de transmisión vertical del virus dengue en mosquitos:
- Justificación biológica (literatura científica)
- Implementación técnica en el modelo metapoblacional
- Parámetros clave (5% de transmisión vertical)
- Impacto epidemiológico en persistencia viral
- Validación con datos de campo

### PARAMETROS_MODELO.md

**Tabla completa de parámetros** con:
- Valores por defecto
- Rangos válidos
- Referencias bibliográficas
- Justificación de calibración
- Sensibilidad del modelo a cada parámetro

### docs/sources.txt

**Referencias específicas** para cada parámetro del modelo con citas bibliográficas exactas.

### PROJECT_STATUS.md

**Estado actual del proyecto**:
- Componentes implementados
- Componentes en desarrollo
- Resultados de validación
- Próximos pasos (v2.1, v2.2)

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

- **Mesa Development Team**: Por el framework ABM en Python
- **IDEAM**: Por los datos climáticos históricos de Colombia
- **Secretaría de Salud de Bucaramanga**: Por el ASIS 2022 y datos epidemiológicos
- **Investigadores citados**: Por la fundamentación científica del modelo
- **Comunidad académica UIS**: Por el apoyo en el desarrollo del proyecto

---

## 📊 Estado del Proyecto

**Versión actual**: 2.0.0 (Metapoblacional)  
**Última actualización**: 24 de noviembre de 2025  
**Mesa version**: 2.3.4  
**Python**: 3.13.7

### Componentes Implementados ✅

- ✅ Modelo metapoblacional de mosquitos (S_m, E_m, I_m)
- ✅ Transmisión vertical del virus (5%)
- ✅ Efectos climáticos complejos (7 temperatura + 4 precipitación)
- ✅ Lluvia intensa → brotes epidémicos
- ✅ Manager de huevos con desarrollo GDD
- ✅ Población humana SEIR con movilidad heterogénea
- ✅ Integración de datos climáticos CSV reales
- ✅ Sistema de criaderos permanentes y temporales
- ✅ Documentación técnica exhaustiva (LOGICA_MODELO.md)

### En Desarrollo 🚧

- 🚧 Calibración con datos reales de Bucaramanga 2022
- 🚧 Validación de R₀ efectivo
- 🚧 Análisis de sensibilidad de parámetros
- 🚧 Comparación con curvas epidemiológicas reales

### Próxima Versión (v2.1) 🔮

- 🔜 Reactivación de estrategias de control (LSM, ITN/IRS)
- 🔜 Simulación de múltiples serotipos (DENV1-4)
- 🔜 Inmunidad cruzada parcial
- 🔜 Visualización interactiva con Mesa
- 🔜 Dashboard web con resultados en tiempo real

---

**Repositorio**: [github.com/AdrianCCRS/abm-dengue](https://github.com/AdrianCCRS/abm-dengue)  
**Documentación**: Ver [LOGICA_MODELO.md](LOGICA_MODELO.md) para detalles técnicos completos
