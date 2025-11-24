#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis de datos reales de dengue en Bucaramanga (SIVIGILA)
Para comparar con resultados del modelo ABM.

Autor: Equipo ABM Dengue
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "validation" / "data" / "13._Dengue,_Dengue_grave_y_mortalidad_por_dengue_municipio_de_Bucaramanga_20251122.csv"

# Cargar datos
print(f"📂 Cargando datos desde: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

print(f"✅ Datos cargados: {len(df):,} registros")
print(f"   Periodo: {df['año'].min()} - {df['año'].max()}")

# ========================================
# 1. CASOS POR AÑO
# ========================================
print("\n" + "="*60)
print("📊 CASOS DE DENGUE POR AÑO - BUCARAMANGA")
print("="*60)

casos_por_año = df.groupby('año').size().sort_index()
print("\nCasos totales por año:")
for año, casos in casos_por_año.items():
    print(f"  {año}: {casos:6,} casos")

# ========================================
# 2. CASOS POR SEMANA (Serie Temporal)
# ========================================
print("\n" + "="*60)
print("📈 SERIE TEMPORAL SEMANAL")
print("="*60)

# Convertir fecha de notificación a datetime
df['fec_not'] = pd.to_datetime(df['fec_not'], errors='coerce')
df['año_semana'] = df['año'].astype(str) + '-S' + df['semana'].astype(str).str.zfill(2)

casos_por_semana = df.groupby(['año', 'semana']).size().reset_index(name='casos')

# Filtrar año específico para análisis detallado (ej: 2022 que es tu datos_climaticos_2022.csv)
AÑO_ANALISIS = 2022
df_2022 = casos_por_semana[casos_por_semana['año'] == AÑO_ANALISIS].copy()

if not df_2022.empty:
    print(f"\n📅 Análisis detallado para {AÑO_ANALISIS}:")
    print(f"   Total casos: {df_2022['casos'].sum():,}")
    print(f"   Promedio semanal: {df_2022['casos'].mean():.1f} casos/semana")
    print(f"   Pico máximo: {df_2022['casos'].max()} casos (semana {df_2022.loc[df_2022['casos'].idxmax(), 'semana']})")
    print(f"   Semanas con casos: {len(df_2022)}/52")
else:
    print(f"⚠️  No hay datos para el año {AÑO_ANALISIS}")
    print("   Años disponibles:", df['año'].unique())

# ========================================
# 3. CLASIFICACIÓN DE CASOS
# ========================================
print("\n" + "="*60)
print("🏥 CLASIFICACIÓN DE CASOS")
print("="*60)

clasificacion = df['clasfinal'].value_counts()
print("\nDistribución por severidad:")
for clase, cantidad in clasificacion.items():
    porcentaje = (cantidad / len(df)) * 100
    print(f"  {clase}: {cantidad:6,} ({porcentaje:5.2f}%)")

# ========================================
# 4. DISTRIBUCIÓN ETARIA
# ========================================
print("\n" + "="*60)
print("👥 DISTRIBUCIÓN POR EDAD")
print("="*60)

edad_dist = df['grupo_etario'].value_counts().sort_index()
print("\nCasos por grupo etario:")
for grupo, casos in edad_dist.items():
    porcentaje = (casos / len(df)) * 100
    print(f"  {grupo}: {casos:6,} ({porcentaje:5.2f}%)")

# ========================================
# 5. DISTRIBUCIÓN POR SEXO
# ========================================
print("\n" + "="*60)
print("⚧️  DISTRIBUCIÓN POR SEXO")
print("="*60)

sexo_dist = df['sexo_'].value_counts()
print("\nCasos por sexo:")
for sexo, casos in sexo_dist.items():
    porcentaje = (casos / len(df)) * 100
    print(f"  {sexo}: {casos:6,} ({porcentaje:5.2f}%)")

# ========================================
# 6. HOSPITALIZACIÓN
# ========================================
print("\n" + "="*60)
print("🏥 CASOS HOSPITALIZADOS")
print("="*60)

# pac_hos_: 1=Hospitalizado, 2=No hospitalizado
hospitalizados = df['pac_hos_'].value_counts()
total_con_info = hospitalizados.sum()
if 1 in hospitalizados.index:
    pct_hosp = (hospitalizados[1] / total_con_info) * 100
    print(f"\n  Hospitalizados: {hospitalizados[1]:6,} ({pct_hosp:5.2f}%)")
if 2 in hospitalizados.index:
    pct_no_hosp = (hospitalizados[2] / total_con_info) * 100
    print(f"  Ambulatorios:   {hospitalizados[2]:6,} ({pct_no_hosp:5.2f}%)")

# ========================================
# 7. GUARDAR DATOS PROCESADOS
# ========================================
OUTPUT_DIR = PROJECT_ROOT / "validation" / "processed"
OUTPUT_DIR.mkdir(exist_ok=True)

# Serie temporal semanal
serie_temporal_path = OUTPUT_DIR / "casos_semanales_bucaramanga.csv"
casos_por_semana.to_csv(serie_temporal_path, index=False)
print(f"\n💾 Serie temporal guardada en: {serie_temporal_path}")

# Datos 2022 específicos (para comparar con tu modelo)
if not df_2022.empty:
    datos_2022_path = OUTPUT_DIR / "casos_semanales_2022.csv"
    df_2022.to_csv(datos_2022_path, index=False)
    print(f"💾 Datos 2022 guardados en: {datos_2022_path}")

# ========================================
# 8. GRÁFICAS
# ========================================
print("\n" + "="*60)
print("📊 GENERANDO GRÁFICAS...")
print("="*60)

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Análisis de Datos Reales - Dengue Bucaramanga (SIVIGILA)', fontsize=16, fontweight='bold')

# Gráfica 1: Casos por año
ax1 = axes[0, 0]
casos_por_año.plot(kind='bar', ax=ax1, color='steelblue', edgecolor='black')
ax1.set_title('Casos Totales por Año')
ax1.set_xlabel('Año')
ax1.set_ylabel('Número de Casos')
ax1.grid(axis='y', alpha=0.3)
ax1.tick_params(axis='x', rotation=45)

# Gráfica 2: Serie temporal 2022 (si existe)
ax2 = axes[0, 1]
if not df_2022.empty:
    ax2.plot(df_2022['semana'], df_2022['casos'], marker='o', linewidth=2, markersize=4, color='crimson')
    ax2.set_title(f'Casos Semanales - {AÑO_ANALISIS}')
    ax2.set_xlabel('Semana Epidemiológica')
    ax2.set_ylabel('Casos')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=df_2022['casos'].mean(), color='orange', linestyle='--', label=f'Promedio: {df_2022["casos"].mean():.1f}')
    ax2.legend()
