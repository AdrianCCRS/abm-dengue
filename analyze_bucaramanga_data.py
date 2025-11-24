#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis simple de datos de dengue en Bucaramanga 2022 para calibración del modelo.
Usa solo bibliotecas estándar de Python.
"""

import csv
from datetime import datetime
from collections import Counter, defaultdict

print("Cargando datos de dengue en Bucaramanga...")

# Leer CSV
casos_2022 = []
with open('validation/data/13._Dengue,_Dengue_grave_y_mortalidad_por_dengue_municipio_de_Bucaramanga_20251122.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['año'] == '2022':
            casos_2022.append(row)

print(f"\n{'='*70}")
print(f"ANÁLISIS DE DATOS DE DENGUE - BUCARAMANGA 2022")
print(f"{'='*70}\n")

print(f"Total de casos reportados en 2022: {len(casos_2022)}")

# Análisis por semana epidemiológica
casos_por_semana = Counter()
for caso in casos_2022:
    semana = caso['semana']
    casos_por_semana[semana] += 1

semanas_ordenadas = sorted(casos_por_semana.items(), key=lambda x: int(x[0]))
semana_max = max(casos_por_semana.items(), key=lambda x: x[1])
semana_min = min(casos_por_semana.items(), key=lambda x: x[1])
promedio_semanal = len(casos_2022) / len(casos_por_semana) if casos_por_semana else 0

print(f"\nCasos por semana epidemiológica:")
print(f"  Semana con más casos: Semana {semana_max[0]} ({semana_max[1]} casos)")
print(f"  Semana con menos casos: Semana {semana_min[0]} ({semana_min[1]} casos)")
print(f"  Promedio casos/semana: {promedio_semanal:.1f}")
print(f"  Número de semanas con casos: {len(casos_por_semana)}")

# Análisis de clasificación
clasificaciones = Counter()
for caso in casos_2022:
    clasif = caso['clasfinal']
    clasificaciones[clasif] += 1

print(f"\nCasos por clasificación:")
for clasif, count in clasificaciones.most_common():
    pct = (count / len(casos_2022)) * 100
    print(f"  {clasif}: {count} ({pct:.1f}%)")

# Análisis de hospitalización
hospitalizados = sum(1 for caso in casos_2022 if caso['pac_hos_'] == '1')
tasa_hospitalizacion = hospitalizados / len(casos_2022) if casos_2022 else 0

print(f"\nHospitalización:")
print(f"  Casos hospitalizados: {hospitalizados} ({tasa_hospitalizacion*100:.1f}%)")

# Análisis por mes
casos_por_mes = defaultdict(int)
for caso in casos_2022:
    try:
        fecha = datetime.strptime(caso['ini_sin_'], '%Y-%m-%dT%H:%M:%S.%f')
        mes = fecha.month
        casos_por_mes[mes] += 1
    except:
        pass

print(f"\nCasos por mes:")
meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
for mes in sorted(casos_por_mes.keys()):
    print(f"  {meses[mes-1]}: {casos_por_mes[mes]}")

# Población de Bucaramanga
poblacion_bucaramanga = 613000
incidencia_acumulada = (len(casos_2022) / poblacion_bucaramanga) * 100000

print(f"\nIncidencia acumulada: {incidencia_acumulada:.1f} casos por 100,000 habitantes")

# PARÁMETROS CALIBRADOS PROPUESTOS
print(f"\n{'='*70}")
print(f"PARÁMETROS CALIBRADOS PROPUESTOS PARA EL MODELO")
print(f"{'='*70}\n")

print(f"1. POBLACIÓN Y ESCALA:")
print(f"   - Población real Bucaramanga: {poblacion_bucaramanga:,}")
print(f"   - Factor de escala sugerido: 1:61")
print(f"   - Población modelo: {poblacion_bucaramanga // 61:,} ≈ 10,000")
print(f"   - Casos reales 2022: {len(casos_2022)}")
print(f"   - Casos esperados en modelo: {len(casos_2022) // 61} ≈ {len(casos_2022) // 61}")

print(f"\n2. INFECTADOS INICIALES:")
# Casos en primeras semanas
casos_semana_1 = casos_por_semana.get('1', 0)
infectados_iniciales_modelo = max(5, casos_semana_1 // 61)
print(f"   - Casos semana 1 (reales): {casos_semana_1}")
print(f"   - infectados_iniciales: {infectados_iniciales_modelo}")

print(f"\n3. MOSQUITOS:")
# Ratio mosquito:humano típico 1.5:1 a 3:1
mosquitos_sugeridos = 15000
mosquitos_infectados = max(6, (casos_semana_1 // 61) * 2)
print(f"   - num_mosquitos: {mosquitos_sugeridos} (ratio 1.5:1)")
print(f"   - mosquitos_infectados_iniciales: {mosquitos_infectados}")
print(f"   - num_huevos: {mosquitos_sugeridos // 10} (10% de mosquitos)")

print(f"\n4. PARÁMETROS EPIDEMIOLÓGICOS:")
print(f"   - incubation_period: 5.0 días (mantener)")
print(f"   - infectious_period: 8.0 días (mantener)")
print(f"   - Tasa hospitalización observada: {tasa_hospitalizacion*100:.1f}%")

print(f"\n5. PARÁMETROS DE TRANSMISIÓN:")
print(f"   Estos deben ajustarse iterativamente para lograr ~{len(casos_2022) // 61} casos:")
print(f"   - mosquito_to_human_prob: 0.3-0.5 (probar 0.4)")
print(f"   - human_to_mosquito_prob: 0.3-0.4 (probar 0.35)")
print(f"   - bite_rate: 0.3-0.5 (probar 0.4)")

print(f"\n6. PARÁMETROS DE MOSQUITOS:")
print(f"   - mortality_rate: 0.07-0.08 (vida media ~12-14 días)")
print(f"   - eggs_per_female: 30-40")
print(f"   - gonotrophic_cycle_days: 3-4")
print(f"   - egg_mortality_rate: 0.15-0.25")

print(f"\n7. DURACIÓN SIMULACIÓN:")
print(f"   - steps: 365 (1 año completo)")

print(f"\n{'='*70}")
print(f"CONFIGURACIÓN YAML SUGERIDA")
print(f"{'='*70}\n")

yaml_config = f"""simulation:
  steps: 365
  width: 150
  height: 150
  num_humanos: 10000
  num_mosquitos: 15000
  num_huevos: 1500
  infectados_iniciales: {infectados_iniciales_modelo}
  mosquitos_infectados_iniciales: {mosquitos_infectados}
  usar_lsm: false
  usar_itn_irs: false
  seed: null

