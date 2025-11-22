#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Validación del Modelo ABM de Dengue
==============================================

Ejecuta múltiples configuraciones del modelo y compara los resultados
con datos reales de dengue en Bucaramanga 2022.

Uso:
    python validate_model.py
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import subprocess
import json

# Configuración de estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10

# Directorio base
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "validation" / "data"
RESULTS_DIR = BASE_DIR / "validation" / "results"
CONFIG_DIR = BASE_DIR / "config"

# Crear directorio de resultados
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_real_data_2022():
    """
    Carga y procesa datos reales de dengue en Bucaramanga 2022.
    
    Returns
    -------
    pd.DataFrame
        DataFrame con casos por semana epidemiológica
    """
    # Ruta al archivo de datos
    data_file = DATA_DIR / "13._Dengue,_Dengue_grave_y_mortalidad_por_dengue_municipio_de_Bucaramanga_20251122.csv"
    
    if not data_file.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {data_file}")
    
    # Leer datos
    print(f"Cargando datos reales desde: {data_file}")
    df = pd.read_csv(data_file)
    
    # Filtrar solo datos de 2022 y Bucaramanga (cod_mun_r = 1)
    df_2022 = df[(df['año'] == 2022) & (df['cod_mun_r'] == 1)].copy()
    
    print(f"Total de casos en 2022: {len(df_2022)}")
    
    # Agrupar por semana epidemiológica
    casos_por_semana = df_2022.groupby('semana').size().reset_index(name='casos')
    
    # Asegurar que tenemos todas las semanas (1-52)
    todas_semanas = pd.DataFrame({'semana': range(1, 53)})
    casos_por_semana = todas_semanas.merge(casos_por_semana, on='semana', how='left').fillna(0)
    
    # Convertir semana a día del año (aproximado)
    casos_por_semana['dia'] = casos_por_semana['semana'] * 7
    
    # Calcular casos acumulados
    casos_por_semana['casos_acumulados'] = casos_por_semana['casos'].cumsum()
    
    print(f"Casos totales: {casos_por_semana['casos'].sum()}")
    print(f"Pico de casos: {casos_por_semana['casos'].max()} en semana {casos_por_semana.loc[casos_por_semana['casos'].idxmax(), 'semana']}")
    
    return casos_por_semana


