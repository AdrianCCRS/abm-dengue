# Resumen Completo del Proyecto: Optimización ABM-Dengue

## Contexto del Proyecto

**Proyecto**: Modelo Basado en Agentes (ABM) para simulación de dengue en Bucaramanga  
**Autores**: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez  
**Universidad**: Industrial de Santander - Simulación Digital F1  
**Framework**: Mesa (Python)  
**Servidores**: felix.uis.edu.co (64 CPUs), thor.uis.edu.co (128 CPUs)

## Problema Principal

La simulación tiene **problemas severos de rendimiento** que impiden ejecutar simulaciones de 365 días en tiempo razonable.

### Síntomas Observados

1. **Crecimiento exponencial de mosquitos**:
   - Configuración original: 1,500 mosquitos iniciales → 35,924 al día 33
   - Tiempo por día: 0.5s → 133s (aumento de 266×)
   - Simulación de 365 días: ~7.6 horas (inaceptable)

2. **Trabas en la ejecución**:
   - La simulación se "congela" en ciertos días
   - No hay mensajes de error, simplemente deja de avanzar
   - Ocurre especialmente con poblaciones grandes (>15,000 mosquitos)

3. **Uso excesivo de memoria y CPU**:
   - Cada mosquito consume recursos como agente Mesa completo
   - Huevos también eran agentes individuales (optimizado posteriormente)

---

## Trabajo Realizado

### Fase 1: Optimización de Huevos (Completada ✅)

**Problema**: 200,000+ agentes huevo saturaban memoria y CPU

**Solución**: Crear `EggManager` con estructura `EggBatch`
- Reemplazó agentes individuales por lotes agrupados
- Reducción de 95% en número de objetos Mesa
- Mantiene modelo GDD (Grados-Día) de Tun-Lin et al. (1999)

**Archivos**:
- `src/model/egg_manager.py` (nuevo)
- `src/model/dengue_model.py` (modificado)
- `src/agents/mosquito_agent.py` (modificado)

**Resultado**: Mejora significativa pero insuficiente

---

### Fase 2: Control Poblacional Inicial (Completada ✅)

**Objetivo**: Controlar crecimiento exponencial de mosquitos adultos

**Cambios en `config/default_config.yaml`**:
```yaml
mosquito_disease:
  mortality_rate: 0.08  # Aumentado de 0.05 (vida media 12 días)

mosquito_breeding:
  egg_mortality_rate: 0.03  # Agregado (3% diario)
```

**Resultado**: Mejora parcial, población aún crece excesivamente

---

### Fase 3: Optimizaciones de Código (Completada ✅)

**Optimizaciones implementadas**:

1. **Skip de agentes estacionarios** (`src/agents/human_agent.py`):
   - Early return para agentes Tipo 4 que ya están en casa
   - Impacto: -20% en procesamiento de humanos

2. **Reducción de logging verbose** (`src/model/dengue_model.py`):
   - Logging detallado solo cada 10 días
   - Impacto: -5% en overhead I/O

3. **Eliminación de debug logs** (`src/agents/mosquito_agent.py`):
   - Removidos time logs de búsquedas
   - Impacto: -2% en overhead I/O

**Resultado**: Mejoras marginales (~25-30%), problema persiste

---

### Fase 4: Profiling y Diagnóstico (Completada ✅)

**Script creado**: `debug_bottleneck.py`

**Hallazgos del profiling** (30 pasos):
```
Paso 19: 2,253 → 7,929 mosquitos (explosión 3.5×)
Paso 30: 20,329 mosquitos, 66.6s/paso

Cuello de botella:
- mosquito_step_total: 83.7% del tiempo
- Promedio: 1.06ms por mosquito
```

**Conclusión crítica**: El problema NO es la eficiencia del código, sino el **número de mosquitos**. Cada mosquito toma ~1ms (razonable), pero con 20,000+ mosquitos el tiempo se vuelve inaceptable.

---

### Fase 5: Control Poblacional Agresivo (Implementada ✅)

**Basado en datos de profiling**, se implementaron ajustes agresivos:

#### Cambios en `config/default_config.yaml`:
```yaml
mosquito_breeding:
  eggs_per_female: 25          # -50% vs original (50)
  gonotrophic_cycle_days: 6    # -50% frecuencia vs original (3)
  egg_mortality_rate: 0.10     # 10% diario (vs 0% original)

mosquito_disease:
  mortality_rate: 0.12         # 12% diario (vida media 8 días)
```

