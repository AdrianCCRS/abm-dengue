# ABM-Dengue-Bucaramanga

Simulación basada en agentes (ABM) para modelar la propagación del dengue en Bucaramanga, inspirada en Jindal et al. (2017).

## Autores
- Yeison Adrián Cáceres Torres
- William Urrutia Torres
- Jhon Anderson Vargas Gómez

**Asignatura:** Simulación Digital F1 — Universidad Industrial de Santander

## Descripción

Este proyecto implementa un modelo de simulación basado en agentes para estudiar la propagación del dengue en Bucaramanga, Colombia. El modelo incluye:

- Agentes humanos con estados SEIR (Susceptible, Expuesto, Infectado, Recuperado)
- Agentes mosquitos (Aedes aegypti) con estados S/I
- Condiciones climáticas reales (temperatura y precipitación)
- Estrategias de control: LSM (Gestión de fuentes larvarias) e ITN/IRS (Protección individual)

## Estructura del Proyecto

```
amb-dengue/
├── src/                    # Código fuente principal
│   ├── agents/            # Definición de agentes (humanos y mosquitos)
│   ├── model/             # Modelo principal de simulación Mesa
│   ├── strategies/        # Estrategias de control (LSM, ITN/IRS)
│   └── utils/             # Utilidades (clima, datos, visualización)
├── data/                  # Datos de entrada
│   ├── raw/              # Datos sin procesar (clima, casos dengue)
│   └── processed/        # Datos procesados
├── results/              # Resultados de simulaciones
│   └── plots/           # Gráficas generadas
├── notebooks/            # Jupyter notebooks para análisis
├── tests/               # Tests unitarios
├── config/              # Archivos de configuración
├── r_analysis/          # Scripts R para análisis estadístico
└── docs/                # Documentación adicional
```

## Requisitos

- Python 3.10+
- Librerías: mesa, numpy, pandas, matplotlib, seaborn, requests
- R (opcional, para análisis estadístico adicional)

## Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Ejecutar simulación básica
python src/main.py

# Ejecutar con configuración específica
python src/main.py --config config/simulation_config.yaml

# Ver visualización en vivo
python src/main.py --visualize
```

## Objetivos

### General
Construir un modelo de simulación basado en agentes que ilustre la propagación del dengue en Bucaramanga, identificando patrones de difusión y evaluando cómo diversas estrategias de control influyen sobre la tasa de transmisión, población vectorial y duración del brote.

### Específicos
1. Representar la interacción entre agentes humanos y mosquitos Aedes aegypti
2. Analizar cómo la movilidad humana afecta la propagación espacial
3. Evaluar el impacto de estrategias de control centralizadas (LSM) y descentralizadas (ITN/IRS)
4. Calibrar parámetros con datos reales de Bucaramanga

## Métricas de Evaluación

- Número total de personas infectadas
- Evolución de la población vectorial
- Tiempo de eliminación del brote
- Comparación entre estrategias de control

## Fuentes de Datos

- **Clima:** API Meteostat (temperatura y precipitación)
- **Epidemiología:** Datos Abiertos Colombia – Casos de dengue
- **Demografía:** Proyecciones oficiales de población urbana

## Licencia

Este proyecto es desarrollado con fines académicos para la Universidad Industrial de Santander.
