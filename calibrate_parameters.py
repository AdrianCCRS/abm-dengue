#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibración analítica de parámetros del modelo ABM de dengue.

Este script usa las ecuaciones del modelo para calcular parámetros
que reproduzcan los datos observados en Bucaramanga 2022.
"""

import csv
from collections import Counter
import math

# ============================================================================
# 1. CARGAR Y ANALIZAR DATOS REALES
# ============================================================================

print("="*80)
print("CALIBRACIÓN ANALÍTICA DEL MODELO ABM - BUCARAMANGA 2022")
print("="*80)

# Cargar datos
casos_2022 = []
with open('validation/data/13._Dengue,_Dengue_grave_y_mortalidad_por_dengue_municipio_de_Bucaramanga_20251122.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['año'] == '2022':
            casos_2022.append(row)

total_casos = len(casos_2022)
poblacion_real = 613000

# Casos por semana
casos_por_semana = Counter()
for caso in casos_2022:
    casos_por_semana[caso['semana']] += 1

print(f"\nDATOS OBSERVADOS:")
print(f"  Población Bucaramanga: {poblacion_real:,}")
print(f"  Casos totales 2022: {total_casos}")
print(f"  Incidencia: {(total_casos/poblacion_real)*100000:.1f} por 100k hab")
print(f"  Casos semana pico: {max(casos_por_semana.values())}")

# ============================================================================
# 2. PARÁMETROS DEL MODELO (ESTRUCTURA)
# ============================================================================

print(f"\n{'='*80}")
print("PARÁMETROS DEL MODELO ABM")
print("="*80)

# Escala del modelo
escala = 61  # 1:61 (613,000 / 10,000)
N_humanos = 10000
N_mosquitos_inicial = 15000

print(f"\nESCALA Y POBLACIÓN:")
print(f"  Factor de escala: 1:{escala}")
print(f"  N_humanos (modelo): {N_humanos}")
print(f"  Casos objetivo (modelo): {total_casos // escala} ≈ {total_casos // escala}")

# ============================================================================
# 3. MODELO DE TRANSMISIÓN (ECUACIONES)
# ============================================================================

print(f"\n{'='*80}")
print("ANÁLISIS DEL MODELO DE TRANSMISIÓN")
print("="*80)

print(f"""
El modelo usa transmisión bidireccional mosquito-humano:

1. MOSQUITO → HUMANO:
   - Mosquitos infecciosos (I_m) pican con probabilidad 'bite_rate'
   - Picaduras se distribuyen entre humanos susceptibles (S_h)
   - Transmisión ocurre con probabilidad α (mosquito_to_human_prob)
   
   Nuevas infecciones humanas ≈ I_m × bite_rate × (S_h/H_total) × α

2. HUMANO → MOSQUITO:
   - Mosquitos susceptibles (S_m) pican con probabilidad 'bite_rate'
   - Picaduras se distribuyen entre humanos infecciosos (I_h)
   - Transmisión ocurre con probabilidad β (human_to_mosquito_prob)
   
   Nuevos mosquitos infectados ≈ S_m × bite_rate × (I_h/H_total) × β

3. NÚMERO REPRODUCTIVO BÁSICO (R0):
   R0 = (α × β × bite_rate² × N_m × vida_mosquito) / (N_h × γ_h)
   
   Donde:
   - γ_h = 1/infectious_period (tasa de recuperación humana)
   - vida_mosquito = 1/mortality_rate
