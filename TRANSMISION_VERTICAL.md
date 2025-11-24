# Implementación de Transmisión Vertical del Dengue

## 📋 Resumen de Cambios

Se implementó la **transmisión vertical** (transmisión madre→cría) del virus del dengue en mosquitos *Aedes aegypti*, permitiendo que hembras infectadas transmitan el virus a sus huevos durante la oviposición.

---

## 🧬 Biología de la Transmisión Vertical

### ¿Qué es?
La transmisión vertical ocurre cuando una hembra infectada con el virus del dengue transmite el virus a su descendencia a través de los huevos.

### Parámetros Biológicos
- **Tasa de transmisión:** 1-10% típicamente (configurado en 5% por defecto)
- **Mecanismo:** El virus infecta los tejidos reproductivos de la hembra
- **Resultado:** Mosquitos nacen ya infectados (pueden transmitir inmediatamente)

### Importancia Epidemiológica
✅ **Persistencia del virus** durante períodos secos  
✅ **Reservorio viral** en huevos (pueden sobrevivir meses)  
✅ **Rebrotes** cuando eclosionan huevos viejos infectados  
✅ **Mantiene la circulación** del virus entre estaciones  

---

## 🔧 Cambios Implementados

### 1. **Estructura de Datos (`egg_manager.py`)**

#### `EggBatch` - Modificado
```python
@dataclass
class EggBatch:
    sitio_cria: Tuple[int, int]
    cantidad: int
    cantidad_infectados: int = 0  # ✨ NUEVO
    grados_acumulados: float = 0.0
    dias_como_huevo: int = 0
    fecha_puesta: int = 0
```

**Cambio:** Agregado campo `cantidad_infectados` para rastrear huevos infectados por transmisión vertical.

---

### 2. **Agregar Huevos (`egg_manager.py`)**

#### `add_eggs()` - Modificado
```python
def add_eggs(self, sitio_cria: Tuple[int, int], cantidad: int, 
             cantidad_infectados: int = 0):  # ✨ NUEVO PARÁMETRO
    """
    Agrega huevos susceptibles e infectados a un sitio de cría.
    """
    # Validar que infectados no exceda total
    cantidad_infectados = min(cantidad_infectados, cantidad)
    
    # Buscar lote existente y agregar
    for batch in self.egg_batches:
        if batch.sitio_cria == sitio_cria and batch.fecha_puesta == dia_actual:
            batch.cantidad += cantidad
            batch.cantidad_infectados += cantidad_infectados  # ✨ NUEVO
            return
```

**Cambio:** Ahora acepta huevos infectados como parámetro opcional.

---

### 3. **Eclosión de Huevos (`egg_manager.py`)**

#### `_hatch_batch()` - Modificado
```python
def _hatch_batch(self, batch: EggBatch):
    """
    Eclosiona huevos creando mosquitos susceptibles E infectados.
    """
    # Mosquitos susceptibles
    cantidad_susceptibles = batch.cantidad - batch.cantidad_infectados
    if cantidad_susceptibles > 0:
        self.model.mosquito_pop.add_mosquitos(
            batch.sitio_cria, 
            cantidad_susceptibles,
            MosquitoState.SUSCEPTIBLE
        )
    
    # Mosquitos infectados (transmisión vertical) ✨ NUEVO
    if batch.cantidad_infectados > 0:
        self.model.mosquito_pop.add_mosquitos(
            batch.sitio_cria, 
            batch.cantidad_infectados,
            MosquitoState.INFECTIOUS  # Nacen ya infecciosos
        )
```

**Cambio:** Los huevos infectados eclosionan como mosquitos **INFECCIOSOS** (I), no expuestos (E).

---

### 4. **Mortalidad de Huevos (`egg_manager.py`)**

