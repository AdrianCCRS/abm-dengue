# Análisis de Componentes Faltantes del Modelo ABM - Dengue

**Fecha**: 3 de Noviembre de 2025  
**Proyecto**: ABM-Dengue-Bucaramanga  
**Análisis**: Comparación entre implementación actual, especificación del paper y extensiones solicitadas

---

## 📊 Resumen Ejecutivo

### ✅ Componentes Implementados (Núcleo del Modelo Base)

| Componente | Estado | Cobertura |
|------------|--------|-----------|
| Agente Humano - Estados SEIR | ✅ Completo | 100% |
| Agente Humano - 4 Tipos de Movilidad | ✅ Completo | 100% |
| Agente Mosquito - Estados SI | ✅ Completo | 100% |
| Agente Mosquito - Ciclo de Vida (Huevo→Adulto) | ✅ Completo | 100% |
| Desarrollo Dependiente de Temperatura | ✅ Completo | 100% |
| Transmisión Bidireccional (α=0.6, β=0.275) | ✅ Completo | 100% |
| Grid Espacial 50×50 MultiGrid | ✅ Completo | 100% |
| Sistema de Configuración YAML | ✅ Completo | 100% |

### ⚠️ Componentes Parcialmente Implementados

| Componente | Estado | Completitud | Ubicación |
|------------|--------|-------------|-----------|
| Clima (Meteostat API) | ⚠️ Parcial | 30% | `DengueModel._obtener_clima_meteostat()` |
| Control Larvario (LSM) | ⚠️ Básico | 50% | `DengueModel._aplicar_lsm()` |
| ITN/IRS | ⚠️ Stub | 20% | `DengueModel._aplicar_itn_irs()` |
| Búsqueda de Parques | ⚠️ Stub | 0% | `HumanAgent._obtener_parque_cercano()` |
| Búsqueda Sitios de Cría | ⚠️ Básico | 40% | `MosquitoAgent._buscar_sitio_cria()` |

### ❌ Componentes No Implementados (Extensiones Solicitadas)

| Extensión | Prioridad | Impacto en Resultados |
|-----------|-----------|----------------------|
| **1. Variabilidad Individual en Parámetros Biológicos** | 🔴 ALTA | Alto - Realismo de distribuciones |
| **2. Probabilidad de Aislamiento en Infectados** | 🔴 ALTA | Alto - Dinámica de transmisión |
| **3. Renovación Estocástica de Criaderos** | 🟡 MEDIA | Medio - Dinámica vectorial |
| **4. Estructura Espacial Simple (Tipos de Celdas)** | 🔴 ALTA | Alto - Lógica espacial |
| **5. Eventos de Aglomeración** | 🟡 MEDIA | Medio - Picos epidémicos |

---

## 🔍 Análisis Detallado por Componente

### 1. ❌ EXTENSIÓN 1: Variabilidad Individual en Parámetros Biológicos

#### 📋 Descripción del Paper/Contexto
> "Cada mosquito y humano posee ligeras diferencias en sus parámetros biológicos para reflejar la heterogeneidad natural de la población."

#### ❌ Estado Actual
**NO IMPLEMENTADO** - Todos los agentes usan valores deterministas desde configuración:

```python
# mosquito_agent.py - Línea 46-49
self.tasa_mortalidad = getattr(model, 'mortalidad_mosquito', 0.05)  # ❌ FIJO
self.prob_apareamiento = getattr(model, 'prob_apareamiento_mosquito', 0.6)  # ❌ FIJO
```

```python
# human_agent.py - Línea 83-84
self.duracion_expuesto = getattr(model, 'incubacion_humano', 5)  # ❌ FIJO
self.duracion_infectado = getattr(model, 'infeccioso_humano', 6)  # ❌ FIJO
```

#### ✅ Implementación Requerida

**MosquitoAgent** - Agregar al `__init__`:
```python
# Variabilidad en mortalidad: Normal(μ=0.05, σ=0.01)
base_mortalidad = getattr(model, 'mortalidad_mosquito', 0.05)
sigma_mortalidad = getattr(model, 'sigma_mortalidad_mosquito', 0.01)
self.tasa_mortalidad = max(0.01, np.random.normal(base_mortalidad, sigma_mortalidad))

# Variabilidad en apareamiento: Uniform(0.15, 0.25)
min_apareamiento = getattr(model, 'min_prob_apareamiento', 0.15)
max_apareamiento = getattr(model, 'max_prob_apareamiento', 0.25)
self.prob_apareamiento = np.random.uniform(min_apareamiento, max_apareamiento)

# Ruido en desarrollo (τ y μ)
self.ruido_temperatura = np.random.normal(0, 0.5)  # ±0.5°C de variación individual
```

