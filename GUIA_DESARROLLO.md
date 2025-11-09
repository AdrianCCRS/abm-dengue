# Guía de Desarrollo Paso a Paso
## ABM-Dengue-Bucaramanga

Esta guía proporciona un plan detallado para implementar el modelo de simulación basado en agentes para el dengue en Bucaramanga.

---

## Fase 1: Configuración del Entorno (Semana 1)

### Paso 1.1: Preparación del Entorno
```bash
# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python -c "import mesa; print(mesa.__version__)"
```

### Paso 1.2: Estructura de Archivos Base
- [x] Crear estructura de carpetas
- [ ] Crear archivos `__init__.py` en cada módulo
- [ ] Configurar `.gitignore`
- [ ] Inicializar repositorio git

### Paso 1.3: Configuración Inicial
- [ ] Revisar y ajustar `config/simulation_config.yaml`
- [ ] Documentar parámetros en `docs/parametros.md`

---

## Fase 2: Implementación de Agentes (Semana 2-3)

### Paso 2.1: Agente Humano (`src/agents/human_agent.py`)

**Componentes a implementar:**

```python
class HumanAgent(mesa.Agent):
    """
    Agente humano con estados SEIR y movilidad.
    
    Estados:
    - S: Susceptible
    - E: Expuesto (infectado pero no contagioso)
    - I: Infectado (contagioso)
    - R: Recuperado (inmune)
    
    Atributos:
    - age: edad del individuo
    - home_pos: posición del hogar
    - work_pos: posición del trabajo
    - current_pos: posición actual
    - disease_state: estado SEIR actual
    - days_in_state: días en el estado actual
    - protected: si usa ITN/IRS
    """
```

**Tareas:**
- [ ] Implementar inicialización del agente
- [ ] Implementar método `move()` para movilidad diaria
- [ ] Implementar método `update_disease_state()` para transiciones SEIR
- [ ] Implementar método `get_exposed()` para infección
- [ ] Implementar patrones de movilidad (hogar-trabajo-parque)
- [ ] Agregar docstrings en formato NumPy
- [ ] Crear tests unitarios en `tests/test_human_agent.py`

### Paso 2.2: Agente Mosquito (`src/agents/mosquito_agent.py`)

**Componentes a implementar:**

```python
class MosquitoAgent(mesa.Agent):
    """
    Agente mosquito Aedes aegypti con estados S/I.
    
    Estados:
    - S: Susceptible
    - I: Infectado
    
    Atributos:
    - age: edad en días
    - breeding_site: sitio de reproducción
    - disease_state: S o I
    - days_infected: días infectado
    - lifespan: expectativa de vida
    """
```

**Tareas:**
- [ ] Implementar inicialización del agente
- [ ] Implementar método `seek_human()` para búsqueda de hospederos
- [ ] Implementar método `bite()` para transmisión
- [ ] Implementar método `age_and_die()` para ciclo de vida
- [ ] Implementar método `can_reproduce()` basado en clima
- [ ] Agregar docstrings en formato NumPy
- [ ] Crear tests unitarios en `tests/test_mosquito_agent.py`

---

## Fase 3: Modelo Principal (Semana 3-4)

### Paso 3.1: Modelo Mesa (`src/model/dengue_model.py`)

**Componentes a implementar:**

```python
class DengueModel(mesa.Model):
    """
    Modelo principal de simulación ABM para dengue.
    
    Gestiona:
    - Creación y actualización de agentes
    - Espacio (grid)
    - Scheduler
    - Recolección de datos
    - Condiciones climáticas
    - Estrategias de control
    """
```

**Tareas:**
- [ ] Implementar `__init__()` con parámetros de configuración
- [ ] Crear grid y scheduler
- [ ] Implementar método `create_humans()`
- [ ] Implementar método `create_mosquitoes()`
- [ ] Implementar método `step()` para cada día de simulación
- [ ] Implementar método `update_climate()` para condiciones diarias
- [ ] Implementar método `apply_control_strategies()`
- [ ] Implementar método `mosquito_breeding()` dependiente de clima
- [ ] Configurar DataCollector para métricas
- [ ] Agregar docstrings en formato NumPy