""")

# ============================================================================
# 4. CÁLCULO DE R0 OBJETIVO
# ============================================================================

print(f"{'='*80}")
print("CÁLCULO DE R0 OBJETIVO")
print("="*80)

# Estimar R0 desde datos reales
# Método: tasa de crecimiento exponencial en fase inicial
semanas_iniciales = sorted([(int(k), v) for k, v in casos_por_semana.items() if int(k) <= 20])[:10]
if len(semanas_iniciales) >= 3:
    # Calcular tasa de crecimiento
    casos_iniciales = [c for _, c in semanas_iniciales if c > 0]
    if len(casos_iniciales) >= 3:
        # Tasa de crecimiento promedio
        ratios = [casos_iniciales[i+1]/casos_iniciales[i] for i in range(len(casos_iniciales)-1) if casos_iniciales[i] > 0]
        tasa_crecimiento_semanal = sum(ratios) / len(ratios) if ratios else 1.0
        
        # R0 = (1 + r*T_gen)
        T_gen = 7  # días (período de generación)
        r_diario = (tasa_crecimiento_semanal - 1) / 7
        R0_estimado = 1 + r_diario * T_gen
        
        print(f"\nDe datos observados:")
        print(f"  Tasa crecimiento semanal: {tasa_crecimiento_semanal:.3f}")
        print(f"  Tasa crecimiento diaria: {r_diario:.4f}")
        print(f"  R0 estimado: {R0_estimado:.2f}")
else:
    R0_estimado = 1.8  # Valor típico para dengue
    print(f"\nR0 asumido (típico dengue): {R0_estimado:.2f}")

# ============================================================================
# 5. CALIBRACIÓN DE PARÁMETROS DE TRANSMISIÓN
# ============================================================================

print(f"\n{'='*80}")
print("CALIBRACIÓN DE PARÁMETROS DE TRANSMISIÓN")
print("="*80)

# Parámetros fijos del modelo
infectious_period = 8.0  # días
mortality_rate_mosq = 0.075  # mortalidad diaria mosquitos
vida_mosquito = 1 / mortality_rate_mosq  # ~13.3 días

gamma_h = 1 / infectious_period  # tasa recuperación humana

print(f"\nParámetros fijos:")
print(f"  infectious_period: {infectious_period} días")
print(f"  γ_h (tasa recuperación): {gamma_h:.4f} /día")
print(f"  mortality_rate (mosquitos): {mortality_rate_mosq}")
print(f"  Vida media mosquito: {vida_mosquito:.1f} días")

# Resolver para α, β, bite_rate dado R0
# R0 = (α × β × bite_rate² × N_m × vida_mosquito) / (N_h × γ_h)
# 
# Asumiendo simetría: α ≈ β (probabilidades similares)
# Y bite_rate típico: 0.33-0.5 (cada 2-3 días)

print(f"\nCálculo de parámetros de transmisión:")
print(f"  R0 objetivo: {R0_estimado:.2f}")

# Probar diferentes valores de bite_rate
for bite_rate in [0.3, 0.35, 0.4, 0.45, 0.5]:
    # R0 = (α × β × bite_rate² × N_m × vida_mosquito) / (N_h × γ_h)
    # Si α = β, entonces:
    # α² = (R0 × N_h × γ_h) / (bite_rate² × N_m × vida_mosquito)
    
    alpha_squared = (R0_estimado * N_humanos * gamma_h) / (bite_rate**2 * N_mosquitos_inicial * vida_mosquito)
    alpha = math.sqrt(alpha_squared)
    beta = alpha  # Asumiendo simetría
    
    # Verificar que estén en rango razonable [0, 1]
    if 0 < alpha <= 1:
        R0_calculado = (alpha * beta * bite_rate**2 * N_mosquitos_inicial * vida_mosquito) / (N_humanos * gamma_h)
        print(f"\n  bite_rate = {bite_rate:.2f}:")
        print(f"    α (mosquito→humano) = {alpha:.4f}")
        print(f"    β (humano→mosquito) = {beta:.4f}")
        print(f"    R0 resultante = {R0_calculado:.2f}")

# ============================================================================
# 6. PARÁMETROS DE MOSQUITOS (DINÁMICA POBLACIONAL)
# ============================================================================

print(f"\n{'='*80}")
print("PARÁMETROS DE DINÁMICA DE MOSQUITOS")
print("="*80)

print(f"""
La población de mosquitos debe mantenerse estable para sostener la transmisión.

Balance poblacional:
  Nacimientos/día = Muertes/día
  
  Nacimientos = (N_m × female_ratio × eggs_per_female) / gonotrophic_cycle
  Muertes = N_m × mortality_rate
  
Para equilibrio:
  eggs_per_female / gonotrophic_cycle ≈ mortality_rate / (female_ratio × survival_egg)
  
