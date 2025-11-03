# Resumen del Proyecto: ABM-Dengue-Bucaramanga

## 📁 Estructura del Proyecto Creada

```
amb-dengue/
├── 📄 .copilot-context.json        # Contexto del proyecto para Copilot
├── 📄 .gitignore                   # Archivos ignorados por Git
├── 📄 README.md                    # Documentación principal
├── 📄 GUIA_DESARROLLO.md          # Guía paso a paso (10 fases)
├── 📄 INICIO_RAPIDO.md            # Quick start guide
├── 📄 requirements.txt             # Dependencias Python
│
├── 📂 config/                      # Configuraciones
│   └── simulation_config.yaml     # Parámetros de simulación
│
├── 📂 src/                        # Código fuente
│   ├── __init__.py
│   ├── main.py                    # Script principal (por crear)
│   │
│   ├── 📂 agents/                 # Agentes del modelo
│   │   ├── __init__.py
│   │   ├── human_agent.py         # Agente humano SEIR (por crear)
│   │   └── mosquito_agent.py      # Agente mosquito SI (por crear)
│   │
│   ├── 📂 model/                  # Modelo principal
│   │   ├── __init__.py
│   │   └── dengue_model.py        # Modelo Mesa (por crear)
│   │
│   ├── 📂 strategies/             # Estrategias de control
│   │   ├── __init__.py
│   │   ├── lsm.py                 # Gestión larvaria (por crear)
│   │   └── itn_irs.py             # Mosquiteros/insecticidas (por crear)
│   │
│   └── 📂 utils/                  # Utilidades
│       ├── __init__.py
│       ├── climate_data.py        # API Meteostat (por crear)
│       ├── epidemiology_data.py   # Datos dengue (por crear)
│       ├── visualization.py       # Gráficas (por crear)
│       └── config_loader.py       # Cargar YAML (por crear)
│
├── 📂 data/                       # Datos
│   ├── 📂 raw/                    # Datos sin procesar
│   │   └── .gitkeep
│   └── 📂 processed/              # Datos procesados
│       └── .gitkeep
│
├── 📂 results/                    # Resultados
│   ├── .gitkeep
│   └── 📂 plots/                  # Gráficas generadas
│       └── .gitkeep
│
├── 📂 notebooks/                  # Jupyter notebooks
│   └── (por crear análisis)
│
├── 📂 tests/                      # Tests unitarios
│   └── (por crear tests)
│
├── 📂 docs/                       # Documentación adicional
│   └── (por crear docs técnicas)
│
└── 📂 r_analysis/                 # Análisis en R
    └── (por crear scripts R)
```

## 🎯 Componentes Principales

### 1. **Agentes** (`src/agents/`)

#### HumanAgent
- **Estados:** S → E → I → R (SEIR)
- **Atributos:** edad, hogar, trabajo, estado de enfermedad
- **Comportamiento:** movilidad diaria (hogar-trabajo-parque)
- **Interacción:** puede ser picado por mosquitos infectados

#### MosquitoAgent
- **Estados:** S → I (Susceptible/Infectado)
- **Atributos:** edad, sitio de reproducción, expectativa de vida
- **Comportamiento:** búsqueda de humanos, reproducción
- **Dependencias:** temperatura y precipitación

### 2. **Modelo Principal** (`src/model/dengue_model.py`)

```
DengueModel (mesa.Model)
├── Grid (50x50 celdas)
├── Scheduler (orden aleatorio)
├── Climate (temperatura, lluvia)
├── Estrategias de control
└── DataCollector (métricas)
```

**Flujo de simulación diaria:**
1. Actualizar clima
2. Mover agentes humanos
3. Mosquitos buscan humanos
4. Transmisión (picaduras)
5. Actualizar estados SEIR/SI
6. Reproducción de mosquitos
7. Aplicar estrategias de control
8. Recolectar datos

### 3. **Estrategias de Control** (`src/strategies/`)

#### LSM (Larval Source Management)
- Reduce población de mosquitos (criaderos)
- Cobertura: 70%
- Efectividad: 80%
- Frecuencia: cada 7 días

#### ITN/IRS (Mosquiteros/Insecticidas)
- Reduce probabilidad de picadura
- Cobertura: 60% hogares
- Reducción picaduras: 70%
- Duración: 90 días

### 4. **Datos** (`src/utils/`)

| Fuente | API/Dataset | Datos |
|--------|------------|-------|
| Clima | Meteostat | Temperatura, precipitación diaria |
| Epidemiología | Datos Abiertos Colombia | Casos de dengue en Bucaramanga |
| Demografía | Proyecciones oficiales | Población urbana por sector |