### Paso 3.2: Scheduler y Grid
- [ ] Configurar `mesa.time.RandomActivation` para orden aleatorio
- [ ] Configurar `mesa.space.MultiGrid` para espacio compartido
- [ ] Implementar métodos de vecindad para contactos

---

## Fase 4: Estrategias de Control (Semana 4)

### Paso 4.1: LSM (`src/strategies/lsm.py`)

```python
class LSMStrategy:
    """
    Gestión de Fuentes Larvarias (Larval Source Management).
    
    Reduce la reproducción de mosquitos mediante:
    - Eliminación de criaderos
    - Tratamiento larvicida
    """
```

**Tareas:**
- [ ] Implementar `apply(model)` para reducir población de huevos/larvas
- [ ] Modelar cobertura espacial
- [ ] Modelar efectividad temporal
- [ ] Agregar tests en `tests/test_lsm.py`

### Paso 4.2: ITN/IRS (`src/strategies/itn_irs.py`)

```python
class ITNIRSStrategy:
    """
    Mosquiteros tratados e Insecticidas Residuales.
    
    Protege individuos mediante:
    - Reducción de probabilidad de picadura
    - Reducción de transmisión
    """
```

**Tareas:**
- [ ] Implementar `apply(model)` para proteger agentes humanos
- [ ] Modelar cobertura de hogares
- [ ] Modelar degradación temporal del efecto
- [ ] Agregar tests en `tests/test_itn_irs.py`

---

## Fase 5: Utilidades y Datos (Semana 5)

### Paso 5.1: Módulo de Clima (`src/utils/climate_data.py`)

**Tareas:**
- [x] Implementar cargador de datos climáticos desde CSV
- [ ] Implementar método `get_temperature(date)` para Bucaramanga
- [ ] Implementar método `get_precipitation(date)`
- [ ] Implementar cache local de datos climáticos
- [ ] Manejar errores de API (fallback a valores por defecto)
- [ ] Guardar datos en `data/raw/climate_bucaramanga.csv`

### Paso 5.2: Módulo de Casos de Dengue (`src/utils/epidemiology_data.py`)

**Tareas:**
- [ ] Implementar descarga de datos abiertos de Colombia
- [ ] Filtrar casos de Bucaramanga
- [ ] Procesar fechas y geocodificación básica
- [ ] Guardar en `data/processed/dengue_cases_bucaramanga.csv`
- [ ] Crear función para estadísticas descriptivas

### Paso 5.3: Módulo de Visualización (`src/utils/visualization.py`)

**Tareas:**
- [ ] Implementar gráfica de serie temporal (infectados, susceptibles, etc.)
- [ ] Implementar gráfica de población vectorial
- [ ] Implementar mapa de calor espacial de infecciones
- [ ] Implementar comparación de estrategias
- [ ] Guardar gráficas en `results/plots/`

### Paso 5.4: Módulo de Configuración (`src/utils/config_loader.py`)

**Tareas:**
- [ ] Implementar carga de `simulation_config.yaml`
- [ ] Validar parámetros obligatorios
- [ ] Proveer valores por defecto

---

## Fase 6: Ejecución Principal (Semana 5)

### Paso 6.1: Script Principal (`src/main.py`)

```python
"""
Script principal para ejecutar la simulación ABM-Dengue.

Uso:
    python src/main.py
    python src/main.py --config config/mi_config.yaml
    python src/main.py --visualize
"""
```

**Tareas:**
- [ ] Implementar parsing de argumentos CLI
- [ ] Cargar configuración
- [ ] Inicializar clima (API o fallback)
- [ ] Crear y ejecutar modelo
- [ ] Guardar resultados en CSV
- [ ] Generar gráficas
- [ ] Agregar barra de progreso (tqdm)

---

## Fase 7: Calibración y Validación (Semana 6)

### Paso 7.1: Notebook de Calibración (`notebooks/01_calibracion_parametros.ipynb`)

**Tareas:**
- [ ] Comparar resultados de simulación con datos reales de dengue
- [ ] Ajustar parámetros de transmisión (probabilidades H→M, M→H)
- [ ] Ajustar parámetros de reproducción vectorial
- [ ] Validar estacionalidad con clima real
- [ ] Documentar parámetros óptimos