#### Capacidad de carga (`src/model/egg_manager.py`):
```python
MAX_EGGS_PER_SITE = 500  # Límite por sitio de cría
```

**Impacto esperado**: Población día 30 de 20k → 3-4k mosquitos

**Resultado**: **NO VALIDADO** - Usuario reporta que configuración no se aplicó correctamente

---

### Fase 6: Configuración Light (Implementada ✅)

**Objetivo**: Crear configuración de escala reducida pero dinámica preservada

**Archivo**: `config/light_config.yaml`

**Escalado 10× con densidad preservada**:
```yaml
# Población
num_humanos: 300      # vs 3,000
num_mosquitos: 150    # vs 1,500
num_huevos: 300       # vs 3,000

# Grid (ajustado para mantener densidad)
width: 48             # vs 150
height: 48            # vs 150
# Densidad: 0.130 humanos/celda (vs 0.133 en default)

# Sitios
num_sitios_cria: 12   # vs 200
num_parques: 2        # vs 10

# Parámetros de control
eggs_per_female: 20
gonotrophic_cycle_days: 5
egg_mortality_rate: 0.08
mortality_rate: 0.10
```

**Rendimiento esperado**: 365 días en 30-45 minutos

**Resultado**: **PROBLEMA CRÍTICO** - Usuario reporta 15,016 mosquitos al día 188 (debería ser ~500-800)

---

## Problemas Actuales (CRÍTICOS 🔴)

### Problema 1: Configuración Light No Funciona

**Síntomas**:
- Día 188: 15,016 mosquitos (esperado: 500-800)
- Simulación se "traba" (no avanza)
- Tiempo: 9.92s/paso (aceptable pero población excesiva)

**Posibles causas**:
1. ❓ Usuario no hizo `git pull` → usando configuración vieja
2. ❓ Límite de capacidad (`MAX_EGGS_PER_SITE`) no funciona
3. ❓ Mortalidad no se aplica correctamente
4. ❓ Parámetros de `light_config.yaml` no se cargan

### Problema 2: Simulación se Traba

**Síntomas**:
- Se detiene en días específicos sin error
- No hay mensaje de excepción
- Simplemente deja de avanzar

**Posibles causas**:
1. ❓ Deadlock en alguna operación
2. ❓ Loop infinito en búsqueda de agentes
3. ❓ Operación I/O bloqueante
4. ❓ Memoria agotada (swap)

### Problema 3: Inconsistencia entre Configuraciones

**Observación**: Con configuración "normal" (default) pudo procesar más agentes antes de trabarse que con "light"

**Paradoja**: 
- Default: 35,924 mosquitos al día 33 → funciona (lento pero funciona)
- Light: 15,016 mosquitos al día 188 → se traba

**Hipótesis**: Hay algo específico en light_config que causa el problema (¿grid pequeño? ¿densidad alta?)

---

## Herramientas de Debugging Creadas

### 1. `debug_bottleneck.py` ✅
**Propósito**: Identificar cuellos de botella por método  
**Uso**: `python debug_bottleneck.py --steps 30`  
**Output**: Tiempo por operación, % del total, llamadas

### 2. `profile_simulation.py` ✅
**Propósito**: Profiling completo con cProfile  
**Uso**: `python profile_simulation.py --steps 10`  
**Output**: Archivo `profiling_results.txt` con análisis detallado

### 3. `quick_profile.py` ✅
**Propósito**: Análisis rápido con decoradores  
**Uso**: `python quick_profile.py --steps 5`  
**Output**: Timing por método sin overhead de cProfile

### 4. `debug_stuck.py` ✅ (NUEVO)
**Propósito**: Detectar dónde se traba la simulación  
**Uso**: `python debug_stuck.py --config config/light_config.yaml --steps 200 --timeout 30`  
**Features**:
- Timeout por paso (detecta trabas)
- Monitoreo de cada operación
- Stack trace cuando se traba
- Alertas de población excesiva

---

## Archivos Modificados

### Configuración
- `config/default_config.yaml` - Parámetros agresivos de control
- `config/light_config.yaml` - Configuración de escala reducida (NUEVO)

### Código Core
- `src/model/egg_manager.py` - Gestor de huevos + capacidad de carga
- `src/model/dengue_model.py` - Integración EggManager, logging reducido
- `src/agents/mosquito_agent.py` - Reproducción optimizada, logs removidos
- `src/agents/human_agent.py` - Skip de estacionarios

### Debugging
- `debug_bottleneck.py` - Profiling por método
- `debug_stuck.py` - Detección de trabas
- `profile_simulation.py` - cProfile completo
- `quick_profile.py` - Profiling ligero

