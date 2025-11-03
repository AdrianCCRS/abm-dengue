# Inicio Rápido - ABM-Dengue-Bucaramanga

## 🚀 Configuración Inicial

### 1. Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Verificar Instalación

```bash
python -c "import mesa; import numpy; import pandas; print('✓ Dependencias instaladas correctamente')"
```

## 📋 Orden de Desarrollo Recomendado

Sigue este orden para implementar el proyecto de manera incremental y probarlo en cada paso:

### **Semana 1-2: Fundamentos**
1. ✅ Estructura de carpetas creada
2. ⬜ Implementar `src/utils/config_loader.py` (cargar YAML)
3. ⬜ Implementar `src/agents/human_agent.py` (clase básica)
4. ⬜ Implementar `src/agents/mosquito_agent.py` (clase básica)
5. ⬜ Escribir tests unitarios para agentes

### **Semana 3: Modelo Base**
6. ⬜ Implementar `src/model/dengue_model.py` (versión mínima)
7. ⬜ Crear script `src/main.py` para ejecutar simulación básica
8. ⬜ Probar simulación sin clima ni control

### **Semana 4: Datos Reales**
9. ⬜ Implementar `src/utils/climate_data.py` (API Meteostat)
10. ⬜ Implementar `src/utils/epidemiology_data.py` (datos abiertos)
11. ⬜ Integrar clima al modelo
12. ⬜ Crear notebook `notebooks/01_exploracion_datos.ipynb`

### **Semana 5: Control**
13. ⬜ Implementar `src/strategies/lsm.py`
14. ⬜ Implementar `src/strategies/itn_irs.py`
15. ⬜ Integrar estrategias al modelo
16. ⬜ Probar cada estrategia individualmente

### **Semana 6: Visualización**
17. ⬜ Implementar `src/utils/visualization.py`
18. ⬜ Generar gráficas básicas
19. ⬜ Crear notebook `notebooks/02_visualizacion_resultados.ipynb`

### **Semana 7: Calibración**
20. ⬜ Comparar con datos reales en notebook
21. ⬜ Ajustar parámetros
22. ⬜ Análisis de sensibilidad

### **Semana 8: Experimentación**
23. ⬜ Ejecutar experimentos comparativos
24. ⬜ Análisis estadístico en R
25. ⬜ Documentación final

## 🔧 Comandos Útiles

### Ejecutar Simulación

```bash
# Simulación básica
python src/main.py

# Con configuración personalizada
python src/main.py --config config/mi_experimento.yaml

# Con visualización
python src/main.py --visualize
```

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/

# Con cobertura
pytest --cov=src tests/

# Test específico
pytest tests/test_human_agent.py
```

### Formateo de Código

```bash
# Formatear con black
black src/

# Verificar estilo con flake8
flake8 src/
```

### Jupyter Notebooks

```bash
# Iniciar Jupyter
jupyter notebook

# O Jupyter Lab
jupyter lab
```

## 📊 Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `config/simulation_config.yaml` | Parámetros de simulación |
| `src/main.py` | Script principal |
| `src/model/dengue_model.py` | Modelo Mesa |
| `src/agents/human_agent.py` | Agente humano SEIR |
| `src/agents/mosquito_agent.py` | Agente mosquito |
| `GUIA_DESARROLLO.md` | Guía detallada paso a paso |

## 🎯 Primeros Pasos Prácticos

### 1. Implementar Agente Humano Básico

Crea `src/agents/human_agent.py`:

```python
import mesa

class HumanAgent(mesa.Agent):
    """Agente humano con estados SEIR."""
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = "S"  # Susceptible
        self.age = self.random.randint(0, 80)
        self.home_pos = None
        
    def step(self):
        """Ejecutar un paso de simulación."""
        # TODO: implementar lógica
        pass
```

### 2. Probar el Agente

Crea `tests/test_human_agent.py`:

```python
from src.agents.human_agent import HumanAgent
import mesa

def test_human_agent_creation():
    model = mesa.Model()
    agent = HumanAgent(1, model)
    assert agent.state == "S"
    assert 0 <= agent.age <= 80
```

### 3. Ejecutar Test

```bash
pytest tests/test_human_agent.py -v
```

## 📚 Recursos

- **Mesa Documentation:** https://mesa.readthedocs.io/
- **NumPy Docstring Guide:** https://numpydoc.readthedocs.io/
- **Meteostat API:** https://dev.meteostat.net/
- **Jindal et al. (2017):** Referencia principal del modelo

## 💡 Tips

1. **Desarrollo Incremental:** Implementa, prueba, documenta. Repite.
2. **Git Commits Frecuentes:** Commit después de cada funcionalidad
3. **Tests Primero:** Escribe tests antes de implementar (TDD opcional)
4. **Documentación Continua:** Docstrings en cada función/clase
5. **Validación Constante:** Compara resultados con datos reales

## 🆘 Solución de Problemas

### Error: "No module named 'mesa'"
```bash
# Verifica que el entorno virtual está activado
which python
# Reinstala dependencias
pip install -r requirements.txt
```

### Error: API Meteostat no responde
- Verifica conexión a internet
- El modelo usa valores por defecto si falla la API
- Revisa logs en consola

### Simulación muy lenta
- Reduce `num_humans` o `num_mosquitoes` en config
- Reduce `simulation_days`
- Desactiva visualización en vivo

## 📞 Contacto

**Equipo de Desarrollo:**
- Yeison Adrián Cáceres Torres
- William Urrutia Torres  
- Jhon Anderson Vargas Gómez

**Universidad Industrial de Santander**  
Simulación Digital F1

---

**¡Comienza con la Fase 1 de la GUIA_DESARROLLO.md!** 🚀