else:
    ax2.text(0.5, 0.5, f'No hay datos para {AÑO_ANALISIS}', 
             ha='center', va='center', fontsize=12)
    ax2.set_title(f'Casos Semanales - {AÑO_ANALISIS}')

# Gráfica 3: Distribución etaria
ax3 = axes[1, 0]
edad_dist_top = edad_dist.head(10)
edad_dist_top.plot(kind='barh', ax=ax3, color='teal', edgecolor='black')
ax3.set_title('Distribución por Grupo Etario (Top 10)')
ax3.set_xlabel('Número de Casos')
ax3.set_ylabel('Grupo Etario')
ax3.grid(axis='x', alpha=0.3)

# Gráfica 4: Clasificación
ax4 = axes[1, 1]
clasificacion_simple = clasificacion.head(5)
colors = ['lightcoral', 'gold', 'lightblue', 'lightgreen', 'plum']
clasificacion_simple.plot(kind='pie', ax=ax4, autopct='%1.1f%%', colors=colors, startangle=90)
ax4.set_title('Clasificación de Casos (Top 5)')
ax4.set_ylabel('')

plt.tight_layout()
plot_path = OUTPUT_DIR / "analisis_datos_reales.png"
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
print(f"✅ Gráficas guardadas en: {plot_path}")

print("\n" + "="*60)
print("✅ ANÁLISIS COMPLETO")
print("="*60)
print(f"\n📁 Revisa los archivos en: {OUTPUT_DIR}")
