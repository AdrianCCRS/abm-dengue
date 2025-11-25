# Lógica del Modelo ABM de Dengue - Bucaramanga

## Tabla de Contenidos
1. [Arquitectura General](#arquitectura-general)
2. [Modelo Metapoblacional de Mosquitos](#modelo-metapoblacional-de-mosquitos)
3. [Población Humana](#población-humana)
4. [Efectos Climáticos](#efectos-climáticos)
5. [Estrategias de Control](#estrategias-de-control)
6. [Transmisión del Virus](#transmisión-del-virus)
7. [Referencias Científicas](#referencias-científicas)

---

## Arquitectura General

### Descripción del Sistema

El modelo simula la transmisión de dengue en la ciudad de Bucaramanga mediante un **Modelo Basado en Agentes (ABM)** que representa de manera realista cómo interactúan humanos, mosquitos y el ambiente.

#### ¿Qué es un Modelo Basado en Agentes?
Un ABM simula el comportamiento de individuos autónomos (agentes) que siguen reglas simples. La complejidad emerge de las interacciones entre miles de agentes. Es como simular una ciudad donde cada persona y mosquito toma decisiones según su estado y entorno.

#### Componentes del Sistema:

1. **10,000 Agentes Humanos**
   - Cada humano es un agente individual con:
     * **Estado de salud**: Susceptible (S), Expuesto (E), Infectado (I), o Recuperado (R)
     * **Ubicación**: Posición en el grid (celda x,y)
     * **Patrón de movilidad**: Estudiante, trabajador, móvil continuo, o estacionario
     * **Lugares específicos**: Hogar, trabajo/escuela (si aplica)
   - Ejemplo: "Juan es un trabajador, vive en celda (10,15), trabaja en (25,30), actualmente está Susceptible"

2. **Poblaciones de Mosquitos en Grid 50×50**
   - La ciudad se divide en una cuadrícula de 50×50 = 2,500 celdas
   - Cada celda representa ~100m × 100m en el mundo real
   - En cada celda guardamos CANTIDADES de mosquitos (no mosquitos individuales):
     * S_m[x,y] = número de mosquitos susceptibles
     * E_m[x,y] = número de mosquitos expuestos
     * I_m[x,y] = número de mosquitos infecciosos
   - Ejemplo: "En celda (20,20) hay 50 mosquitos susceptibles, 10 expuestos, 5 infecciosos"

3. **Datos Climáticos Reales**
   - Leídos desde archivo CSV con datos históricos de Bucaramanga
   - Cada día del año tiene:
     * Temperatura promedio (°C)
     * Precipitación total (mm)
   - Ejemplo: "1 de enero 2022: 23.5°C, 12.3mm de lluvia"

4. **Espacio Urbano Heterogéneo**
   - **Celdas urbanas (85%)**: Viviendas, edificios, donde vive la gente
   - **Celdas de parque (10%)**: Zonas verdes, mayor actividad recreativa
   - **Celdas de agua (5%)**: Ríos, lagos, sitios permanentes de cría de mosquitos
   - Esta distribución refleja la estructura real de una ciudad tropical

### Flujo de Simulación Diaria

Cada "día" en la simulación ejecuta un ciclo completo de 10 pasos. Piensa en esto como la rutina diaria de la ciudad:

#### **1. Actualización de Fecha y Clima** 📅🌡️
```
Acción: Avanzar un día y leer datos climáticos del CSV
Entrada: Archivo datos_climaticos_2022.csv
Salida: Temperatura del día (ej: 23.5°C), Precipitación (ej: 15.2mm)

Ejemplo:
  Día 1: Lee fila 1 del CSV → 25°C, 0mm
  Día 2: Lee fila 2 del CSV → 24°C, 5mm
  Día 50: Lee fila 50 del CSV → 21°C, 30mm
```

#### **2. Gestión de Sitios de Cría** 💧
```
Acción: Crear charcos nuevos si llovió, eliminar charcos secos

SI precipitación >= 5mm:
  - Crear charcos temporales (0.5 charcos por cada mm de lluvia)
  - Ejemplo: 20mm → 10 charcos nuevos
  - Cada charco dura 7 días

PARA cada charco existente:
  - Decrementar días restantes
  - SI días restantes == 0: Eliminar charco (se secó)

Ejemplo visual:
  Día 10: Llueven 30mm → Crear 15 charcos (duran hasta día 17)
  Día 11-16: Charcos aún disponibles para oviposición
  Día 17: Charcos se secan y desaparecen
```

#### **3. Desarrollo de Huevos** 🥚➡️🦟
```
Acción: Acumular grados-día en cada lote de huevos, eclosionar si alcanza umbral

PARA cada lote de huevos en cada sitio de cría:
  - Calcular grados-día hoy: GD = max(Temperatura - 8.3°C, 0)
  - Acumular: lote.grados_acumulados += GD
  - SI lote.grados_acumulados >= 181.2:
      → Eclosionar: Crear mosquitos adultos en la celda del sitio
      → Huevos infectados → Mosquitos infecciosos (transmisión vertical)
      → Huevos sanos → Mosquitos susceptibles

Ejemplo numérico:
  Lote A: 100 huevos (5 infectados)
  - Día 1 (25°C): GD=16.7 → Acumulado=16.7
  - Día 2 (26°C): GD=17.7 → Acumulado=34.4
  - ...
  - Día 11 (25°C): GD=16.7 → Acumulado=183.7 >= 181.2
  → ECLOSIÓN: 95 mosquitos S_m + 5 mosquitos I_m en esa celda
```

#### **4. Mortalidad de Huevos** ☠️🥚
```
Acción: Aplicar mortalidad diaria según temperatura

PARA cada lote de huevos:
  - Determinar tasa de mortalidad según temperatura:
    * < 10°C o > 40°C (extremo): 90% mueren
    * 10-15°C o 35-40°C (subóptimo): 50% mueren
    * 25-30°C (óptimo): 0% mueren (todos sobreviven)
  
  - Calcular muertos: Binomial(n=huevos, p=tasa)
  - Remover huevos muertos del lote

Ejemplo:
  Lote B: 200 huevos a 12°C (frío subóptimo)
  - Tasa mortalidad = 50%
  - Muertos = Binomial(200, 0.5) ≈ 100
  - Sobreviven ≈ 100 huevos
```

#### **5. Dinámica de Mosquitos** 🦟
```
Acción: Procesar cada celda del grid - mortalidad, incubación, reproducción

PARA cada celda (x,y) del grid 50×50:
  
  A. MORTALIDAD (5% base, modificado por temperatura):
     - Tasa efectiva = 0.05 × multiplicador_climático
     - Muertos_S = Binomial(S_m[x,y], tasa)
     - Muertos_E = Binomial(E_m[x,y], tasa)
     - Muertos_I = Binomial(I_m[x,y], tasa)
     - Actualizar poblaciones restando muertos
  
  B. INCUBACIÓN EXTRÍNSECA (E → I):
     - EIP = 10 días (ajustado por temperatura)
     - Nuevos_infectados = Binomial(E_m[x,y], 1/EIP)
     - E_m[x,y] -= Nuevos_infectados
     - I_m[x,y] += Nuevos_infectados
  
  C. REPRODUCCIÓN (solo mosquitos hembra que picaron):
     - Identificar mosquitos que pueden reproducir
     - Buscar sitio de cría cercano (radio 5 celdas)
     - SI hay sitio: Depositar ~50 huevos por hembra
     - 5% de huevos heredan infección si madre infectada

Ejemplo en celda (25,25):
  Inicio: S_m=100, E_m=20, I_m=10
  
  Mortalidad (25°C, óptimo, 5%):
    - Muertos_S ≈ 5, Muertos_E ≈ 1, Muertos_I ≈ 0
    - Quedan: S_m=95, E_m=19, I_m=10
  
  Incubación (EIP=10 días):
    - Nuevos_I = Binomial(19, 0.1) ≈ 2
    - Quedan: S_m=95, E_m=17, I_m=12
  
  Reproducción:
    - 10 hembras pican y ponen huevos
    - 10 × 50 = 500 huevos depositados en sitio cercano
    - Si hembra infectada: 25 huevos infectados (5%)
```

#### **6. Aplicación de Controles** 🛡️
```
Acción: SI estrategias activas, aplicar intervenciones

SI LSM activo Y (día % 7 == 0):  # Cada 7 días
  - Visitar 70% de sitios de cría
  - En cada sitio visitado: Eliminar 80% de huevos
  - Efecto neto: 56% reducción semanal
  
  Ejemplo:
    Sitio X: 1000 huevos
    - Probabilidad visita = 70% → Visitado
    - Eliminar 80% → Quedan 200 huevos

SI ITN/IRS activo Y dentro_de_duracion:  # 90 días
  - Proteger 60% de hogares
  - En hogares protegidos:
    * Reducir picaduras 70% (barrera física)
    * Aumentar mortalidad mosquitos +20% (insecticida)
  
  Ejemplo:
    Hogar celda (15,15): Protegido
    - Picaduras normales: 10/día → Efectivas: 3/día
    - Mortalidad mosquitos: 5% → 25% diario
```

#### **7. Activación de Humanos** 🚶‍♂️🚶‍♀️
```
Acción: Cada humano se mueve y puede infectarse/transmitir

PARA cada humano (10,000 iteraciones):
  
  1. MOVIMIENTO según patrón:
     - Estudiante: 35% va a escuela, 55% queda en casa, 10% parque
     - Trabajador: 35% va a trabajo, 60% casa, 5% parque
     - Móvil: 40% movimiento aleatorio, 40% casa, 20% parque
     - Estacionario: 95% casa, 5% parque
     
     SI infectado: 70% se aísla en casa
  
  2. INTERACCIÓN CON MOSQUITOS en celda actual:
     - Contar mosquitos infectados: I_m[celda_humano]
     - Ajustar actividad por lluvia:
       * > 20mm: Solo 30% mosquitos activos
       * > 10mm: 60% activos
       * ≤ 10mm: 100% activos
     
     - Intentos de picadura: Binomial(I_m, bite_rate × actividad)
  
  3. TRANSMISIÓN MOSQUITO→HUMANO (SI humano Susceptible):
     - PARA cada picadura:
       - Probabilidad infección = 60%
       - SI aleatorio < 0.60: S → E
  
  4. TRANSMISIÓN HUMANO→MOSQUITO (SI humano Infectado):
     - Mosquitos_infectados = Binomial(picaduras, 27.5%)
     - S_m[celda] -= Mosquitos_infectados
     - E_m[celda] += Mosquitos_infectados

Ejemplo caso concreto:
  Humana María (Trabajadora, Susceptible):
    - Ubicación actual: Celda (30,20) - Su trabajo
    - Mosquitos en celda: I_m=15
    - Clima: 2mm lluvia → 100% actividad
    - Picaduras: Binomial(15, 0.33) = 5 picaduras
    - Transmisión: Por cada picadura, 60% probabilidad
      * Picadura 1: 0.45 < 0.60 → ¡INFECTADA!
      * María: S → E (incubación 5 días)
  
  Humano Pedro (Estudiante, Infectado día 3):
    - Ubicación: Celda (10,10) - Aislado en casa
    - Mosquitos susceptibles: S_m=50
    - Picaduras: Binomial(50, 0.33) = 17
    - Transmisión: Binomial(17, 0.275) = 5 mosquitos infectados
    - Actualización celda:
      * S_m[10,10] = 50 - 5 = 45
      * E_m[10,10] = 0 + 5 = 5 (inician incubación)
```

#### **8. Progresión de Estados Humanos** ⏭️
```
Acción: Avanzar estados epidemiológicos (E→I, I→R, R→S)

PARA cada humano:
  
  SI estado == EXPUESTO:
    - Incrementar días_incubacion
    - SI días_incubacion >= 5: E → I
  
  SI estado == INFECTADO:
    - Incrementar días_infección
    - SI días_infección >= 6: I → R
  
  SI estado == RECUPERADO:
    - Probabilidad pérdida inmunidad = 0.5% diario
    - SI aleatorio < 0.005: R → S

Ejemplo:
  Humano Ana:
    - Día 1: S (susceptible)
    - Día 10: Picada → E (expuesto, contador=0)
    - Día 11-14: E (contador=1,2,3,4)
    - Día 15: E→I (contador alcanza 5, ahora infectado)
    - Día 15-20: I (contador infección=1,2,3,4,5,6)
    - Día 21: I→R (recuperada, inmune)
    - Día 221 (200 días después): Probabilidad 0.5%×200≈63% de volver a S
```

#### **9. Recolección de Datos** 📊
```
Acción: Guardar estado actual para análisis posterior

Registrar en CSV:
  - Día simulación
  - Conteos SEIR humanos: S_count, E_count, I_count, R_count
  - Conteos SI mosquitos: S_m_total, E_m_total, I_m_total
  - Total huevos y huevos infectados
  - Clima: Temperatura, Precipitación
  - Sitios de cría activos
  - Estrategias de control activas

Ejemplo fila CSV:
  día,S,E,I,R,Sm,Em,Im,huevos,huevos_inf,temp,precip,charcos,LSM,ITN
  50,9950,30,15,5,12000,800,200,45000,2250,23.5,12.0,25,True,False
```

#### **10. Verificación de Fin** 🏁
```
Acción: Comprobar si terminó la simulación

SI día_actual >= días_totales (200):
  - Generar resumen estadístico
  - Crear gráficas
  - Guardar archivos finales
  - TERMINAR simulación

SINO:
  - Volver al paso 1 (siguiente día)
```

### Visualización del Ciclo Completo

```
┌─────────────────────── DÍA N ───────────────────────┐
│                                                      │
│  [1] Clima ──→ 23°C, 15mm                          │
│       ↓                                              │
│  [2] Charcos ──→ Crear 7 nuevos, secar 3 viejos    │
│       ↓                                              │
│  [3] Huevos ──→ 50 lotes eclosionan → +500 mosquitos│
│       ↓                                              │
│  [4] Mortalidad huevos ──→ 200 huevos mueren        │
│       ↓                                              │
│  [5] Mosquitos ──→ Mortalidad 5%, 20 E→I, 100 ponen │
│       ↓                                              │
│  [6] Control ──→ LSM elimina 5000 huevos            │
│       ↓                                              │
│  [7] Humanos ──→ 10000 se mueven, 5 se infectan     │
│       ↓                                              │
│  [8] Estados ──→ 3 E→I, 2 I→R, 1 R→S               │
│       ↓                                              │
│  [9] Guardar ──→ CSV, estadísticas                  │
│       ↓                                              │
│  [10] ¿Fin? ──→ No → Siguiente día                 │
│                                                      │
└──────────────────────────────────────────────────────┘
         │
         └──→ Repetir hasta día 200
```

---

## Modelo Metapoblacional de Mosquitos

### ¿Por qué Metapoblacional?

#### El Problema de Modelar Mosquitos Individualmente

Imagina que cada mosquito fuera un agente individual en el modelo:

```
Mosquito #1: Ubicación (25,30), Estado: Infectado, Edad: 12 días, ...
Mosquito #2: Ubicación (25,30), Estado: Susceptible, Edad: 5 días, ...
Mosquito #3: Ubicación (25,31), Estado: Expuesto, Edad: 8 días, ...
...
Mosquito #100,000: Ubicación (40,15), Estado: Infectado, Edad: 3 días, ...
```

**Problemas**:
- **Memoria**: 100,000 mosquitos × 50 bytes/mosquito = 5 MB solo para almacenar
- **Procesamiento**: Iterar 100,000 mosquitos cada día × 200 días = 20 millones de iteraciones
- **Complejidad**: Código más difícil de mantener y debuggear
- **Tiempo**: Simulación tomaría horas en lugar de minutos

#### La Solución: Agrupar por Ubicación y Estado

En lugar de rastrear cada mosquito, contamos **cuántos mosquitos de cada tipo hay en cada celda**:

```
Celda (25,30):
  - Mosquitos Susceptibles (S_m): 150
  - Mosquitos Expuestos (E_m): 30
  - Mosquitos Infecciosos (I_m): 20
  Total en esta celda: 200

Celda (25,31):
  - S_m: 80
  - E_m: 15
  - I_m: 5
  Total: 100
```

**Ventajas**:
- **Memoria**: 2,500 celdas × 3 contadores × 4 bytes = 30 KB (¡166× menos!)
- **Procesamiento**: 2,500 celdas × 200 días = 500,000 iteraciones (¡40× menos!)
- **Velocidad**: Simulación completa en 5-10 minutos
- **Suficiente**: Para dengue, no necesitamos identidad individual de mosquitos

### Estructura de Datos

#### Tres Arrays Numpy 2D (50×50)

```python
# Matriz de mosquitos Susceptibles
S_m = numpy.array([
    [10, 5, 8, ..., 12],    # Fila 0 (y=0)
    [7, 15, 3, ..., 9],     # Fila 1 (y=1)
    ...,
    [11, 6, 14, ..., 8]     # Fila 49 (y=49)
])  # 50 filas × 50 columnas

# Similar para E_m (Expuestos) e I_m (Infecciosos)
```

#### Acceso a una Celda Específica

```python
# ¿Cuántos mosquitos infectados hay en celda (25,30)?
infectados_en_celda = I_m[30, 25]  # Nota: [fila, columna] = [y, x]

# Agregar 10 mosquitos susceptibles a celda (10,15)
S_m[15, 10] += 10

# Mover 5 mosquitos de E→I en celda (20,20)
E_m[20, 20] -= 5
I_m[20, 20] += 5
```

### Ciclo de Vida del Mosquito (Explicado Paso a Paso)

---

#### **FASE 1: Etapa de Huevo** 🥚

Los huevos NO están en el grid metapoblacional. Se gestionan en un sistema separado (`EggManager`) porque necesitan:
- Rastrear **ubicación exacta** del sitio de cría
- Acumular **grados-día** individualmente
- Saber si están **infectados** (transmisión vertical)

##### Modelo de Grados-Día Acumulados (GDD)

Este es un modelo biológico que dice: **"El desarrollo de insectos depende del calor acumulado, no solo del tiempo"**

**Fórmula Básica**:
```
GD_día = max(Temperatura - T_base, 0)

Donde:
  - GD_día = Grados-día acumulados HOY
  - Temperatura = Temperatura promedio del día (°C)
  - T_base = 8.3°C (umbral mínimo para desarrollo de Aedes aegypti)
  - max(..., 0) = Si temperatura < 8.3°C, entonces GD_día = 0
```

**Constante Térmica**: K = 181.2 °C·día
- Cuando acumulado alcanza 181.2, el huevo eclosiona

**Ejemplo Detallado - Desarrollo de un Lote de Huevos**:

```
Lote depositado el Día 1 en un charco de la celda (25,25)
Cantidad: 100 huevos (5 infectados por transmisión vertical)

DÍA 1 - Temperatura: 25°C
  GD_día = max(25 - 8.3, 0) = 16.7
  Acumulado = 0 + 16.7 = 16.7
  ¿Eclosiona? No (16.7 < 181.2)

DÍA 2 - Temperatura: 26°C
  GD_día = max(26 - 8.3, 0) = 17.7
  Acumulado = 16.7 + 17.7 = 34.4
  ¿Eclosiona? No (34.4 < 181.2)

DÍA 3 - Temperatura: 24°C
  GD_día = max(24 - 8.3, 0) = 15.7
  Acumulado = 34.4 + 15.7 = 50.1
  ¿Eclosiona? No

DÍA 4 - Temperatura: 27°C
  GD_día = max(27 - 8.3, 0) = 18.7
  Acumulado = 50.1 + 18.7 = 68.8
  ¿Eclosiona? No

DÍA 5 - Temperatura: 25°C
  GD_día = 16.7
  Acumulado = 68.8 + 16.7 = 85.5
  ¿Eclosiona? No

DÍA 6 - Temperatura: 26°C
  GD_día = 17.7
  Acumulado = 85.5 + 17.7 = 103.2
  ¿Eclosiona? No

DÍA 7 - Temperatura: 25°C
  GD_día = 16.7
  Acumulado = 103.2 + 16.7 = 119.9
  ¿Eclosiona? No

DÍA 8 - Temperatura: 24°C
  GD_día = 15.7
  Acumulado = 119.9 + 15.7 = 135.6
  ¿Eclosiona? No

DÍA 9 - Temperatura: 25°C
  GD_día = 16.7
  Acumulado = 135.6 + 16.7 = 152.3
  ¿Eclosiona? No

DÍA 10 - Temperatura: 26°C
  GD_día = 17.7
  Acumulado = 152.3 + 17.7 = 170.0
  ¿Eclosiona? No (casi!)

DÍA 11 - Temperatura: 25°C
  GD_día = 16.7
  Acumulado = 170.0 + 16.7 = 186.7
  ¿Eclosiona? ¡SÍ! (186.7 >= 181.2)
  
  → ECLOSIÓN:
    - 95 huevos sanos → Agregar S_m[25,25] += 95
    - 5 huevos infectados → Agregar I_m[25,25] += 5
    - Lote eliminado del EggManager
```

**Efecto de la Temperatura en Tiempo de Eclosión**:

```
Temperatura Constante → GD por día → Días hasta eclosión

  15°C → 6.7 °C/día → 181.2 ÷ 6.7 ≈ 27 días
  20°C → 11.7 °C/día → 181.2 ÷ 11.7 ≈ 15 días
  25°C → 16.7 °C/día → 181.2 ÷ 16.7 ≈ 11 días
  30°C → 21.7 °C/día → 181.2 ÷ 21.7 ≈ 8 días
  35°C → 26.7 °C/día → 181.2 ÷ 26.7 ≈ 7 días

Conclusión: A mayor temperatura, más rápido se desarrollan los huevos
```

##### Transmisión Vertical (Madre→Huevo)

Cuando una hembra **INFECTADA** pone huevos, algunos heredan el virus:

```python
hembra_infectada = True
huevos_totales = 100
tasa_vertical = 5%  # 0.05

huevos_infectados = 100 × 0.05 = 5 huevos
huevos_sanos = 100 - 5 = 95 huevos

# Al eclosionar:
# - 5 huevos → Mosquitos I_m (ya nacen INFECCIOSOS, saltan estado E)
# - 95 huevos → Mosquitos S_m (nacen susceptibles)
```

**Importancia biológica**: 
- Permite que el virus persista incluso si todos los mosquitos adultos mueren
- Los huevos pueden sobrevivir meses secos y eclosionar cuando llueve
- Mantiene el virus "latente" en la población

---

#### **FASE 2: Eclosión y Emergencia** 🥚➡️🦟

Cuando un lote alcanza K = 181.2 °C·día:

```python
# Antes de eclosión
lote = {
    'ubicacion': (25, 25),
    'cantidad_sanos': 95,
    'cantidad_infectados': 5,
    'grados_acumulados': 186.7  # >= 181.2
}

# Grid ANTES:
S_m[25, 25] = 200
E_m[25, 25] = 50
I_m[25, 25] = 30

# PROCESO DE ECLOSIÓN:
1. Crear mosquitos sanos:
   S_m[25, 25] += 95  # Ahora 295

2. Crear mosquitos infectados:
   I_m[25, 25] += 5   # Ahora 35
   # Nota: NO van a E_m porque heredaron virus (ya son infecciosos)

3. Eliminar lote del EggManager

# Grid DESPUÉS:
S_m[25, 25] = 295  (+95)
E_m[25, 25] = 50   (sin cambio)
I_m[25, 25] = 35   (+5)
```

---

#### **FASE 3: Dinámica de Adultos** 🦟

Cada día se procesa CADA celda del grid (2,500 celdas):

##### **A) Mortalidad Diaria**

**Tasa Base**: 5% mueren cada día → Esperanza de vida = 1/0.05 = 20 días

```python
# Ejemplo en celda (30,20)
# Estado inicial:
S_m[20, 30] = 100
E_m[20, 30] = 40
I_m[20, 30] = 10

# Temperatura hoy: 25°C (óptimo) → Multiplicador = 1.0
# Tasa efectiva = 5% × 1.0 = 5%

# Proceso estocástico (aleatorio):
muertos_S = Binomial(n=100, p=0.05)  # Lanzar 100 monedas con 5% de morir
# Resultado (ejemplo): muertos_S = 6

muertos_E = Binomial(n=40, p=0.05) = 2
muertos_I = Binomial(n=10, p=0.05) = 1

# Actualizar poblaciones:
S_m[20, 30] = 100 - 6 = 94
E_m[20, 30] = 40 - 2 = 38
I_m[20, 30] = 10 - 1 = 9
```

**Modificadores Climáticos** (ver tabla detallada más abajo):

```
Temperatura    Multiplicador    Tasa Efectiva    Esperanza Vida
-----------------------------------------------------------------
5°C (extremo)      × 2.5          12.5%          8 días
12°C (subópt)      × 1.5          7.5%           13 días
25°C (óptimo)      × 1.0          5.0%           20 días
37°C (subópt)      × 1.5          7.5%           13 días
42°C (extremo)     × 2.5          12.5%          8 días
```

##### **B) Incubación Extrínseca (E→I)**

Los mosquitos **Expuestos** tienen el virus pero aún no lo pueden transmitir. Necesitan un **Período de Incubación Extrínseca (EIP)** para que el virus se replique en sus glándulas salivales.

```python
# Celda (15,10)
E_m[10, 15] = 60  # 60 mosquitos expuestos

# Temperatura hoy: 28°C (cálido) → EIP = 10 × 0.7 = 7 días

# Probabilidad diaria de completar incubación:
p = 1 / 7 ≈ 0.143 (14.3%)

# Cuántos completan incubación HOY:
nuevos_infecciosos = Binomial(60, 0.143)  # ≈ 8-9 mosquitos

# Actualizar:
E_m[10, 15] = 60 - 9 = 51
I_m[10, 15] += 9
```

**Tabla de EIP según Temperatura**:

```
Temp     Multiplicador   EIP Efectivo   Prob. Diaria   Días Promedio
-----------------------------------------------------------------------
18°C         × 2.0         20 días         5%           20 días
22°C         × 1.5         15 días         6.7%         15 días
26°C         × 1.0         10 días         10%          10 días
32°C         × 0.7         7 días          14.3%        7 días

Biología: Virus se replica más rápido a temperaturas altas
```

##### **C) Reproducción**

Solo mosquitos **HEMBRA** (el modelo solo simula hembras, los machos son implícitos en la probabilidad de apareamiento).

**Requisitos para Reproducir** (todos deben cumplirse):

```
1. ✓ Es hembra (todas en el modelo lo son)
2. ✓ Ha picado un humano (obtener proteína de sangre)
3. ✓ Se ha apareado (probabilidad 60%)
4. ✓ Pasó ciclo gonotrófico (3 días desde última puesta)
5. ✓ Hay sitio de cría cercano (radio 5 celdas)
```

**Proceso Detallado**:

```python
# Mosquito hembra en celda (20,20)
# Asumiendo cumple todos los requisitos:

1. DETERMINAR CANTIDAD DE HUEVOS:
   huevos_totales = 100  # Fecundidad típica de Aedes aegypti
   
2. SOLO HEMBRAS (sexo 50/50):
   huevos_hembra = 100 × 0.5 = 50
   huevos_macho = 50 (estos se descartan, no se modelan)

3. TRANSMISIÓN VERTICAL (si madre infectada):
   if madre.estado == INFECTADO:
       tasa_vertical = 5%  # 0.05
       huevos_infectados = 50 × 0.05 = 2.5 ≈ 3
       huevos_sanos = 50 - 3 = 47
   else:
       huevos_infectados = 0
       huevos_sanos = 50

4. BUSCAR SITIO DE CRÍA:
   # Buscar en radio 5 celdas desde (20,20)
   sitios_disponibles = [
       (20,21) - Charco temporal,
       (22,19) - Celda AGUA permanente,
       ...
   ]
   
   sitio_elegido = aleatorio(sitios_disponibles)

5. DEPOSITAR HUEVOS:
   egg_manager.add_eggs(
       sitio = sitio_elegido,
       cantidad_sanos = 47,
       cantidad_infectados = 3,
       grados_acumulados = 0  # Empiezan en 0
   )

6. COOLDOWN:
   mosquito.dias_desde_puesta = 0  # Reset ciclo gonotrófico
   # No podrá poner huevos por 3 días más
```

**Ejemplo Numérico - 10 Hembras Reproducen**:

```
Celda (25,25): 10 mosquitos infectados listos para poner

ANTES:
  - Mosquitos I_m[25,25] = 10
  - Huevos en charco cercano = 0

REPRODUCCIÓN:
  Hembra 1: 50 huevos (3 infectados) → Charco A
  Hembra 2: 50 huevos (2 infectados) → Charco A
  Hembra 3: 50 huevos (3 infectados) → Charco B
  ...
  Hembra 10: 50 huevos (2 infectados) → Charco C

DESPUÉS:
  - Mosquitos I_m[25,25] = 10 (sin cambio, siguen vivos)
  - Huevos totales depositados = 10 × 50 = 500
  - Huevos infectados = 10 × 2.5 = 25
  - Distribuidos en ~3 charcos cercanos
  - Eclosionarán en 8-15 días según temperatura
```

---

### Sitios de Cría (Breeding Sites)

Los mosquitos Aedes aegypti necesitan agua estancada para depositar huevos. El modelo simula dos tipos:

#### **Sitios Permanentes (Celdas AGUA)**

```
Configuración inicial del grid:

  5% de celdas = AGUA
  50×50 grid → 2500 celdas → 125 celdas de AGUA

Características:
  - Zonas de 2×2 hasta 4×4 celdas contiguas
  - Simulan: Ríos, lagos, estanques permanentes
  - Siempre disponibles para oviposición
  - No se secan nunca

Ejemplo visual (fragmento del grid):

  [ ][ ][ ][ ][ ]
  [ ][W][W][ ][ ]    W = AGUA (sitio permanente)
  [ ][W][W][ ][ ]    [ ] = URBANO
  [ ][ ][ ][ ][ ]
  [ ][ ][ ][ ][W]
```

#### **Sitios Temporales (Charcos Post-Lluvia)**

Estos se crean y destruyen dinámicamente según la lluvia:

```python
# Cada día se ejecuta:

if precipitacion >= 5.0 mm:
    # Crear charcos nuevos
    num_charcos = int(precipitacion × 0.5)
    
    for i in range(num_charcos):
        posicion = celda_aleatoria_urbana()  # No en AGUA
        charcos_temporales[posicion] = {
            'dias_restantes': 7,
            'creado_dia': dia_actual
        }

# Ejemplo lluvia 24mm:
num_charcos = int(24 × 0.5) = 12 charcos nuevos
Duración: 7 días cada uno
```

**Lógica de Persistencia**:

```
DÍA 1: Llueve 30mm
  → Crear 15 charcos (posiciones aleatorias)
  → Cada charco: dias_restantes = 7

DÍA 2: No llueve
  → TODOS los charcos: dias_restantes -= 1  (ahora 6)

DÍA 3: Llueve 10mm
  → Crear 5 charcos nuevos (dias_restantes = 7)
  → Charcos del Día 1: dias_restantes -= 1  (ahora 5)

DÍA 4: No llueve
  → Charcos Día 1: dias_restantes = 4
  → Charcos Día 3: dias_restantes = 6

...

DÍA 8: No llueve
  → Charcos Día 1: dias_restantes = 0 → ELIMINADOS (secados)
  → Charcos Día 3: dias_restantes = 4 (aún disponibles)

Si llueve nuevamente en un charco existente:
  → dias_restantes se RENUEVA a 7 (como si fuera nuevo)
```

#### **Inserción de Mosquitos por Lluvia Fuerte** (≥15mm)

Simula la **eclosión masiva de huevos latentes** que estaban en diapausa:

```python
if precipitacion >= 15.0 mm:
    # Fórmula:
    factor = (precipitacion - 15.0) / 8.0
    base = num_charcos_creados × factor × 0.93
    infectados_nuevos = min(int(base), 100)  # Límite 100
    
    # Distribuir mosquitos infectados en charcos nuevos
    for charco in charcos_nuevos:
        I_m[charco.x, charco.y] += infectados_nuevos // len(charcos_nuevos)
```

**Ejemplos Numéricos**:

```
Caso 1: Lluvia 20mm
  charcos = 20 × 0.5 = 10
  factor = (20 - 15) / 8 = 0.625
  base = 10 × 0.625 × 0.93 = 5.8
  infectados = min(5, 100) = 5 mosquitos I_m
  
Caso 2: Lluvia 50mm
  charcos = 50 × 0.5 = 25
  factor = (50 - 15) / 8 = 4.375
  base = 25 × 4.375 × 0.93 = 101.7
  infectados = min(101, 100) = 100 mosquitos I_m (límite)
  
Caso 3: Lluvia 80mm (tormenta fuerte)
  charcos = 80 × 0.5 = 40
  factor = (80 - 15) / 8 = 8.125
  base = 40 × 8.125 × 0.93 = 302.6
  infectados = min(302, 100) = 100 mosquitos I_m (límite)

Conclusión: Lluvias >50mm siempre inyectan 100 mosquitos infectados
```

**Justificación Biológica**:
- Huevos de Aedes pueden sobrevivir MESES secos
- Lluvia fuerte "activa" eclosión simultánea de miles de huevos
- Simula brotes post-tormenta observados en campo
- Explica picos de dengue 2-3 semanas después de lluvias intensas

---

## Población Humana

### Estados Epidemiológicos (SEIR)

```
S (Susceptible) --[picadura infectada]--> E (Expuesto)
E --[incubación 5 días]--> I (Infectado)
I --[recuperación 6 días]--> R (Recuperado)
R --[pérdida inmunidad 0.5%]--> S (ciclo)
```

**Parámetros**:
- **Período de incubación**: 5 días (promedio)
- **Período infeccioso**: 6 días (promedio)
- **Pérdida de inmunidad**: 0.5% diario (R → S, para dengue homólogo)

### Tipos de Movilidad
Cada humano tiene un patrón de movilidad que determina su exposición:

| Tipo | Proporción | Destino Hogar | Destino Trabajo/Escuela | Parque | Aleatorio |
|------|-----------|---------------|------------------------|--------|-----------|
| **Estudiante** | 30% | 55% | 35% | 10% | 0% |
| **Trabajador** | 40% | 60% | 35% | 5% | 0% |
| **Móvil Continuo** | 20% | 40% | 0% | 20% | 40% |
| **Estacionario** | 10% | 95% | 0% | 5% | 0% |

**Comportamiento especial para infectados**:
- 70% se aíslan en casa (movilidad reducida)
- 30% continúan moviéndose pero con radio reducido (1 celda)

### Interacción con Mosquitos
Cada día, en la celda actual del humano:

1. **Contar mosquitos locales**: `I_m[x,y]` (infecciosos)
2. **Modificador climático de actividad**:
   ```python
   if precipitacion > 10 mm: actividad × 0.6
   if precipitacion > 20 mm: actividad × 0.3
   ```
3. **Intentos de picadura**: Binomial(n=I_m, p=bite_rate × actividad)
4. **Transmisión mosquito→humano** (si humano es S):
   ```python
   prob_transmision = mosquito_to_human_prob (60%)
   if random() < prob_transmision: S → E
   ```
5. **Transmisión humano→mosquito** (si humano es I):
   ```python
   prob_transmision = human_to_mosquito_prob (27.5%)
   mosquitos_infectados = Binomial(n=picaduras, p=27.5%)
   S_m[x,y] -= mosquitos_infectados
   E_m[x,y] += mosquitos_infectados
   ```

---

## Efectos Climáticos

### 1. Mortalidad de Mosquitos Adultos

| Rango de Temperatura | Multiplicador | Explicación |
|---------------------|---------------|-------------|
| < 10°C (extremo frío) | × 2.5 | Torpor térmico, parálisis |
| 10-15°C (subóptimo frío) | × 1.5 | Metabolismo lento |
| 25-30°C (óptimo) | × 1.0 | Rango ideal para *Aedes aegypti* |
| 35-40°C (subóptimo calor) | × 1.5 | Estrés térmico |
| > 40°C (extremo calor) | × 2.5 | Deshidratación, muerte celular |

### 2. Mortalidad de Huevos

Aplicada diariamente sobre todos los lotes:

| Condición | Tasa de Mortalidad | Umbral |
|-----------|-------------------|---------|
| Extremo frío | 90% | < 10°C |
| Extremo calor | 80% | > 40°C |
| Subóptimo (frío o calor) | 50% | 10-15°C o 35-40°C |
| Óptimo | 0% | 25-30°C |

### 3. Desarrollo de Huevos (GDD)

```python
# Contribución diaria
grados_dia = max(T - 8.3, 0)

# Acumulación
batch.grados_acumulados += grados_dia

# Eclosión cuando:
if batch.grados_acumulados >= 181.2:
    eclosionar(batch)
```

**Impacto de temperatura variable**:
- **Días fríos** (15°C): solo 6.7°C/día → desarrollo más lento
- **Días cálidos** (30°C): 21.7°C/día → desarrollo rápido
- **Días extremos** (<8.3°C): 0°C/día → desarrollo detenido

### 4. Período de Incubación Extrínseca (EIP)

```python
EIP_base = 10 días

if T < 20°C:
    EIP = 10 × 2.0 = 20 días
elif 20 <= T < 25°C:
    EIP = 10 × 1.5 = 15 días
elif T > 30°C:
    EIP = 10 × 0.7 = 7 días
else:
    EIP = 10 días
```

**Consecuencia**: Temperaturas altas aceleran el ciclo de transmisión (mosquitos infecciosos más rápido).

### 5. Actividad de Mosquitos por Lluvia

Reduce la actividad de picadura durante precipitación fuerte:

```python
if precipitacion > 20 mm:
    actividad_mosquitos = 0.3  # Solo 30% activos
elif precipitacion > 10 mm:
    actividad_mosquitos = 0.6  # 60% activos
else:
    actividad_mosquitos = 1.0  # 100% activos
```

### 6. Creación de Sitios de Cría por Lluvia

```python
if precipitacion >= 5.0 mm:
    num_charcos = int(precipitacion × 0.5)
    # Ejemplo: 12mm → 6 charcos
    # Ejemplo: 30mm → 15 charcos
    
    for charco in range(num_charcos):
        posicion = aleatoria()
        duracion = 7 días
        sitios_cria_temporales[posicion] = duracion
```

### 7. Efectos de Sequía (Acumulado 7 Días)

```python
precipitacion_7dias = sum(ultimos_7_dias)

if precipitacion_7dias < 10 mm:  # Sequía severa
    # Sitios de cría se secan más rápido
    for charco in sitios_temporales:
        charco.duracion -= 1  # Doble decremento
elif precipitacion_7dias < 25 mm:  # Sequía moderada
    # Mortalidad de huevos aumenta 20%
    egg_manager.apply_mortality(0.20)
```

---

## Estrategias de Control

### LSM (Larval Source Management) - Control Larvario

**Objetivo**: Eliminar huevos antes de que eclosionen

**Parámetros**:
- **Frecuencia**: Cada 7 días (configurable)
- **Cobertura**: 70% de sitios de cría visitados
- **Efectividad**: 80% de huevos eliminados en sitios visitados

**Algoritmo**:
```python
if dia_simulacion % 7 == 0:  # Aplicar LSM semanalmente
    for sitio in sitios_cria:
        if random() < 0.70:  # 70% cobertura
            huevos_en_sitio = egg_manager.get_eggs_at(sitio)
            huevos_eliminados = Binomial(n=huevos_en_sitio, p=0.80)
            egg_manager.remove_eggs(sitio, huevos_eliminados)
```

**Efecto neto**: 70% × 80% = 56% de reducción semanal en huevos

**Realismo biológico**: Simula:
- Eliminación de recipientes con agua estancada
- Limpieza de canaletas y alcantarillas
- Tratamiento con larvicidas (Bti, temefos)

### ITN/IRS (Insecticide-Treated Nets / Indoor Residual Spraying)

**Objetivo**: Reducir picaduras y matar mosquitos adultos

**Parámetros**:
- **Duración**: 90 días (efectividad del insecticida)
- **Cobertura**: 60% de hogares protegidos
- **Efectividad barrera**: 70% reducción de picaduras
- **Mortalidad adicional**: 20% diario para mosquitos en hogares tratados

**Algoritmo**:
```python
if itn_irs_activo:
    for celda_hogar in celdas_con_hogares:
        if random() < 0.60:  # 60% hogares cubiertos
            # Reducir picaduras
            bite_rate_efectivo = bite_rate × (1 - 0.70)
            
            # Aumentar mortalidad
            mortality_rate_efectivo = mortality_rate + 0.20
            
            mosquitos_muertos_extra = Binomial(
                n=mosquitos_en_celda, 
                p=0.20
            )
            mosquitos_totales -= mosquitos_muertos_extra
```

**Efectos combinados**:
1. **Barrera física/química**: 70% menos picaduras → 70% menos transmisión
2. **Mortalidad adulticida**: 20% muerte adicional → reduce población vectorial
3. **Duración limitada**: Efecto decae después de 90 días (requiere reaplicación)

**Realismo biológico**: Simula:
- Mosquiteros impregnados con permetrina/deltametrina
- Fumigación residual intradomiciliaria
- Decaimiento de eficacia por lavado/degradación del insecticida

### Comparación de Estrategias

| Aspecto | LSM | ITN/IRS |
|---------|-----|---------|
| **Fase del vector** | Inmadura (huevos) | Adulta (mosquitos) |
| **Velocidad de efecto** | Lenta (10-14 días) | Rápida (inmediata) |
| **Sostenibilidad** | Alta (no genera resistencia) | Media (resistencia posible) |
| **Cobertura espacial** | Focal (sitios de cría) | Domiciliaria (hogares) |
| **Costo relativo** | Bajo | Alto |
| **Intensidad de trabajo** | Alta (búsqueda activa) | Media (aplicación focalizada) |

---

## Transmisión del Virus

### Ciclo de Transmisión

```
Humano Infectado (I) --[picadura]--> Mosquito Susceptible (S_m)
     ↑                                         ↓
     |                                   [EIP: 7-20 días]
     |                                         ↓
     |                              Mosquito Infeccioso (I_m)
     |                                         ↓
     +---------[picadura]------------- Humano Susceptible (S)
                                               ↓
                                         [incubación: 5 días]
                                               ↓
                                        Humano Expuesto (E)
```

### Probabilidades de Transmisión

#### Mosquito → Humano (α = 60%)
```python
if humano.estado == SUSCEPTIBLE and mosquitos_infectados > 0:
    picaduras = Binomial(n=mosquitos_infectados, p=bite_rate)
    for picadura in range(picaduras):
        if random() < 0.60:  # 60% probabilidad
            humano.estado = EXPUESTO
            humano.dias_incubacion = 5
            break  # Solo una infección por día
```

**Factores que modulan α**:
- Temperatura óptima (26°C): α máximo
- Temperatura fría/calor: α reducido
- ITN/IRS activo: α × 0.3

#### Humano → Mosquito (β = 27.5%)
```python
if humano.estado == INFECTADO and mosquitos_susceptibles > 0:
    picaduras = Binomial(n=mosquitos_susceptibles, p=bite_rate)
    infectados = Binomial(n=picaduras, p=0.275)  # 27.5% éxito
    
    S_m[x,y] -= infectados
    E_m[x,y] += infectados  # Inician incubación extrínseca
```

**Factores que modulan β**:
- Carga viral del humano (días de infección)
- Temperatura óptima (26°C): β máximo
- Lluvia intensa: β reducido (menos picaduras)

### Tasa Básica de Reproducción (R₀)

Aproximación según parámetros del modelo:

```
R₀ = (m × a² × b × c × v) / (μ × r)

Donde:
m = densidad mosquitos/humano (~10-50 en simulación)
a = tasa de picadura (0.33/día)
b = prob. transmisión mosquito→humano (0.60)
c = prob. transmisión humano→mosquito (0.275)
v = duración período infeccioso humano (6 días)
μ = tasa mortalidad mosquito (0.05/día → vida ~20 días)
r = tasa recuperación humana (1/6 = 0.167/día)
```

**Estimación**:
```
R₀ = (20 × 0.33² × 0.60 × 0.275 × 6) / (0.05 × 0.167)
R₀ ≈ (20 × 0.109 × 0.165 × 6) / 0.00835
R₀ ≈ 2.16 / 0.00835 ≈ 2.6
```

**Interpretación**: Cada humano infectado genera ~2.6 casos secundarios (sin control).

---

## Referencias Científicas

### Modelo Base
1. **Jindal, A., & Rao, S. (2017)**. "Agent-based modeling of mosquito-borne disease transmission". En *Modeling and Simulation of Complex Systems* (pp. 243-267).

### Biología de *Aedes aegypti*
2. **Tun-Lin, W., Burkot, T. R., & Kay, B. H. (1999)**. "Effects of temperature and larval diet on development rates and survival of the dengue vector *Aedes aegypti* in north Queensland, Australia". *Medical and Veterinary Entomology*, 14(1), 31-37.

3. **Scott, T. W., Amerasinghe, P. H., Morrison, A. C., et al. (1993)**. "Longitudinal studies of *Aedes aegypti* (Diptera: Culicidae) in Thailand and Puerto Rico: blood feeding frequency". *Journal of Medical Entomology*, 30(5), 859-865.

### Efectos Climáticos
4. **Mordecai, E. A., Cohen, J. M., Evans, M. V., et al. (2017)**. "Detecting the impact of temperature on transmission of Zika, dengue, and chikungunya using mechanistic models". *PLoS Neglected Tropical Diseases*, 11(4), e0005568.

5. **Alto, B. W., & Bettinardi, D. (2013)**. "Temperature and dengue virus infection in mosquitoes: Independent effects on the immature and adult stages". *The American Journal of Tropical Medicine and Hygiene*, 88(3), 497-505.

### Transmisión Vertical
6. **Gunay, F., Alten, B., & Ozsoy, E. D. (2010)**. "Estimating reaction norms for predictive population modeling: *Aedes albopictus* in Europe responds to photoperiod and temperature". *Journal of Vector Ecology*, 35(2), 344-354.

7. **Thavara, U., Tawatsin, A., Pengsakul, T., et al. (2006)**. "Outbreak of chikungunya fever in Thailand and virus detection in field population of vector mosquitoes, *Aedes aegypti* (L.) and *Aedes albopictus* Skuse (Diptera: Culicidae)". *Southeast Asian Journal of Tropical Medicine and Public Health*, 37(3), 437.

### Estrategias de Control
8. **Wilson, A. L., Courtenay, O., Kelly-Hope, L. A., et al. (2020)**. "The importance of vector control for the control and elimination of vector-borne diseases". *PLoS Neglected Tropical Diseases*, 14(1), e0007831.

9. **Bowman, L. R., Donegan, S., & McCall, P. J. (2016)**. "Is dengue vector control deficient in effectiveness or evidence?: Systematic review and meta-analysis". *PLoS Neglected Tropical Diseases*, 10(3), e0004551.

### Modelos Metapoblacionales
10. **Keeling, M. J., & Rohani, P. (2008)**. *Modeling Infectious Diseases in Humans and Animals*. Princeton University Press.

---

## Resumen Ejecutivo

Este modelo ABM captura la complejidad de la transmisión de dengue mediante:

1. **Realismo biológico**: Parámetros calibrados desde literatura científica
2. **Heterogeneidad espacial**: Grid urbano con parques, agua y hogares
3. **Variabilidad temporal**: Datos climáticos reales diarios desde CSV
4. **Eficiencia computacional**: Modelo metapoblacional (2,500 celdas vs 100,000+ agentes)
5. **Intervenciones realistas**: LSM y ITN/IRS con parámetros validados

**Aplicaciones**:
- Evaluación de estrategias de control (comparación LSM vs ITN/IRS)
- Predicción de brotes según clima (temporada lluviosa = alta transmisión)
- Análisis de sensibilidad (¿qué parámetro tiene mayor impacto?)
- Optimización de recursos (¿cuándo y dónde aplicar control?)
- Educación en salud pública (visualización de dinámica de transmisión)