**HumanAgent** - Agregar al `__init__`:
```python
# Variabilidad en incubación: Uniform(2-6 días) según paper
min_incubacion = getattr(model, 'min_incubacion_humano', 2)
max_incubacion = getattr(model, 'max_incubacion_humano', 6)
self.duracion_expuesto = np.random.randint(min_incubacion, max_incubacion + 1)

# Variabilidad en periodo infeccioso: Uniform(4-7 días)
min_infeccioso = getattr(model, 'min_infeccioso_humano', 4)
max_infeccioso = getattr(model, 'max_infeccioso_humano', 7)
self.duracion_infectado = np.random.randint(min_infeccioso, max_infeccioso + 1)

# Prob. infección crónica individual (Pirc)
self.prob_infeccion_cronica = np.random.uniform(0.90, 1.0)  # Base 0.95 con variabilidad
```

**Configuración YAML** - Agregar sección:
```yaml
biological_variability:
  enabled: true
  mosquito:
    mortality_sigma: 0.01
    mating_min: 0.15
    mating_max: 0.25
    temperature_noise_sigma: 0.5
  human:
    incubation_min: 2
    incubation_max: 6
    infectious_min: 4
    infectious_max: 7
    chronic_min: 0.90
    chronic_max: 1.0
```

#### 🎯 Impacto Esperado
- **Realismo**: Curvas de incidencia más suaves (sin sincronización artificial)
- **Validación**: Distribuciones epidemiológicas más cercanas a datos reales
- **Métricas**: Intervalos de confianza en lugar de valores únicos

---

### 2. ❌ EXTENSIÓN 2: Probabilidad de Aislamiento en Humanos Infectados

#### 📋 Descripción del Paper/Contexto
> "Los infectados (estado I) permanecen en casa" - `human_agent.py` línea 198

Actualmente: **Aislamiento 100% determinista**

#### ❌ Estado Actual
```python
# human_agent.py - Línea 198-200
if self.estado == EstadoSalud.INFECTADO:
    self.mover_a(self.pos_hogar)  # ❌ SIEMPRE en casa
    return
```

**Atributos definidos pero NO usados**:
```python
# human_agent.py - Línea 67-68
self.prob_aislamiento = getattr(model, 'prob_aislamiento', 0.7)  # ⚠️ NO SE USA
self.en_aislamiento = False  # ⚠️ NO SE USA
```

#### ✅ Implementación Requerida

**HumanAgent.ejecutar_movilidad_diaria()** - Reemplazar líneas 198-200:
```python
if self.estado == EstadoSalud.INFECTADO:
    # Decidir aislamiento al momento de infectarse
    if not hasattr(self, '_aislamiento_decidido'):
        self.en_aislamiento = (self.random.random() < self.prob_aislamiento)
        self._aislamiento_decidido = True
    
    if self.en_aislamiento:
        # Aislamiento completo
        self.mover_a(self.pos_hogar)
        return
    else:
        # Movilidad reducida (solo hogar o celdas adyacentes)
        radio_mov = getattr(self.model, 'radio_mov_infectado', 1)
        vecindad = self.model.grid.get_neighborhood(
            self.pos_hogar,
            moore=True,
            include_center=True,
            radius=radio_mov
        )
        nueva_pos = self.random.choice(vecindad)
        self.mover_a(nueva_pos)
        return
```

**HumanAgent.actualizar_estado_seir()** - Resetear flag al recuperarse:
```python
elif self.estado == EstadoSalud.INFECTADO:
    if self.dias_en_estado >= self.duracion_infectado:
        self.estado = EstadoSalud.RECUPERADO
        self.dias_en_estado = 0
        self._aislamiento_decidido = False  # ✅ Resetear para futura reinfección
```

**Configuración YAML** - Agregar:
```yaml
human_behavior:
  isolation_probability: 0.7  # 70% se aíslan voluntariamente
  infected_mobility_radius: 1  # Celdas de radio si NO se aísla
  isolation_compliance_by_type:  # Opcional: diferenciado por tipo
    student: 0.8
    worker: 0.6
    mobile: 0.5
    stationary: 0.9
```

#### 🎯 Impacto Esperado
- **Transmisión**: Reducción 20-30% en R₀ efectivo con 70% aislamiento
- **Escenarios**: Simular políticas de cuarentena vs comportamiento libre
- **Realismo**: Captura heterogeneidad de cumplimiento social

---

### 3. ⚠️ EXTENSIÓN 3: Renovación Estocástica de Criaderos

#### 📋 Descripción del Contexto
> "Los criaderos aparecen y desaparecen aleatoriamente de acuerdo con la lluvia y el tiempo."

#### ⚠️ Estado Actual (Parcialmente Implementado)
```python
# dengue_model.py - Línea 155-159
def _generar_sitios_cria(self) -> List[Tuple[int, int]]:
    """Genera sitios ESTÁTICOS al inicio."""  # ❌ NO se renuevan
    # ...
    return sitios  # ⚠️ FIJOS durante toda la simulación
```

**Hay precipitación simulada pero NO afecta criaderos**:
```python
# dengue_model.py - Línea 239-245
self.precipitacion_actual = self._generar_precipitacion_sintetica()
# ❌ NO se usa para crear/eliminar criaderos dinámicamente
```