### Paso 7.2: Análisis de Sensibilidad (`notebooks/02_analisis_sensibilidad.ipynb`)

**Tareas:**
- [ ] Variar parámetros clave (±20%, ±50%)
- [ ] Analizar impacto en resultados
- [ ] Identificar parámetros más influyentes
- [ ] Documentar rangos de confianza

---

## Fase 8: Experimentación y Comparación (Semana 7)

### Paso 8.1: Escenarios de Control

**Tareas:**
- [ ] Ejecutar simulación sin control (baseline)
- [ ] Ejecutar simulación con LSM
- [ ] Ejecutar simulación con ITN/IRS
- [ ] Ejecutar simulación con LSM + ITN/IRS
- [ ] Ejecutar múltiples réplicas (n=30) con diferentes seeds

### Paso 8.2: Análisis Comparativo (`notebooks/03_comparacion_estrategias.ipynb`)

**Tareas:**
- [ ] Comparar número total de infectados
- [ ] Comparar duración del brote
- [ ] Comparar población vectorial
- [ ] Análisis estadístico (t-test, ANOVA)
- [ ] Generar gráficas comparativas

---

## Fase 9: Análisis en R (Semana 8)

### Paso 9.1: Scripts R (`r_analysis/analisis_comparativo.R`)

**Tareas:**
- [ ] Cargar resultados de simulación
- [ ] Cargar datos reales de dengue y clima
- [ ] Análisis de correlación clima-casos
- [ ] Modelos estadísticos (GLM, GAM)
- [ ] Visualizaciones con ggplot2
- [ ] Informe en RMarkdown

---

## Fase 10: Documentación y Entrega (Semana 8-9)

### Paso 10.1: Documentación Técnica

**Tareas:**
- [ ] Completar docstrings en todos los módulos
- [ ] Crear `docs/arquitectura.md` con diagramas UML
- [ ] Crear `docs/parametros.md` con tabla de parámetros
- [ ] Crear `docs/resultados.md` con hallazgos principales
- [ ] Actualizar README.md con instrucciones de uso

### Paso 10.2: Tests y Calidad de Código

**Tareas:**
- [ ] Alcanzar >80% cobertura de tests
- [ ] Ejecutar `black` para formato de código
- [ ] Ejecutar `flake8` para linting
- [ ] Revisar y corregir warnings

### Paso 10.3: Docker (Opcional)

**Tareas:**
- [ ] Crear `Dockerfile`
- [ ] Crear `docker-compose.yml`
- [ ] Documentar uso con Docker

### Paso 10.4: Presentación Final

**Tareas:**
- [ ] Preparar slides con resultados
- [ ] Incluir gráficas comparativas
- [ ] Discusión de limitaciones
- [ ] Conclusiones y trabajo futuro

---

## Checklist de Verificación Pre-Entrega

- [ ] Código ejecuta sin errores
- [ ] Todos los tests pasan
- [ ] Resultados reproducibles (seed fijo)
- [ ] Gráficas generadas en `results/plots/`
- [ ] README.md actualizado
- [ ] Documentación completa
- [ ] Código formateado (black)
- [ ] Sin warnings de flake8
- [ ] Git commits con mensajes descriptivos
- [ ] `.gitignore` configurado correctamente

---

## Recursos Adicionales

### Referencias Bibliográficas
- Jindal et al. (2017) - Modelo ABM para dengue (referencia base)
- Documentación oficial de Mesa: https://mesa.readthedocs.io/
- Datos Abiertos Colombia: https://www.datos.gov.co/

### Contacto y Soporte
- Dudas sobre implementación: discutir en equipo
- Issues técnicas: documentar en GitHub Issues
- Reuniones semanales: revisar progreso

---

## Notas Importantes

1. **Modularidad**: Mantener código modular y reutilizable
2. **Documentación**: Docstrings en formato NumPy en cada función/clase
3. **Control de versiones**: Commits frecuentes con mensajes claros
4. **Testing**: Escribir tests para funciones críticas
5. **Reproducibilidad**: Usar seeds fijos para experimentos finales
6. **Validación**: Comparar constantemente con datos reales

---

**Última actualización:** Octubre 26, 2025
**Versión:** 1.0