def create_config_variant(base_config_path, variant_name, params):
    """
    Crea una variante de configuración con parámetros modificados.
    
    Parameters
    ----------
    base_config_path : Path
        Ruta a la configuración base
    variant_name : str
        Nombre de la variante
    params : dict
        Parámetros a modificar
        
    Returns
    -------
    Path
        Ruta al archivo de configuración creado
    """
    # Cargar configuración base
    with open(base_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Aplicar modificaciones
    for key_path, value in params.items():
        keys = key_path.split('.')
        current = config
        for key in keys[:-1]:
            current = current[key]
        current[keys[-1]] = value
    
    # Guardar variante
    variant_path = CONFIG_DIR / f"{variant_name}_config.yaml"
    with open(variant_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Configuración '{variant_name}' creada: {variant_path}")
    return variant_path


def run_simulation(config_path, steps=365, seed=None):
    """
    Ejecuta una simulación con la configuración especificada.
    
    Parameters
    ----------
    config_path : Path
        Ruta a la configuración
    steps : int
        Número de días a simular
    seed : int, optional
        Semilla aleatoria
        
    Returns
    -------
    pd.DataFrame
        Resultados de la simulación
    """
    cmd = [
        sys.executable,
        str(BASE_DIR / "main.py"),
        "--config", str(config_path),
        "--steps", str(steps),
        "--no-graphics"  # Sin gráficas individuales
    ]
    
    if seed is not None:
        cmd.extend(["--seed", str(seed)])
    
    print(f"Ejecutando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode != 0:
            print(f"Error en simulación: {result.stderr}")
            return None
        
        # Buscar el archivo CSV generado más reciente
        results_files = list((BASE_DIR / "results").glob("simulacion_*.csv"))
        if not results_files:
            print("No se encontró archivo de resultados")
            return None
        
        latest_file = max(results_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file)
        
        print(f"Simulación completada: {len(df)} días")
        return df
        
    except subprocess.TimeoutExpired:
        print("Simulación excedió el tiempo límite (1 hora)")
        return None
    except Exception as e:
        print(f"Error ejecutando simulación: {e}")
        return None


def plot_comparison(real_data, simulations_data, output_path):
    """
    Genera gráficas de comparación entre datos reales y simulaciones.
    
    Parameters
    ----------
    real_data : pd.DataFrame
        Datos reales
    simulations_data : dict
        Diccionario {nombre_config: DataFrame}
    output_path : Path
        Ruta para guardar la gráfica
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Validación del Modelo ABM de Dengue - Bucaramanga 2022', fontsize=16, fontweight='bold')
    
    # 1. Casos por semana - Comparación
    ax = axes[0, 0]
    ax.plot(real_data['semana'], real_data['casos'], 'ko-', linewidth=2, markersize=6, label='Datos Reales 2022', zorder=10)
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(simulations_data)))
    for (name, df), color in zip(simulations_data.items(), colors):
        # Agrupar por semana
        df['semana'] = (df['dia'] // 7) + 1
        casos_semana = df.groupby('semana')['infectados'].mean()
        ax.plot(casos_semana.index, casos_semana.values, '-', color=color, alpha=0.7, linewidth=1.5, label=name)
    
    ax.set_xlabel('Semana Epidemiológica')
    ax.set_ylabel('Casos por Semana')
    ax.set_title('Incidencia Semanal de Dengue')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # 2. Casos acumulados
    ax = axes[0, 1]
    ax.plot(real_data['dia'], real_data['casos_acumulados'], 'ko-', linewidth=2, markersize=4, label='Datos Reales 2022', zorder=10)
    
    for (name, df), color in zip(simulations_data.items(), colors):
        df['casos_acumulados'] = df['infectados'].cumsum()
        ax.plot(df['dia'], df['casos_acumulados'], '-', color=color, alpha=0.7, linewidth=1.5, label=name)
    
    ax.set_xlabel('Día del Año')
    ax.set_ylabel('Casos Acumulados')
    ax.set_title('Casos Acumulados de Dengue')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # 3. Dinámica de mosquitos (solo simulaciones)
    ax = axes[1, 0]
    for (name, df), color in zip(simulations_data.items(), colors):
        ax.plot(df['dia'], df['mosquitos_adultos'], '-', color=color, alpha=0.7, linewidth=1.5, label=name)
    
    ax.set_xlabel('Día del Año')
    ax.set_ylabel('Mosquitos Adultos')
    ax.set_title('Dinámica Poblacional de Mosquitos')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    
    # 4. Métricas de ajuste
    ax = axes[1, 1]
    metrics = []
    
    for name, df in simulations_data.items():
        # Calcular RMSE y correlación
        df['semana'] = (df['dia'] // 7) + 1
        casos_semana_sim = df.groupby('semana')['infectados'].mean()
        
        # Alinear con datos reales
        common_weeks = set(real_data['semana']) & set(casos_semana_sim.index)
        real_aligned = real_data[real_data['semana'].isin(common_weeks)].set_index('semana')['casos']
        sim_aligned = casos_semana_sim[casos_semana_sim.index.isin(common_weeks)]
        
        rmse = np.sqrt(((real_aligned - sim_aligned) ** 2).mean())
        corr = real_aligned.corr(sim_aligned)
        
        metrics.append({'Config': name, 'RMSE': rmse, 'Correlación': corr})
    
    metrics_df = pd.DataFrame(metrics)
    
    # Barras de RMSE
    x = np.arange(len(metrics_df))
    width = 0.35
    
    ax2 = ax.twinx()
    bars1 = ax.bar(x - width/2, metrics_df['RMSE'], width, label='RMSE', color='steelblue', alpha=0.7)
    bars2 = ax2.bar(x + width/2, metrics_df['Correlación'], width, label='Correlación', color='coral', alpha=0.7)
    
    ax.set_xlabel('Configuración')
    ax.set_ylabel('RMSE', color='steelblue')
    ax2.set_ylabel('Correlación', color='coral')
    ax.set_title('Métricas de Ajuste del Modelo')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_df['Config'], rotation=45, ha='right', fontsize=8)
    ax.tick_params(axis='y', labelcolor='steelblue')
    ax2.tick_params(axis='y', labelcolor='coral')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Leyenda combinada
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Gráfica guardada en: {output_path}")
    plt.close()
    
    return metrics_df


def main():
    """
    Función principal del script de validación.
    """
    print("="*70)
    print("VALIDACIÓN DEL MODELO ABM DE DENGUE")
    print("="*70)
    print()
    
    # 1. Cargar datos reales
    print("1. Cargando datos reales de Bucaramanga 2022...")
    real_data = load_real_data_2022()
    print()
    
    # 2. Definir configuraciones a probar
    print("2. Definiendo configuraciones a probar...")
    base_config = CONFIG_DIR / "default_config.yaml"
    
    configurations = {
        'Default': {},
        'High_Transmission': {
            'transmission.bite_rate': 0.7,
            'transmission.mosquito_to_human_prob': 0.7
        },
        'Low_Transmission': {
            'transmission.bite_rate': 0.3,
            'transmission.mosquito_to_human_prob': 0.5
        },
        'High_Mortality': {
            'mosquito_disease.mortality_rate': 0.12,
            'human_disease.infectious_period': 7.0
        },
        'Low_Mortality': {
            'mosquito_disease.mortality_rate': 0.05,
            'human_disease.infectious_period': 12.0
        }
    }
    
    # Crear variantes de configuración
    config_paths = {}
    for name, params in configurations.items():
        if params:  # Si hay parámetros, crear variante
            config_paths[name] = create_config_variant(base_config, name.lower(), params)
        else:  # Usar configuración base
            config_paths[name] = base_config
    print()
    
    # 3. Ejecutar simulaciones
    print("3. Ejecutando simulaciones (esto puede tomar tiempo)...")
    simulations_data = {}
    
    for name, config_path in config_paths.items():
        print(f"\n--- Ejecutando configuración: {name} ---")
        df = run_simulation(config_path, steps=365, seed=42)
        
        if df is not None:
            simulations_data[name] = df
            print(f"✓ {name}: {len(df)} días simulados")
        else:
            print(f"✗ {name}: Falló")
    print()
    
    # 4. Generar gráficas de comparación
    if simulations_data:
        print("4. Generando gráficas de comparación...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = RESULTS_DIR / f"validacion_{timestamp}.png"
        
        metrics = plot_comparison(real_data, simulations_data, output_path)
        
        # Guardar métricas
        metrics_path = RESULTS_DIR / f"metricas_{timestamp}.csv"
        metrics.to_csv(metrics_path, index=False)
        print(f"Métricas guardadas en: {metrics_path}")
        print()
        
        # Mostrar resumen
        print("="*70)
        print("RESUMEN DE VALIDACIÓN")
        print("="*70)
        print(metrics.to_string(index=False))
        print()
        print(f"Mejor configuración (menor RMSE): {metrics.loc[metrics['RMSE'].idxmin(), 'Config']}")
        print(f"Mejor correlación: {metrics.loc[metrics['Correlación'].idxmax(), 'Config']}")
    else:
        print("✗ No se pudieron ejecutar simulaciones")
    
    print()
    print("="*70)
    print("VALIDACIÓN COMPLETADA")
    print("="*70)


if __name__ == "__main__":
    main()