#### ✅ Implementación Requerida

**DengueModel** - Agregar atributos dinámicos:
```python
def __init__(self, ...):
    # ... código existente ...
    
    # Criaderos dinámicos
    self.sitios_cria_permanentes = self._generar_sitios_cria_permanentes()
    self.sitios_cria_temporales = {}  # {pos: dias_restantes}
```

**DengueModel._actualizar_clima()** - Agregar lógica de criaderos:
```python
def _actualizar_clima(self):
    # ... código existente de temperatura/precipitación ...
    
    # Actualizar criaderos dinámicos
    self._actualizar_criaderos_temporales()
```

**Nuevo método DengueModel._actualizar_criaderos_temporales()**:
```python
def _actualizar_criaderos_temporales(self):
    """
    Actualiza criaderos temporales según lluvia.
    
    Lógica:
    1. Si llueve (precipitacion > umbral): crear nuevos criaderos temporales
    2. Cada día: envejecer criaderos existentes
    3. Eliminar criaderos que superaron vida_util
    """
    # 1. Crear nuevos criaderos si llueve
    if self.precipitacion_actual > getattr(self, 'umbral_lluvia_criadero', 5.0):
        prob_nuevo = getattr(self, 'prob_renovacion_criadero', 0.2)
        
        if self.random.random() < prob_nuevo:
            # Número proporcional a intensidad de lluvia
            num_nuevos = int(self.precipitacion_actual / 10)  # 1 por cada 10mm
            
            for _ in range(num_nuevos):
                pos = (self.random.randrange(self.width),
                      self.random.randrange(self.height))
                
                vida_util = getattr(self, 'vida_util_criadero_temporal', 7)  # <7 días
                self.sitios_cria_temporales[pos] = vida_util
    
    # 2. Envejecer criaderos existentes
    eliminados = []
    for pos, dias_restantes in self.sitios_cria_temporales.items():
        self.sitios_cria_temporales[pos] -= 1
        if self.sitios_cria_temporales[pos] <= 0:
            eliminados.append(pos)
    
    # 3. Eliminar criaderos vencidos
    for pos in eliminados:
        del self.sitios_cria_temporales[pos]
        
        # Eliminar huevos en ese sitio
        huevos_sitio = [a for a in self.schedule.agents
                       if isinstance(a, MosquitoAgent) 
                       and a.etapa == EtapaVida.HUEVO
                       and a.sitio_cria == pos]
        for huevo in huevos_sitio:
            self.schedule.remove(huevo)
```

**Modificar MosquitoAgent._buscar_sitio_cria()**:
```python
def _buscar_sitio_cria(self) -> Optional[Tuple[int, int]]:
    """Busca sitios permanentes + temporales."""
    # Combinar ambos tipos
    sitios_disponibles = (
        self.model.sitios_cria_permanentes + 
        list(self.model.sitios_cria_temporales.keys())
    )
    
    if not sitios_disponibles:
        return None
    
    # Elegir el más cercano
    return min(sitios_disponibles, key=lambda s: self._distancia(s))
```

**Configuración YAML**:
```yaml
mosquito_breeding:
  # ... existentes ...
  dynamic_breeding_sites:
    enabled: true
    permanent_ratio: 0.05  # 5% celdas permanentes (lagos, tanques)
    rainfall_threshold: 5.0  # mm mínimos para crear charcos
    renewal_probability: 0.2  # prob. de crear charcos cuando llueve
    temporary_lifespan: 7  # días que duran charcos sin más lluvia
    puddles_per_10mm: 1  # 1 charco nuevo por cada 10mm de lluvia
```

#### 🎯 Impacto Esperado
- **Estacionalidad**: Picos de mosquitos correlacionados con época lluviosa
- **Realismo**: Población vectorial fluctuante (no estable)
- **Intervenciones**: LSM más crítico en época seca (pocos criaderos)

---

### 4. ❌ EXTENSIÓN 4: Estructura Espacial Simple (Tipos de Celdas)

#### 📋 Descripción del Contexto
> "El grid se compone de celdas categorizadas: urbana, parque, agua"

#### ❌ Estado Actual
```python
# dengue_model.py - Línea 88
self.grid = MultiGrid(width, height, torus=False)
# ❌ NO hay diferenciación de tipos de celdas
```

**Búsquedas de parques fallidas**:
```python
# human_agent.py - Línea 292-298
def _obtener_parque_cercano(self) -> Optional[Tuple[int, int]]:
    # TODO: Implementar búsqueda de celdas tipo "parque"
    return None  # ❌ NUNCA encuentra parques
```

#### ✅ Implementación Requerida