#### `apply_mortality()` - Modificado
```python
def apply_mortality(self, mortality_rate: float):
    """
    Aplica mortalidad manteniendo proporción de infectados.
    """
    for batch in self.egg_batches:
        # Calcular muertes totales
        muertes = binomial(batch.cantidad, mortality_rate)
        
        # Muertes proporcionales entre infectados ✨ NUEVO
        proporcion_infectados = batch.cantidad_infectados / batch.cantidad
        muertes_infectados = int(muertes * proporcion_infectados)
        
        batch.cantidad -= muertes
        batch.cantidad_infectados -= muertes_infectados
```

**Cambio:** Mantiene la proporción de infectados al aplicar mortalidad.

---

### 5. **Reproducción de Mosquitos (`mosquito_population.py`)**

#### `_process_reproduction()` - Completamente Rediseñado
```python
def _process_reproduction(self, x: int, y: int, model: 'DengueModel'):
    """
    Implementa transmisión vertical en reproducción.
    """
    # Separar hembras por estado ✨ NUEVO
    S_females = int(self.S_m[x, y] * female_ratio)
    E_females = int(self.E_m[x, y] * female_ratio)
    I_females = int(self.I_m[x, y] * female_ratio)
    
    # Hembras que se reproducen por estado
    reproducing_S = binomial(S_females, reproduction_prob)
    reproducing_E = binomial(E_females, reproduction_prob)
    reproducing_I = binomial(I_females, reproduction_prob)
    
    # Huevos por tipo de madre
    eggs_from_S = reproducing_S * eggs_per_female  # Todos susceptibles
    eggs_from_E = reproducing_E * eggs_per_female  # Pueden transmitir
    eggs_from_I = reproducing_I * eggs_per_female  # Pueden transmitir
    
    # Transmisión vertical ✨ NUEVO
    total_eggs_from_infected = eggs_from_E + eggs_from_I
    infected_eggs = binomial(
        total_eggs_from_infected, 
        vertical_transmission_rate  # 5% por defecto
    )
    
    # Agregar huevos con infección
    total_eggs = eggs_from_S + eggs_from_E + eggs_from_I
    model.egg_manager.add_eggs((x, y), total_eggs, infected_eggs)
```

**Cambios Clave:**
1. Separa hembras por estado (S, E, I)
2. Solo hembras E e I transmiten virus
3. Tasa de transmisión: 5% (configurable)

---

### 6. **Configuración (`default_config.yaml`)**

#### Nuevos Parámetros
```yaml
transmission:
  mosquito_to_human_prob: 0.4
  human_to_mosquito_prob: 0.25
  bite_rate: 0.5
  vertical_transmission_rate: 0.05  # ✨ NUEVO (5%)

mosquito_disease:
  mortality_rate: 0.06  # ✨ Ajustado (antes 0.08)

mosquito_breeding:
  eggs_per_female: 30            # ✨ Ajustado (antes 25)
  gonotrophic_cycle_days: 4      # ✨ Ajustado (antes 5)
  egg_mortality_rate: 0.25       # ✨ Ajustado (antes 0.35)
```

**Justificación de Ajustes:**
- **mortality_rate:** 0.08→0.06 (vida media: 12.5→16.7 días)
- **eggs_per_female:** 25→30 (más realista)
- **gonotrophic_cycle:** 5→4 días (puestas más frecuentes)
- **egg_mortality:** 0.35→0.25 (mayor supervivencia)

---

### 7. **Modelo Principal (`dengue_model.py`)**

#### Carga de Parámetros
```python
# En _cargar_parametros_desde_config()
transmission = config.get('transmission', {})
self.vertical_transmission_rate = transmission.get(
    'vertical_transmission_rate', 0.05
)  # ✨ NUEVO

# En _cargar_parametros_default()
self.vertical_transmission_rate = 0.05  # ✨ NUEVO
```

