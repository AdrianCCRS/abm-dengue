# Parámetros del Modelo ABM-Dengue (Jindal & Rao 2017)

## Extracción desde el análisis LaTeX

Este documento consolida todos los parámetros, fórmulas y valores del modelo ABM del dengue basado en Jindal & Rao (2017) adaptado para Bucaramanga.

---

## 1. Parámetros del Agente Mosquito

| Atributo | Símbolo | Valor | Descripción |
|----------|---------|-------|-------------|
| **Velocidad de vuelo** | `Fs` | 0.0–1.0 km/h | Velocidad promedio de desplazamiento |
| **Distancia máxima** | `Fr` | 350 m | Distancia máxima de vuelo diario |
| **Período activo** | `As, Ae` | 07:00–18:00 | Horas de actividad diaria |
| **Máx. picaduras/día** | `Mm` | 1 | Número máximo de comidas por día |
| **Tasa de mortalidad** | `Mr` | 0.05 /día | Probabilidad diaria de muerte |
| **Prob. apareamiento** | `Pm` | 0.6 | Probabilidad de reproducción exitosa |
| **Proporción hembras** | `Pf` | 0.5 | Proporción de mosquitos hembras |
| **Rango sensorial** | `Sr` | 3 m | Radio de detección de humanos |
| **Huevos por puesta** | — | 100 | Huevos depositados por hembra |

### Fórmulas Dependientes de Temperatura

**Tiempo de maduración de huevos:**
```
τ = 3 + |θ - 21| / 5  (días)
```
donde `θ` = temperatura en °C

**Tiempo de desarrollo huevo→adulto:**
```
μ = 8 + |θ - 25|  (días)
```

### Estados del Mosquito
- **S (Susceptible):** puede infectarse al picar humano infectado
- **I (Infectado):** puede transmitir virus a humanos susceptibles
- No hay recuperación: permanecen infectados hasta morir

---

## 2. Parámetros del Agente Humano

| Atributo | Símbolo | Valor | Descripción |
|----------|---------|-------|-------------|
| **Período incubación** | `Ne` | 5 días | Duración del estado Expuesto (E) |
| **Período infeccioso** | `Ni` | 6 días | Duración del estado Infectado (I) |
| **Prob. infección crónica** | `Pirc` | 0.95 | Prob. de infección crónica |
| **Prob. R→S** | `Prc` | 0.0 | Prob. de volver a ser susceptible |
| **Prob. visita parque (estudiantes)** | `Pp1` | 0.3 | Tipo 1 - Estudiantes |
| **Prob. visita parque (trabajadores)** | `Pp2` | 0.1 | Tipo 2 - Trabajadores |

### Estados SEIR del Humano
- **S (Susceptible):** vulnerable a infección
- **E (Expuesto):** infectado pero no contagioso (período de incubación)
- **I (Infectado):** sintomático y contagioso, permanece en casa
- **R (Recuperado):** inmune (temporal o permanente)

### Tipos de Movilidad Humana

1. **Tipo 1 - Estudiantes:**
   - Hogar → Escuela (7:00 AM)
   - Escuela → Hogar (3:00 PM)
   - Posible visita a parque (4:00 PM - 7:00 PM) con prob. `Pp1 = 0.3`

2. **Tipo 2 - Trabajadores:**
   - Hogar → Oficina (7:00 AM)
   - Oficina → Hogar (variado)
   - Posible visita a parque con prob. `Pp2 = 0.1`

3. **Tipo 3 - Móviles continuos:**
   - Movimiento constante durante el día
   - Cambio de ubicación cada 2 horas
   - Regreso a hogar (7:00 PM)

4. **Tipo 4 - Estacionarios:**
   - Permanecen en hogar todo el día
   - Baja movilidad (adultos mayores, amas de casa)

---

## 3. Parámetros de Transmisión