**Nueva clase `Celda` en `src/model/celda.py`**:
```python
from enum import Enum

class TipoCelda(Enum):
    """Tipos de celdas en el entorno."""
    URBANA = "urbana"       # Viviendas, oficinas, escuelas
    PARQUE = "parque"       # Áreas recreativas (alta exposición)
    AGUA = "agua"           # Criaderos permanentes (lagos, estanques)

class Celda:
    """
    Representa una celda del grid con propiedades espaciales.
    
    Attributes
    ----------
    tipo : TipoCelda
        Tipo de celda (urbana, parque, agua)
    pos : Tuple[int, int]
        Coordenadas (x, y)
    es_criadero : bool
        Si es sitio de cría activo
    densidad_humanos : int
        Número de humanos en la celda (actualizado dinámicamente)
    """
    
    def __init__(self, tipo: TipoCelda, pos: Tuple[int, int]):
        self.tipo = tipo
        self.pos = pos
        self.es_criadero = (tipo == TipoCelda.AGUA)
        self.densidad_humanos = 0
    
    def __repr__(self):
        return f"Celda({self.tipo.value}, {self.pos})"
```

**DengueModel** - Inicializar mapa de celdas:
```python
def __init__(self, ...):
    # ... código existente ...
    
    # Crear mapa de tipos de celdas
    self.mapa_celdas = self._inicializar_mapa_celdas()
```

**Nuevo método DengueModel._inicializar_mapa_celdas()**:
```python
def _inicializar_mapa_celdas(self) -> Dict[Tuple[int, int], Celda]:
    """
    Crea mapa de celdas con tipos asignados.
    
    Distribución desde configuración:
    - 5% agua (criaderos permanentes)
    - 10% parques
    - 85% urbana
    """
    from .celda import Celda, TipoCelda
    
    mapa = {}
    
    # Obtener proporciones desde config
    prop_agua = getattr(self, 'proporcion_celdas_agua', 0.05)
    prop_parques = getattr(self, 'proporcion_celdas_parques', 0.10)
    
    # Calcular cantidades
    total_celdas = self.width * self.height
    num_agua = int(total_celdas * prop_agua)
    num_parques = int(total_celdas * prop_parques)
    
    # Crear lista de todas las posiciones
    todas_pos = [(x, y) for x in range(self.width) for y in range(self.height)]
    self.random.shuffle(todas_pos)
    
    # Asignar agua
    for i in range(num_agua):
        pos = todas_pos[i]
        mapa[pos] = Celda(TipoCelda.AGUA, pos)
    
    # Asignar parques
    for i in range(num_agua, num_agua + num_parques):
        pos = todas_pos[i]
        mapa[pos] = Celda(TipoCelda.PARQUE, pos)
    
    # Resto: urbanas
    for i in range(num_agua + num_parques, total_celdas):
        pos = todas_pos[i]
        mapa[pos] = Celda(TipoCelda.URBANA, pos)
    
    return mapa
```

**HumanAgent._obtener_parque_cercano()** - Implementar búsqueda:
```python
def _obtener_parque_cercano(self) -> Optional[Tuple[int, int]]:
    """Busca el parque más cercano en el modelo."""
    from ..model.celda import TipoCelda
    
    # Filtrar celdas tipo parque
    parques = [pos for pos, celda in self.model.mapa_celdas.items() 
               if celda.tipo == TipoCelda.PARQUE]
    
    if not parques:
        return None
    
    # Retornar el más cercano a la posición actual
    return min(parques, key=lambda p: self._distancia_manhattan(p))

def _distancia_manhattan(self, pos: Tuple[int, int]) -> int:
    """Calcula distancia Manhattan."""
    x1, y1 = self.pos
    x2, y2 = pos
    return abs(x2 - x1) + abs(y2 - y1)
```

**MosquitoAgent._buscar_sitio_cria()** - Usar mapa de celdas:
```python
def _buscar_sitio_cria(self) -> Optional[Tuple[int, int]]:
    """Busca sitios tipo AGUA o temporales."""
    from ..model.celda import TipoCelda
    
    # Sitios permanentes (celdas tipo AGUA)
    sitios_agua = [pos for pos, celda in self.model.mapa_celdas.items()
                   if celda.tipo == TipoCelda.AGUA]
    
    # Sitios temporales (charcos post-lluvia)
    sitios_temp = list(self.model.sitios_cria_temporales.keys())
    
    # Combinar
    sitios_disponibles = sitios_agua + sitios_temp
    
    if not sitios_disponibles:
        return None
    
    # Elegir el más cercano dentro del rango de vuelo
    rango_max = getattr(self.model, 'rango_vuelo_max', 10)  # Fr = 10 celdas (~350m)
    sitios_alcanzables = [s for s in sitios_disponibles 
                          if self._distancia(s) <= rango_max]
    
    if not sitios_alcanzables:
        return None
    
    return min(sitios_alcanzables, key=lambda s: self._distancia(s))
```

**Configuración YAML**:
```yaml
environment:
  cell_types:
    water_ratio: 0.05       # 5% celdas tipo agua (criaderos permanentes)
    park_ratio: 0.10        # 10% parques (alta exposición)
    urban_ratio: 0.85       # 85% urbana (resto)
  
  mosquito_flight:
    max_range: 10           # Celdas máximas de vuelo (~350m si celda=35m)
```

