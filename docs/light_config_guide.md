# Configuración Light - Guía de Uso

## Descripción

`light_config.yaml` es una configuración optimizada para **rendimiento** manteniendo la **dinámica epidemiológica realista** mediante escalado proporcional de todos los componentes.

## Diferencias vs Configuración Default

| Parámetro | Default | Light | Ratio | Justificación |
|-----------|---------|-------|-------|---------------|
| **Población** |
| Humanos | 3,000 | 300 | 10× | Mantiene diversidad de tipos |
| Mosquitos | 1,500 | 150 | 10× | Preserva ratio 1:2 |
| Huevos | 3,000 | 300 | 10× | Mismo ratio inicial |
| **Espacialidad** |
| Grid | 150×150 | 100×100 | ~2.25× | Densidad similar |
| Sitios de cría | 200 | 50 | 4× | 1 sitio/200 celdas |
| Parques | 10 | 3 | 3.3× | Proporcional |
| **Control Poblacional** |
| eggs_per_female | 25 | 20 | 1.25× | Límite inferior realista |
| gonotrophic_cycle | 6 | 5 | 1.2× | Valor medio-alto |
| egg_mortality | 10% | 8% | 0.8× | Realista |
| adult_mortality | 12% | 10% | 0.83× | Vida media 10 días |

## Parámetros Sin Cambios (Biológicamente Determinados)

- **Transmisión**: α=0.6, Pb=0.5
- **Incubación**: Ne=5 días, Ni=6 días
- **Desarrollo térmico**: T_base=8.3°C, K=181.2 °C·día
- **Movilidad humana**: Patrones y probabilidades

## Rendimiento Esperado

| Métrica | Default | Light | Mejora |
|---------|---------|-------|--------|
| Mosquitos (equilibrio) | ~10,000-15,000 | ~500-800 | 15-20× |
| Tiempo/día | ~20-30s | ~2-5s | 6-10× |
| 365 días | ~7.6 horas | ~30-45 min | **10-15×** |

## Uso

### Ejecución Básica

```bash
python main.py --config config/light_config.yaml --steps 365
```

### Con Debugging

```bash
python debug_bottleneck.py --steps 30
# Modificar línea 158 para usar light_config.yaml
```

### Comparación con Default

```bash
# Ejecutar ambas configuraciones con mismo seed
python main.py --config config/default_config.yaml --steps 30 --seed 42
python main.py --config config/light_config.yaml --steps 30 --seed 42

# Comparar resultados
```

## Validación de Balance

### Criterios de Éxito

✅ **Población estable**: Mosquitos no crecen exponencialmente  
✅ **Dinámica epidemiológica**: Brotes ocurren de forma similar  
✅ **Rendimiento**: 365 días en < 1 hora  
✅ **Reproducibilidad**: Mismo seed → mismos resultados

### Métricas a Monitorear

1. **Población de mosquitos** (día 30):
   - Esperado: 500-1,000
   - Alerta si > 2,000

2. **Tiempo por día** (día 30):
   - Esperado: 2-5s
   - Alerta si > 10s

3. **Casos humanos** (acumulado 365 días):
   - Esperado: Proporcional a default (~10% de escala)

## Cuándo Usar Cada Configuración

### `default_config.yaml`
- Simulaciones finales para publicación
- Análisis detallado de sensibilidad
- Validación con datos reales
- Cuando el tiempo no es limitante

### `light_config.yaml`
- Desarrollo y debugging
- Pruebas rápidas de parámetros
- Exploración de espacio de parámetros
- Ejecución en laptops/máquinas locales
- Iteración rápida de modelos

## Escalado a Otras Configuraciones

Para crear configuraciones intermedias:

```yaml
# medium_config.yaml (5× reducción)
num_humanos: 600
num_mosquitos: 300
width: 120
height: 120
num_sitios_cria: 100
```

**Regla general**: Mantener ratios consistentes
- Humanos:Mosquitos = 2:1
- Sitios:Área = 1:200 celdas
- Densidad humanos ≈ 0.03-0.13 por celda

## Notas Técnicas

### Capacidad de Carga

El límite de 500 huevos/sitio está hardcoded en `EggManager.add_eggs()`:

```python
MAX_EGGS_PER_SITE = 500
```

Con light_config:
- 50 sitios × 500 huevos = 25,000 huevos máximo teórico
- En práctica: ~5,000-8,000 huevos en equilibrio

### Determinismo

Ambas configuraciones son deterministas con seed fijo:

```bash
python main.py --config config/light_config.yaml --steps 365 --seed 42
```

Ejecutar dos veces con mismo seed → resultados idénticos

## Troubleshooting

### Población aún muy alta

Si mosquitos > 2,000 al día 30:

1. Aumentar `egg_mortality_rate` a 0.10
2. Aumentar `adult_mortality` a 0.12
3. Reducir `eggs_per_female` a 15

### Simulación muy lenta

Si tiempo > 10s/día:

1. Reducir `num_humanos` a 200
2. Reducir `num_mosquitos` a 100
3. Reducir grid a 80×80

### No hay brotes

Si no hay casos humanos:

1. Aumentar `infectados_iniciales` a 15
2. Aumentar `mosquitos_infectados_iniciales` a 10
3. Verificar `transmission_probability`

## Referencias

- Configuración basada en profiling de 30 pasos
- Parámetros biológicos de Tun-Lin et al. (1999)
- Escalado validado con seed fijo