Donde survival_egg = 1 - egg_mortality_rate
""")

female_ratio = 0.52
egg_mortality = 0.20
survival_egg = 1 - egg_mortality

print(f"\nParámetros de reproducción:")
print(f"  female_ratio: {female_ratio}")
print(f"  egg_mortality_rate: {egg_mortality}")
print(f"  survival_egg: {survival_egg}")

print(f"\nPara mantener población estable:")
for gonotrophic_cycle in [3, 4, 5]:
    # eggs_per_female necesarios para equilibrio
    eggs_needed = (mortality_rate_mosq * gonotrophic_cycle) / (female_ratio * survival_egg)
    print(f"  gonotrophic_cycle = {gonotrophic_cycle} días → eggs_per_female ≈ {eggs_needed:.1f}")

# ============================================================================
# 7. CONFIGURACIÓN FINAL CALIBRADA
# ============================================================================

print(f"\n{'='*80}")
print("CONFIGURACIÓN CALIBRADA FINAL")
print("="*80)

# Seleccionar parámetros óptimos
bite_rate_opt = 0.4
alpha_opt = 0.35
beta_opt = 0.35
eggs_per_female_opt = 35
gonotrophic_cycle_opt = 4

print(f"""
simulation:
  steps: 365
  width: 150
  height: 150
  num_humanos: {N_humanos}
  num_mosquitos: {N_mosquitos_inicial}
  num_huevos: {N_mosquitos_inicial // 10}
  infectados_iniciales: 5
  mosquitos_infectados_iniciales: 6
  usar_lsm: false
  usar_itn_irs: false
  seed: null

human_disease:
  incubation_period: 5.0
  infectious_period: {infectious_period}

mosquito_disease:
  mortality_rate: {mortality_rate_mosq}
  sensory_range: 3
  incubation_period: 10
  carrying_capacity_per_cell: 3000

transmission:
  mosquito_to_human_prob: {alpha_opt}
  human_to_mosquito_prob: {beta_opt}
  bite_rate: {bite_rate_opt}

mosquito_breeding:
  eggs_per_female: {eggs_per_female_opt}
  mating_probability: 0.6
  female_ratio: {female_ratio}
  gonotrophic_cycle_days: {gonotrophic_cycle_opt}
  egg_mortality_rate: {egg_mortality}
  breeding_site_ratio: 0.15
  
  immature_development_threshold: 8.3
  immature_thermal_constant: 181.2
  rainfall_threshold: 0.0
  
  temporary_sites:
    min_rainfall: 5.0
    sites_per_mm: 0.4
    duration_days: 7
    max_sites: 90

mobility:
  student_daily_probabilities:
    home: 0.55
    destination: 0.35
    park: 0.10
  worker_daily_probabilities:
    home: 0.60
    destination: 0.35
    park: 0.05
  mobile_daily_probabilities:
    home: 0.45
    destination: 0.0
    park: 0.15
    random: 0.40
  stationary_daily_probabilities:
    home: 0.95
    destination: 0.0
    park: 0.05
    random: 0.0

population:
  mobility_distribution:
    student: 0.30
    worker: 0.40
    mobile: 0.20
    stationary: 0.10

environment:
  cell_types:
    water_ratio: 0.05
    park_ratio: 0.10
  zone_sizes:
    water_min: 2
    water_max: 4
    park_min: 3
    park_max: 6
  mosquito_flight:
    max_range: 5
  grid_generation:
    max_placement_failures: 50
    max_total_attempts: 500
  synthetic_climate:
    rain_probability: 0.35
    rain_min_mm: 5.0
    rain_max_mm: 50.0

control:
  lsm:
    frequency_days: 7
    coverage: 0.7
    effectiveness: 0.8
  itn_irs:
    duration_days: 90
    coverage: 0.6
    effectiveness: 0.7

human_behavior:
  isolation_probability: 0.7
  infected_mobility_radius: 1
""")

# ============================================================================
# 8. VALIDACIÓN TEÓRICA
# ============================================================================

print(f"\n{'='*80}")
print("VALIDACIÓN TEÓRICA")
print("="*80)

R0_final = (alpha_opt * beta_opt * bite_rate_opt**2 * N_mosquitos_inicial * vida_mosquito) / (N_humanos * gamma_h)

print(f"\nR0 con parámetros calibrados: {R0_final:.2f}")
print(f"R0 objetivo: {R0_estimado:.2f}")
print(f"Diferencia: {abs(R0_final - R0_estimado):.3f}")

# Estimar casos esperados (aproximación simple)
# En equilibrio endémico: I ≈ N × (R0 - 1) / R0
casos_esperados_equilibrio = N_humanos * (R0_final - 1) / R0_final
print(f"\nCasos en equilibrio endémico (aprox): {casos_esperados_equilibrio:.0f}")
print(f"Casos objetivo: {total_casos // escala}")

print(f"\n{'='*80}")
print("PRÓXIMOS PASOS")
print("="*80)

print(f"""
1. EJECUTAR SIMULACIÓN con parámetros calibrados
2. COMPARAR resultados con datos reales:
   - Casos totales: {total_casos // escala} esperados
   - Curva temporal: pico en semana ~20
   - Duración: todo el año (no extinción prematura)
   
3. AJUSTE FINO si es necesario:
   - Si casos < objetivo: ↑ α o ↑ bite_rate ligeramente
   - Si casos > objetivo: ↓ α o ↓ bite_rate ligeramente
   - Si extinción prematura: ↓ mortality_rate o ↑ eggs_per_female
   
4. VALIDAR MÉTRICAS SECUNDARIAS:
   - Distribución espacial
   - Dinámica temporal (picos y valles)
   - Población de mosquitos estable
""")

print(f"\n{'='*80}")
print("Calibración completada.")
print("="*80 + "\n")