#### 🎯 Impacto Esperado
- **Movilidad Humana**: ✅ Funcional (visitas a parques según tipo)
- **Reproducción Mosquitos**: ✅ Funcional (buscan agua real)
- **Análisis Espacial**: Mapas de calor por tipo de celda
- **Intervenciones**: Focalizar LSM en celdas tipo AGUA

---

### 5. ❌ EXTENSIÓN 5: Eventos de Aglomeración

#### 📋 Descripción del Contexto
> "Concentraciones humanas periódicas que pueden amplificar brotes (ferias, mercados)"

#### ❌ Estado Actual
**NO IMPLEMENTADO** - No hay mecanismo de eventos

#### ✅ Implementación Requerida

**DengueModel** - Agregar atributos de eventos:
```python
def __init__(self, ...):
    # ... código existente ...
    
    # Sistema de eventos
    self.evento_activo = False
    self.celda_evento = None
    self.dias_hasta_evento = getattr(self, 'intervalo_eventos', 7)
```

**DengueModel.step()** - Agregar lógica de eventos:
```python
def step(self):
    # ... código existente ...
    
    # Gestionar eventos de aglomeración
    self._gestionar_eventos()
    
    # ... resto del código ...
```

**Nuevo método DengueModel._gestionar_eventos()**:
```python
def _gestionar_eventos(self):
    """
    Gestiona eventos de aglomeración semanal.
    
    Lógica:
    - Cada 7 días: activar evento en parque aleatorio
    - Duración: 1 día
    - Atracción: 30% humanos no aislados visitan el evento
    """
    if self.evento_activo:
        # Desactivar evento después de 1 día
        self.evento_activo = False
        self.celda_evento = None
        return
    
    # Contar días hasta próximo evento
    self.dias_hasta_evento -= 1
    
    if self.dias_hasta_evento <= 0:
        # Activar nuevo evento
        self._activar_evento()
        
        # Resetear contador
        intervalo = getattr(self, 'intervalo_eventos', 7)
        self.dias_hasta_evento = intervalo

def _activar_evento(self):
    """Activa evento en parque aleatorio."""
    from .celda import TipoCelda
    
    # Buscar parques disponibles
    parques = [pos for pos, celda in self.mapa_celdas.items()
               if celda.tipo == TipoCelda.PARQUE]
    
    if not parques:
        return
    
    # Elegir parque aleatorio
    self.celda_evento = self.random.choice(parques)
    self.evento_activo = True
```

**HumanAgent.ejecutar_movilidad_diaria()** - Agregar lógica de eventos:
```python
def ejecutar_movilidad_diaria(self):
    """Movilidad con prioridad a eventos."""
    
    # Infectados
    if self.estado == EstadoSalud.INFECTADO:
        # ... lógica de aislamiento existente ...
        return
    
    # NUEVO: Verificar evento activo
    if self.model.evento_activo and self._debe_asistir_evento():
        self.mover_a(self.model.celda_evento)
        return
    
    # ... resto de lógica de movilidad existente ...

def _debe_asistir_evento(self) -> bool:
    """Decide si el agente asiste al evento."""
    prob_base = getattr(self.model, 'prob_participar_evento', 0.3)
    
    # Ajustar según tipo (estudiantes y móviles más propensos)
    multiplicador = {
        TipoMovilidad.ESTUDIANTE: 1.5,
        TipoMovilidad.TRABAJADOR: 0.8,
        TipoMovilidad.MOVIL_CONTINUO: 1.3,
        TipoMovilidad.ESTACIONARIO: 0.3
    }
    
    prob_ajustada = prob_base * multiplicador.get(self.tipo, 1.0)
    return self.random.random() < min(prob_ajustada, 1.0)
```

**Configuración YAML**:
```yaml
events:
  enabled: true
  interval_days: 7            # Evento cada 7 días
  base_participation_prob: 0.3  # 30% participan
  participation_by_type:
    student: 1.5              # 150% más propenso
    worker: 0.8               # 80% (menos propenso)
    mobile: 1.3
    stationary: 0.3
```

**DataCollector** - Agregar métricas:
```python
self.datacollector = DataCollector(
    model_reporters={
        # ... existentes ...
        "Evento_Activo": lambda m: m.evento_activo,
        "Densidad_Evento": lambda m: m._calcular_densidad_evento(),
    },
    # ...
)

def _calcular_densidad_evento(self) -> int:
    """Cuenta humanos en celda de evento."""
    if not self.evento_activo or not self.celda_evento:
        return 0
    
    agentes = self.grid.get_cell_list_contents([self.celda_evento])
    return sum(1 for a in agentes if isinstance(a, HumanAgent))
```

#### 🎯 Impacto Esperado
- **Picos de Transmisión**: Aumentos súbitos de incidencia post-evento
- **Escenarios**: Evaluar impacto de prohibir eventos en epidemia
- **Realismo**: Captura dinámica social de congregaciones