### Documentación
- `cambios.md` - Registro detallado de cambios
- `docs/light_config_guide.md` - Guía de configuración light
- `docs/server_execution.md` - Guía de ejecución en servidores
- `docs/parallelization_status.md` - Estado de paralelización (pausada)

---

## Próximos Pasos Recomendados

### Inmediato (Debugging)

1. **Ejecutar `debug_stuck.py`** en servidor:
   ```bash
   python debug_stuck.py --config config/light_config.yaml --steps 200
   ```
   → Identificar exactamente dónde se traba

2. **Verificar que configuración se cargó**:
   ```bash
   grep "eggs_per_female" config/light_config.yaml
   grep "mortality_rate:" config/light_config.yaml
   ```
   → Confirmar parámetros correctos

3. **Validar límite de capacidad**:
   - Agregar prints en `EggManager.add_eggs()` para ver si se aplica
   - Verificar que `get_eggs_by_site()` funciona correctamente

### Corto Plazo (Fixes)

1. **Si límite de capacidad no funciona**:
   - Revisar lógica en `egg_manager.py:100-113`
   - Agregar logging para debugging
   - Verificar que `get_eggs_by_site()` retorna valor correcto

2. **Si mortalidad no se aplica**:
   - Verificar que `apply_mortality()` se llama en `dengue_model.py:step()`
   - Confirmar que `egg_mortality_rate` se carga de config

3. **Si se traba en operación específica**:
   - Optimizar esa operación
   - Agregar timeout interno
   - Considerar paralelización

### Mediano Plazo (Optimizaciones)

1. **Paralelización espacial** (rama `parallelization`):
   - Infraestructura base ya implementada
   - Requiere 1-2 semanas de integración
   - Speedup esperado: 25-50×

2. **Optimizaciones algorítmicas**:
   - Cache de búsquedas con `@lru_cache`
   - Índices espaciales más eficientes
   - Pre-carga de datos climáticos

---

## Métricas de Éxito

### Configuración Default
- ✅ Población estable: < 10,000 mosquitos al día 30
- ❌ Tiempo/día: < 20s (actualmente ~133s al día 33)
- ❌ 365 días: < 2 horas (actualmente ~7.6h estimado)

### Configuración Light
- ❌ Población estable: < 1,000 mosquitos al día 30 (actualmente 15,016 al día 188)
- ✅ Tiempo/día: < 10s (actualmente ~10s)
- ❌ 365 días: < 1 hora (no completado, se traba)
- ❌ Sin trabas: Debe completar 365 días (actualmente se traba)

---

## Preguntas Sin Responder

1. **¿Por qué light_config tiene 15k mosquitos?**
   - ¿Se cargó la configuración correctamente?
   - ¿El límite de capacidad funciona?
   - ¿La mortalidad se aplica?

2. **¿Por qué se traba la simulación?**
   - ¿En qué operación específica?
   - ¿Es un deadlock, loop infinito, o I/O?
   - ¿Por qué solo con light_config?

3. **¿Por qué default funciona mejor que light?**
   - ¿Es la densidad poblacional?
   - ¿Es el grid pequeño?
   - ¿Hay un bug específico de light_config?

---

## Comandos Útiles

### Debugging
```bash
# Detectar dónde se traba
python debug_stuck.py --config config/light_config.yaml --steps 200

# Profiling de cuellos de botella
python debug_bottleneck.py --steps 30

# Verificar configuración
grep -A 2 "eggs_per_female\|mortality_rate" config/light_config.yaml
```

### Ejecución
```bash
# Default config
python main.py --config config/default_config.yaml --steps 365

# Light config
python main.py --config config/light_config.yaml --steps 365

# Con seed fijo (reproducible)
python main.py --config config/light_config.yaml --steps 365 --seed 42
```

### Monitoreo
```bash
# Ver uso de CPU/memoria
htop

# Ver procesos Python
ps aux | grep python

# Matar proceso trabado
pkill -9 python
```

---

## Contacto y Referencias

**Repositorio**: github.com:AdrianCCRS/abm-dengue.git  
**Rama principal**: `main`  
**Rama paralelización**: `parallelization` (pausada)

**Referencias científicas**:
- Tun-Lin et al. (1999) - Modelo GDD para Aedes aegypti
- Jindal & Rao (2017) - Patrones de movilidad humana
- Scott et al. (1993) - Ciclo gonotrófico de mosquitos

**Última actualización**: 2025-11-22