| Evento | Dirección | Probabilidad | Descripción |
|--------|-----------|--------------|-------------|
| **Infección M→H** | Mosquito (I) → Humano (S) | `α = 0.6` | Prob. transmisión en picadura |
| **Infección H→M** | Humano (I) → Mosquito (S) | `β = 0.275` | Prob. infección del mosquito |
| **Transmisión vertical** | Mosquito (I) → Huevos | Implícita | Huevos nacen infectados |

---

## 4. Parámetros del Entorno

| Atributo | Variable | Valor Ejemplo | Descripción |
|----------|----------|---------------|-------------|
| **Tamaño cuadrícula** | `grid_size` | 50×50 | Dimensiones del espacio |
| **Población humana inicial** | `Nh` | 1000 | Número de agentes humanos |
| **Población mosquitos inicial** | `Nm` | 2000 | Número de mosquitos adultos |
| **Huevos iniciales** | `Ne` | 500 | Huevos al inicio |
| **Temperatura** | `T(t)` | Variable °C | Temperatura diaria |
| **Precipitación** | `P(t)` | Variable mm | Lluvia diaria |
| **Paso de tiempo** | `Δt` | 1 día | Unidad temporal |

### Tipos de Celdas
- **Urbana:** Viviendas/edificios
- **Agua:** Criaderos permanentes (lagos, estanques)
- **Parque:** Áreas de recreación
- **Criadero temporal:** Generado por lluvia (dura < 7 días)

### Generación de Criaderos por Lluvia
- Precipitación crea criaderos temporales
- Duración depende de intensidad de lluvia
- Si no llueve, desaparecen en < 7 días

---

## 5. Configuración Inicial del Modelo

```yaml
Población:
  humanos_totales: 1000
  mosquitos_adultos: 2000
  huevos_iniciales: 500
  infectados_iniciales_humanos: 2
  infectados_iniciales_mosquitos: 20

Distribución de Tipos Humanos:
  tipo_1_estudiantes: 25%
  tipo_2_trabajadores: 40%
  tipo_3_moviles: 10%
  tipo_4_estacionarios: 25%

Grid:
  tamaño: 50x50
  celdas_urbanas: 70%
  celdas_agua: 5%
  celdas_parque: 10%
  celdas_vacias: 15%
```

---

## 6. Ciclo de Simulación Diario

1. **Actualizar clima** (temperatura, precipitación)
2. **Actualizar criaderos** según lluvia
3. **Actualizar población mosquitos** (nacimientos/muertes)
4. **Mover humanos** según tipo y rutina
5. **Mover mosquitos** (búsqueda aleatoria o dirigida)
6. **Picaduras** e interacciones
7. **Transmisión** del virus (bidireccional)
8. **Actualizar estados** SEIR/SI
9. **Aplicar estrategias** de control (LSM, ITN/IRS)
10. **Registrar métricas** del día

---

## 7. Estrategias de Control (para implementar)

### LSM (Larval Source Management)
- Eliminación de criaderos
- Cobertura: 70%
- Efectividad: 80% reducción
- Frecuencia: cada 7 días

### ITN/IRS (Mosquiteros/Insecticidas)
- Protección individual
- Cobertura: 60% hogares
- Reducción picaduras: 70%
- Duración: 90 días

---

## 8. Métricas a Recolectar

- Número de humanos por estado (S, E, I, R)
- Número de mosquitos por estado (S, I)
- Población total de mosquitos
- Número de huevos
- Nuevas infecciones diarias (humanos y mosquitos)
- Temperatura y precipitación diarias
- Tasa de reproducción efectiva (Rt)
- Duración del brote

---

## Referencias

- Jindal, A., & Rao, S. (2017). Agent-Based Modeling and Simulation of Mosquito-Borne Disease Transmission. *Simulation Series*, 49(4).
- Adaptación para Bucaramanga, Colombia (2025)
- Datos climáticos: CSV con datos históricos de temperatura y precipitación
- Datos epidemiológicos: Datos Abiertos Colombia