---

## 🔧 Componentes Parcialmente Implementados (Mejoras)

### ⚠️ 1. Integración Meteostat API

**Archivo**: `dengue_model.py`, línea 260-272

**Problema Actual**:
```python
def _obtener_clima_meteostat(self) -> Tuple[float, float]:
    # TODO: Implementar conexión real con Meteostat
    raise Exception("Meteostat no implementado aún")  # ❌
```

**Solución**:
```python
def _obtener_clima_meteostat(self) -> Tuple[float, float]:
    """
    Obtiene clima real de Bucaramanga vía Meteostat API.
    
    Requiere: pip install meteostat
    """
    from meteostat import Point, Daily
    from datetime import datetime, timedelta
    
    # Coordenadas de Bucaramanga
    lat, lon, alt = 7.1254, -73.1198, 959  # m.s.n.m.
    location = Point(lat, lon, alt)
    
    # Obtener datos del día actual simulado
    fecha = self.fecha_actual
    
    try:
        # Consultar API
        data = Daily(location, fecha, fecha + timedelta(days=1))
        data = data.fetch()
        
        if data.empty:
            raise ValueError("Sin datos")
        
        temp = data['tavg'].iloc[0]  # Temperatura promedio
        precip = data['prcp'].iloc[0]  # Precipitación
        
        # Manejar valores NaN
        temp = temp if not np.isnan(temp) else 23.0
        precip = precip if not np.isnan(precip) else 0.0
        
        return float(temp), float(precip)
    
    except Exception as e:
        # Fallback a modelo sintético
        return (self._generar_temperatura_sintetica(),
                self._generar_precipitacion_sintetica())
```

**Dependencias**:
```bash
pip install meteostat
```

**Configuración YAML**:
```yaml
climate:
  use_real_data: true        # false = modelo sintético
  location:
    name: "Bucaramanga"
    latitude: 7.1254
    longitude: -73.1198
    altitude: 959            # metros sobre el nivel del mar
  synthetic_fallback: true   # Usar sintético si API falla
```

---

### ⚠️ 2. Control Larvario (LSM) Mejorado

**Archivo**: `dengue_model.py`, línea 331-343

**Problema Actual**:
```python
def _aplicar_lsm(self):
    """Elimina huevos uniformemente."""
    # ❌ Simplificado: elimina 56% de TODOS los huevos
```

**Mejora Requerida**:
```python
def _aplicar_lsm(self):
    """
    Control larvario mejorado con cobertura espacial.
    
    Lógica realista:
    1. Seleccionar 70% de sitios de cría (cobertura)
    2. En esos sitios, eliminar 80% de huevos (efectividad)
    3. Priorizar celdas tipo AGUA (permanentes)
    """
    from .celda import TipoCelda
    
    self.lsm_activo = True
    
    # Obtener parámetros
    cobertura = getattr(self, 'lsm_cobertura', 0.7)
    efectividad = getattr(self, 'lsm_efectividad', 0.8)
    
    # 1. Identificar sitios de cría con huevos
    sitios_con_huevos = {}
    for agente in self.schedule.agents:
        if isinstance(agente, MosquitoAgent) and agente.etapa == EtapaVida.HUEVO:
            sitio = agente.sitio_cria
            if sitio not in sitios_con_huevos:
                sitios_con_huevos[sitio] = []
            sitios_con_huevos[sitio].append(agente)
    
    # 2. Seleccionar sitios a tratar (70%)
    sitios_lista = list(sitios_con_huevos.keys())
    num_tratar = int(len(sitios_lista) * cobertura)
    sitios_tratados = self.random.sample(sitios_lista, num_tratar)
    
    # 3. Eliminar huevos en sitios tratados (80% efectividad)
    eliminados = 0
    for sitio in sitios_tratados:
        huevos = sitios_con_huevos[sitio]
        for huevo in huevos:
            if self.random.random() < efectividad:
                self.schedule.remove(huevo)
                eliminados += 1
    
    # Registrar métrica
    if not hasattr(self, 'lsm_huevos_eliminados'):
        self.lsm_huevos_eliminados = 0
    self.lsm_huevos_eliminados += eliminados
```

**Configuración YAML**:
```yaml
control_strategies:
  lsm:
    enabled: true
    frequency_days: 7        # Aplicar cada 7 días
    coverage: 0.7            # 70% de sitios tratados
    effectiveness: 0.8       # 80% eliminación en sitios tratados
    prioritize_permanent: true  # Priorizar celdas tipo AGUA
```

---

### ⚠️ 3. ITN/IRS (Redes/Insecticidas) Implementación

**Archivo**: `dengue_model.py`, línea 345-354

**Problema Actual**:
```python
def _aplicar_itn_irs(self):
    """Stub - NO implementado."""
    self.itn_irs_activo = True
    # ❌ NO hace nada real
```

**Implementación Completa**:

**DengueModel** - Agregar atributos:
```python
def __init__(self, ...):
    # ... código existente ...
    
    # ITN/IRS
    self.hogares_protegidos = set()  # Set de posiciones de hogares con ITN/IRS
    self.dias_proteccion_restante = {}  # {pos_hogar: dias_restantes}
```

**DengueModel._aplicar_itn_irs()** - Implementar:
```python
def _aplicar_itn_irs(self):
    """
    Aplica ITN/IRS a 60% de hogares por 90 días.
    
    Efectos:
    - 70% reducción en probabilidad de picadura
    - Duración: 90 días desde aplicación
    - Cobertura: 60% de hogares únicos
    """
    self.itn_irs_activo = True
    
    cobertura = getattr(self, 'itn_irs_cobertura', 0.6)
    duracion = getattr(self, 'itn_irs_duracion', 90)
    
    # Activar si es día de aplicación o si ya está activo
    if self.dia_simulacion == 1 or not self.hogares_protegidos:
        # Primera aplicación: seleccionar hogares
        hogares_unicos = set(a.pos_hogar for a in self.schedule.agents
                            if isinstance(a, HumanAgent))
        
        num_proteger = int(len(hogares_unicos) * cobertura)
        self.hogares_protegidos = set(self.random.sample(
            list(hogares_unicos), num_proteger
        ))
        
        # Inicializar duración
        for hogar in self.hogares_protegidos:
            self.dias_proteccion_restante[hogar] = duracion
    
    # Actualizar duración de protección
    expirados = []
    for hogar in self.hogares_protegidos:
        self.dias_proteccion_restante[hogar] -= 1
        if self.dias_proteccion_restante[hogar] <= 0:
            expirados.append(hogar)
    
    # Remover hogares con protección vencida
    for hogar in expirados:
        self.hogares_protegidos.remove(hogar)
        del self.dias_proteccion_restante[hogar]
    
    # Desactivar si no quedan hogares protegidos
    if not self.hogares_protegidos:
        self.itn_irs_activo = False
```

**MosquitoAgent.intentar_picar()** - Agregar lógica de reducción:
```python
def intentar_picar(self):
    """Picar con reducción por ITN/IRS."""
    if self.ha_picado_hoy:
        return
    
    agentes_celda = self.model.grid.get_cell_list_contents([self.pos])
    humanos = [a for a in agentes_celda if a.__class__.__name__ == 'HumanAgent']
    
    if not humanos:
        return
    
    humano = self.random.choice(humanos)
    
    # ✅ NUEVO: Verificar protección ITN/IRS
    if self.model.itn_irs_activo:
        hogar_protegido = humano.pos_hogar in self.model.hogares_protegidos
        if hogar_protegido:
            reduccion = getattr(self.model, 'itn_irs_reduccion', 0.7)
            if self.random.random() < reduccion:
                # Picadura bloqueada por ITN/IRS
                return
    
    self.ha_picado_hoy = True
    
    # ... resto de lógica de transmisión ...
```

**Configuración YAML**:
```yaml
control_strategies:
  itn_irs:
    enabled: true
    coverage: 0.6            # 60% de hogares
    duration_days: 90        # Duración de protección
    bite_reduction: 0.7      # 70% reducción en picaduras
```

---

## 📊 Matriz de Priorización

| Componente | Complejidad | Impacto Científico | Tiempo Estimado | Prioridad |
|------------|-------------|-------------------|-----------------|-----------|
| **Extensión 4: Tipos de Celdas** | 🟡 Media | 🔴 Crítico | 4-6 horas | 🔴 **1. URGENTE** |
| **Extensión 2: Aislamiento** | 🟢 Baja | 🔴 Alto | 2-3 horas | 🔴 **2. ALTA** |
| **Extensión 1: Variabilidad** | 🟢 Baja | 🟡 Medio-Alto | 2-3 horas | 🟡 **3. MEDIA** |
| **Extensión 3: Criaderos Dinámicos** | 🟡 Media | 🟡 Medio | 3-4 horas | 🟡 **4. MEDIA** |
| **ITN/IRS Completo** | 🟡 Media | 🟡 Medio | 2-3 horas | 🟡 **5. MEDIA** |
| **Meteostat API** | 🟢 Baja | 🟢 Bajo | 1-2 horas | 🟢 **6. BAJA** |
| **Extensión 5: Eventos** | 🟡 Media | 🟢 Bajo | 3-4 horas | 🟢 **7. BAJA** |
| **LSM Mejorado** | 🟢 Baja | 🟢 Bajo | 1-2 horas | 🟢 **8. BAJA** |

**Total tiempo estimado**: 18-27 horas de desarrollo

---

## 🎯 Plan de Implementación Recomendado

### Fase 1: Fundamentos Espaciales (6-9 horas) - **PRIORITARIO**
1. ✅ **Tipos de Celdas** (Extensión 4)
   - Crear clase `Celda`
   - Inicializar mapa en `DengueModel`
   - Implementar búsqueda de parques
   - Implementar búsqueda de sitios de cría
   - **Razón**: Desbloquea lógica de movilidad y reproducción