human_disease:
  incubation_period: 5.0
  infectious_period: 8.0

mosquito_disease:
  mortality_rate: 0.075
  sensory_range: 3
  incubation_period: 10
  carrying_capacity_per_cell: 3000

transmission:
  mosquito_to_human_prob: 0.4
  human_to_mosquito_prob: 0.35
  bite_rate: 0.4

mosquito_breeding:
  eggs_per_female: 35
  mating_probability: 0.6
  female_ratio: 0.52
  gonotrophic_cycle_days: 3
  egg_mortality_rate: 0.20
  breeding_site_ratio: 0.15
  temporary_sites:
    min_rainfall: 5.0
    sites_per_mm: 0.4
    duration_days: 7
    max_sites: 90

# NOTA: Ajustar iterativamente los parámetros de transmisión
# hasta lograr aproximadamente {len(casos_2022) // 61} casos en la simulación
"""

print(yaml_config)

print(f"\n{'='*70}")
print(f"ESTRATEGIA DE CALIBRACIÓN")
print(f"{'='*70}\n")

print(f"""1. OBJETIVO: Lograr ~{len(casos_2022) // 61} casos totales en 365 días

2. PROCESO ITERATIVO:
   a) Ejecutar simulación con parámetros iniciales
   b) Comparar casos totales con objetivo ({len(casos_2022) // 61})
   c) Ajustar parámetros:
      - Si muy pocos casos: ↑ mosquito_to_human_prob, ↑ bite_rate
      - Si demasiados casos: ↓ mosquito_to_human_prob, ↓ bite_rate
   d) Repetir hasta convergencia

3. MÉTRICAS DE VALIDACIÓN:
   - Casos totales: ~{len(casos_2022) // 61} ± 20%
   - Incidencia: ~{incidencia_acumulada:.0f} por 100k habitantes
   - Duración epidemia: Varios meses (no extinción prematura)
   - Curva epidémica: Picos y valles realistas

4. PARÁMETROS SECUNDARIOS (ajustar si es necesario):
   - Movilidad humana (afecta dispersión espacial)
   - Mortalidad de mosquitos (afecta duración epidemia)
   - Reproducción de mosquitos (afecta tamaño población)
""")

print(f"\n{'='*70}")
print(f"Análisis completado.")
print(f"{'='*70}\n")