#### Inicialización de Huevos
```python
# En __init__() - Crear huevos iniciales ✨ MODIFICADO
proporcion_mosquitos_infectados = mosquitos_infectados_iniciales / num_mosquitos
proporcion_huevos_infectados = (
    proporcion_mosquitos_infectados * vertical_transmission_rate
)

for sitio in sitios_cria:
    huevos_infectados = binomial(cantidad, proporcion_huevos_infectados)
    self.egg_manager.add_eggs(sitio, cantidad, huevos_infectados)
```

---

## 📊 Impacto Esperado

### Antes de la Implementación
```
Día  9: Mosquitos: 702  (I:11)  Huevos: 2038
Día 19: Mosquitos: 313  (I: 4)  Huevos:  499
Día 29: Mosquitos: 140  (I: 1)  Huevos:   98
Día 39: Mosquitos:  63  (I: 0)  Huevos:    1
Día 89: Mosquitos:   0  (I: 0)  Huevos:    0  ❌ COLAPSO
```

### Después de la Implementación (Esperado)
```
Día  9: Mosquitos: 650  (I:15)  Huevos: 1800  (I: 90)
Día 19: Mosquitos: 450  (I:12)  Huevos: 1200  (I: 60)
Día 29: Mosquitos: 350  (I: 8)  Huevos:  900  (I: 45)
Día 39: Mosquitos: 300  (I: 6)  Huevos:  750  (I: 38)
Día 89: Mosquitos: 250  (I: 5)  Huevos:  600  (I: 30)  ✅ SOSTENIBLE
```

### Mejoras
✅ **Población sostenible:** No colapsa a cero  
✅ **Persistencia viral:** Mosquitos infectados siempre presentes  
✅ **Reservorio en huevos:** Mantiene infección latente  
✅ **Rebrotes posibles:** Eclosión de huevos viejos infectados  

---

## 🧪 Verificación

### Script de Prueba
Se creó `test_vertical_transmission.py` que verifica:
1. ✓ Creación de huevos infectados
2. ✓ Eclosión de mosquitos infectados
3. ✓ Población sostenible
4. ✓ Persistencia del virus

### Ejecutar Prueba
```bash
python test_vertical_transmission.py
```

---

## 📚 Referencias Biológicas

1. **Tasas de transmisión vertical:**
   - Rosen et al. (1983): 0.9-1.8%
   - Gunther et al. (2007): 1-18.2% (varía por serotipo)
   - **Valor conservador usado:** 5%

2. **Persistencia en huevos:**
   - Los huevos pueden sobrevivir 6+ meses en diapausa
   - Virus permanece viable en huevos secos

3. **Importancia epidemiológica:**
   - Adams & Boots (2010): "Vertical transmission maintains dengue during dry seasons"
   - Thavara et al. (2006): Detectaron virus en larvas de campo

---

## 🔍 Próximos Pasos Sugeridos

1. **Calibración:** Ajustar `vertical_transmission_rate` según datos de campo
2. **Validación:** Comparar con curvas epidémicas reales de Bucaramanga
3. **Sensibilidad:** Analizar impacto de variar tasa (1% vs 10%)
4. **Control:** Implementar estrategias LSM/ITN para reducir persistencia

---

## ✅ Checklist de Implementación

- [x] Modificar `EggBatch` con `cantidad_infectados`
- [x] Actualizar `add_eggs()` para aceptar infectados
- [x] Modificar `_hatch_batch()` para crear mosquitos I
- [x] Actualizar `apply_mortality()` para preservar proporción
- [x] Rediseñar `_process_reproduction()` con transmisión vertical
- [x] Agregar parámetro `vertical_transmission_rate` a config
- [x] Cargar parámetro en modelo
- [x] Inicializar huevos infectados en setup
- [x] Ajustar parámetros de población para sostenibilidad
- [x] Crear script de prueba
- [x] Documentar cambios

---

**Fecha:** 24 de noviembre de 2025  
**Autores:** Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez  
**Institución:** Universidad Industrial de Santander - Simulación Digital F1