2. ✅ **Aislamiento de Infectados** (Extensión 2)
   - Implementar decisión estocástica de aislamiento
   - Agregar movilidad reducida como opción
   - **Razón**: Afecta R₀ y validación del modelo

### Fase 2: Heterogeneidad Biológica (5-7 horas)
3. ✅ **Variabilidad Individual** (Extensión 1)
   - Parámetros estocásticos en `MosquitoAgent`
   - Parámetros estocásticos en `HumanAgent`
   - Actualizar configuración YAML
   - **Razón**: Mejora realismo de distribuciones

4. ✅ **Criaderos Dinámicos** (Extensión 3)
   - Implementar `_actualizar_criaderos_temporales()`
   - Vincular con precipitación
   - **Razón**: Captura estacionalidad vectorial

### Fase 3: Intervenciones y Clima (4-6 horas)
5. ✅ **ITN/IRS Completo**
   - Gestión de hogares protegidos
   - Reducción de picaduras

6. ✅ **Meteostat API**
   - Integración con API real
   - Fallback sintético robusto

### Fase 4: Extensiones Sociales (3-4 horas) - **OPCIONAL**
7. ⚪ **Eventos de Aglomeración** (Extensión 5)
   - Sistema de eventos periódicos
   - Movilidad hacia eventos

8. ⚪ **LSM Mejorado**
   - Cobertura espacial realista

---

## ✅ Checklist de Validación Post-Implementación

### Tests Unitarios Requeridos
```python
# tests/test_extensiones.py

def test_variabilidad_mosquitos():
    """Verificar que cada mosquito tiene parámetros únicos."""
    # Crear 100 mosquitos
    # Verificar desviación estándar de mortalidad > 0

def test_aislamiento_infectados():
    """Verificar decisión de aislamiento."""
    # Crear 100 humanos infectados
    # ~70% deben estar en_aislamiento=True

def test_tipos_celdas():
    """Verificar distribución de tipos."""
    # Contar celdas por tipo
    # Verificar proporciones ~5% agua, ~10% parque

def test_busqueda_parques():
    """Verificar que humanos encuentran parques."""
    # Crear humano en (0,0)
    # Crear parque en (5,5)
    # Verificar que encuentra el parque

def test_criaderos_temporales():
    """Verificar creación/eliminación de charcos."""
    # Simular día con lluvia intensa
    # Verificar sitios_cria_temporales > 0
    # Simular 7 días sin lluvia
    # Verificar sitios_cria_temporales = 0

def test_itn_irs_reduccion():
    """Verificar reducción de picaduras con ITN/IRS."""
    # Activar ITN/IRS
    # Contar picaduras con/sin protección
    # Verificar reducción ~70%
```

### Tests de Integración
```python
def test_simulacion_completa_365_dias():
    """Verificar que modelo corre 1 año sin errores."""

def test_consistencia_poblaciones():
    """Verificar conservación de poblaciones."""
    # Nacimientos + muertes = balance consistente

def test_transmision_funciona():
    """Verificar que ocurre transmisión."""
    # Iniciar con 1 infectado
    # Verificar propagación después de 30 días
```

---

## 📈 Métricas de Validación del Modelo Completo

### Comparación con Paper Base (Jindal & Rao 2017)
- [ ] Curva de incidencia similar (pico ~día 60-90)
- [ ] R₀ efectivo en rango 1.5-3.0
- [ ] Tasa de ataque final 30-60% según parámetros
- [ ] Dinámica vectorial: picos correlacionados con lluvia

### Validación con Datos de Bucaramanga
- [ ] Obtener datos históricos dengue 2023-2024
- [ ] Calibrar parámetros para reproducir curva real
- [ ] Análisis de sensibilidad: ±20% en parámetros críticos
- [ ] Validación cruzada: datos 2024 para calibrar, 2023 para validar

---

## 📝 Notas Finales

### Archivos a Crear
1. `src/model/celda.py` - Clase Celda y TipoCelda
2. `tests/test_extensiones.py` - Suite de tests
3. `config/scenario_*.yaml` - Configuraciones de escenarios

### Archivos a Modificar
1. `src/agents/human_agent.py` - Aislamiento, búsqueda parques, variabilidad
2. `src/agents/mosquito_agent.py` - Búsqueda sitios, variabilidad
3. `src/model/dengue_model.py` - Tipos celdas, criaderos dinámicos, ITN/IRS, eventos
4. `config/simulation_config.yaml` - Nuevos parámetros

### Documentación a Actualizar
1. `docs/CONFIGURACION_PARAMETROS.md` - Agregar nuevos parámetros
2. `README.md` - Actualizar sección de características
3. `CHANGELOG.md` - Crear con registro de cambios

---

**Preparado por**: GitHub Copilot  
**Fecha**: 3 de Noviembre de 2025  
**Versión del Análisis**: 1.0  
**Estado del Proyecto**: En desarrollo - Núcleo completo, extensiones pendientes