## 🔬 Parámetros Clave

### Transmisión
- **H→M (Humano a Mosquito):** 50%
- **M→H (Mosquito a Humano):** 50%
- **Tasa de picadura:** 0.5/día
- **Radio de contacto:** 1 celda

### Enfermedad Humana (SEIR)
- **Incubación (E→I):** 5.5 días
- **Infeccioso (I→R):** 7.0 días
- **Mortalidad:** 0.1%

### Mosquito
- **Vida promedio:** 14 días
- **Incubación vectorial:** 10 días
- **Huevos por hembra:** 100
- **Desarrollo huevo→adulto:** 10 días

### Clima (Bucaramanga)
- **Temperatura óptima:** 28°C
- **Temperatura mínima:** 15°C
- **Temperatura máxima:** 35°C
- **Lluvia mínima para criaderos:** 5mm

## 📊 Métricas de Evaluación

1. **Infectados totales:** Suma de humanos infectados durante el brote
2. **Pico de infección:** Máximo número de infectados simultáneos
3. **Duración del brote:** Días hasta eliminación del virus
4. **Población vectorial:** Evolución de mosquitos adultos
5. **Efectividad de control:** Reducción % respecto a baseline

## 🗓️ Plan de Desarrollo (8-9 Semanas)

| Fase | Semana | Tareas Principales |
|------|--------|-------------------|
| **1. Configuración** | 1 | ✅ Estructura, entorno, Git |
| **2. Agentes** | 2-3 | Implementar HumanAgent y MosquitoAgent |
| **3. Modelo** | 3-4 | Implementar DengueModel (Mesa) |
| **4. Control** | 4 | Implementar LSM e ITN/IRS |
| **5. Datos** | 5 | APIs clima, datos dengue, visualización |
| **6. Ejecución** | 5 | Script main.py y ejecución |
| **7. Calibración** | 6 | Ajustar parámetros con datos reales |
| **8. Experimentos** | 7 | Comparar estrategias (n=30 réplicas) |
| **9. Análisis R** | 8 | Análisis estadístico comparativo |
| **10. Documentación** | 8-9 | Docs, presentación, entrega |

## 🚀 Próximos Pasos Inmediatos

### Paso 1: Configurar Entorno
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 2: Implementar Primer Agente
Edita `src/agents/human_agent.py` siguiendo la guía

### Paso 3: Crear Test
Edita `tests/test_human_agent.py` y ejecuta:
```bash
pytest tests/ -v
```

### Paso 4: Implementar Modelo Básico
Edita `src/model/dengue_model.py`

### Paso 5: Script Principal
Edita `src/main.py` para ejecutar simulación

## 📚 Archivos de Referencia

| Documento | Descripción |
|-----------|-------------|
| `README.md` | Visión general del proyecto |
| `GUIA_DESARROLLO.md` | **Guía detallada con 10 fases** |
| `INICIO_RAPIDO.md` | Comandos y tips útiles |
| `config/simulation_config.yaml` | Todos los parámetros configurables |
| `.copilot-context.json` | Contexto completo del proyecto |

## 🎓 Objetivos Académicos

### Objetivo General
Construir un modelo ABM que ilustre la propagación del dengue en Bucaramanga, identificando patrones y evaluando estrategias de control.

### Objetivos Específicos
1. ✅ Representar interacción humanos-mosquitos
2. ✅ Analizar impacto de movilidad humana
3. ✅ Evaluar estrategias LSM vs ITN/IRS
4. ✅ Calibrar con datos reales de Bucaramanga

## 💻 Tecnologías

- **Python 3.10+**
- **Mesa** (framework ABM)
- **NumPy, Pandas** (procesamiento)
- **Matplotlib, Seaborn** (visualización)
- **Meteostat** (datos climáticos)
- **R** (análisis estadístico)
- **Jupyter** (notebooks interactivos)

## ✅ Estado Actual

- ✅ Estructura de carpetas creada
- ✅ Archivos de configuración creados
- ✅ Documentación base establecida
- ✅ Requirements definidos
- ⬜ Agentes por implementar
- ⬜ Modelo por implementar
- ⬜ Estrategias por implementar
- ⬜ Utilidades por implementar

## 📞 Información del Equipo

**Universidad Industrial de Santander**  
**Asignatura:** Simulación Digital F1

**Equipo:**
- Yeison Adrián Cáceres Torres
- William Urrutia Torres
- Jhon Anderson Vargas Gómez

---

**📖 Lee `GUIA_DESARROLLO.md` para comenzar la implementación paso a paso!**

**🚀 Usa `INICIO_RAPIDO.md` para comandos y tips prácticos!**
