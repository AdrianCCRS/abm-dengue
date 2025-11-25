#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar experimentos paralelos del modelo ABM de Dengue.

Ejecuta 16 simulaciones en total:
- 4 sin estrategias de control
- 4 con LSM solamente
- 4 con ITN/IRS solamente
- 4 con ambas estrategias

Cada conjunto de 4 simulaciones (una por estrategia) usa la misma semilla.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander
"""

import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool, cpu_count
import pandas as pd

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel


def ejecutar_simulacion_individual(params):
    """
    Ejecuta una simulación individual con los parámetros dados.
    
    Parameters
    ----------
    params : dict
        Diccionario con los parámetros de la simulación
        
    Returns
    -------
    dict
        Resultados de la simulación
    """
    seed = params['seed']
    usar_lsm = params['usar_lsm']
    usar_itn_irs = params['usar_itn_irs']
    run_id = params['run_id']
    config = params['config']
    
    # Identificar tipo de estrategia
    if not usar_lsm and not usar_itn_irs:
        estrategia = "sin_control"
    elif usar_lsm and not usar_itn_irs:
        estrategia = "lsm"
    elif not usar_lsm and usar_itn_irs:
        estrategia = "itn_irs"
    else:
        estrategia = "ambas"
    
    print(f"[Iniciando] Run {run_id} - Estrategia: {estrategia} - Semilla: {seed}")
    
    # Convertir fecha_inicio a datetime si es string
    fecha_inicio_str = config['simulation'].get('fecha_inicio', '2022-01-01')
    if isinstance(fecha_inicio_str, str):
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
    else:
        fecha_inicio = fecha_inicio_str
    
    # Crear modelo con configuración
    model = DengueModel(
        width=config['simulation']['width'],
        height=config['simulation']['height'],
        num_humanos=config['simulation']['num_humanos'],
        num_mosquitos=config['simulation']['num_mosquitos'],
        num_huevos=config['simulation']['num_huevos'],
        infectados_iniciales=config['simulation']['infectados_iniciales'],
        mosquitos_infectados_iniciales=config['simulation']['mosquitos_infectados_iniciales'],
        usar_lsm=usar_lsm,
        usar_itn_irs=usar_itn_irs,
        seed=seed,
        fecha_inicio=fecha_inicio,
        climate_data_path='data/raw/datos_climaticos_2022.csv',
        config=config
    )
    
    # Ejecutar simulación
    steps = config['simulation']['steps']
    for step in range(steps):
        model.step()
        
        # Mostrar progreso cada 50 días
        if (step + 1) % 50 == 0:
            print(f"[Run {run_id} - {estrategia}] Día {step + 1}/{steps}")
    
    # Recolectar resultados
    df = model.datacollector.get_model_vars_dataframe()
    
    # Agregar metadatos
    df['seed'] = seed
    df['estrategia'] = estrategia
    df['usar_lsm'] = usar_lsm
    df['usar_itn_irs'] = usar_itn_irs
    df['run_id'] = run_id
    
    # Calcular métricas finales
    resultados = {
        'run_id': run_id,
        'seed': seed,
        'estrategia': estrategia,
        'usar_lsm': usar_lsm,
        'usar_itn_irs': usar_itn_irs,
        'total_infectados': df['Infectados'].iloc[-1],
        'total_recuperados': df['Recuperados'].iloc[-1],
        'pico_infectados': df['Infectados'].max(),
        'dia_pico': df['Infectados'].idxmax(),
        'mosquitos_finales': df['Mosquitos_Total'].iloc[-1],
        'mosquitos_infectados_finales': df['Mosquitos_I'].iloc[-1],
        'tasa_ataque': (df['Infectados'].iloc[-1] + df['Recuperados'].iloc[-1]) / config['simulation']['num_humanos'] * 100,
        'dataframe': df
    }
    
    print(f"[Completado] Run {run_id} - {estrategia} - Pico: {resultados['pico_infectados']} - Tasa ataque: {resultados['tasa_ataque']:.2f}%")
    
    return resultados


def main():
    """Función principal para ejecutar experimentos paralelos."""
    parser = argparse.ArgumentParser(
        description='Ejecutar experimentos paralelos del modelo ABM de Dengue'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/default_config.yaml',
        help='Archivo de configuración YAML'
    )
    parser.add_argument(
        '--seeds',
        type=int,
        nargs='+',
        default=[42, 123, 456, 789],
        help='Semillas para las simulaciones (4 valores)'
    )
    parser.add_argument(
        '--processes',
        type=int,
        default=4,
        help='Número de procesos paralelos (default: 4)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/experiments',
        help='Directorio para guardar resultados'
    )
    
    args = parser.parse_args()
    
    # Validar semillas
    if len(args.seeds) != 4:
        print("Error: Se requieren exactamente 4 semillas")
        sys.exit(1)
    
    # Cargar configuración
    print(f"Cargando configuración desde: {args.config}")
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Crear directorio de salida
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Preparar lista de simulaciones
    simulaciones = []
    run_counter = 1
    
    # Configuraciones de estrategias
    estrategias = [
        {'usar_lsm': False, 'usar_itn_irs': False},  # Sin control
        {'usar_lsm': True, 'usar_itn_irs': False},   # LSM
        {'usar_lsm': False, 'usar_itn_irs': True},   # ITN/IRS
        {'usar_lsm': True, 'usar_itn_irs': True}     # Ambas
    ]
    
    # Para cada semilla, crear 4 simulaciones (una por estrategia)
    for seed in args.seeds:
        for estrategia in estrategias:
            simulaciones.append({
                'seed': seed,
                'usar_lsm': estrategia['usar_lsm'],
                'usar_itn_irs': estrategia['usar_itn_irs'],
                'run_id': run_counter,
                'config': config
            })
            run_counter += 1
    
    print(f"\n{'='*70}")
    print(f"EXPERIMENTOS PARALELOS - ABM DENGUE")
    print(f"{'='*70}")
    print(f"Total de simulaciones: {len(simulaciones)}")
    print(f"Semillas: {args.seeds}")
    print(f"Procesos paralelos: {args.processes}")
    print(f"Directorio de salida: {output_dir}")
    print(f"{'='*70}\n")
    
    # Ejecutar simulaciones en paralelo
    with Pool(processes=args.processes) as pool:
        resultados = pool.map(ejecutar_simulacion_individual, simulaciones)
    
    print(f"\n{'='*70}")
    print("TODAS LAS SIMULACIONES COMPLETADAS")
    print(f"{'='*70}\n")
    
    # Consolidar resultados
    resultados_summary = []
    dataframes_completos = []
    
    for resultado in resultados:
        # Guardar dataframe individual
        df = resultado.pop('dataframe')
        df.to_csv(
            output_dir / f"simulacion_{timestamp}_run{resultado['run_id']}_{resultado['estrategia']}_seed{resultado['seed']}.csv",
            index=True
        )
        dataframes_completos.append(df)
        
        # Agregar a resumen
        resultados_summary.append(resultado)
    
    # Crear DataFrame resumen
    df_summary = pd.DataFrame(resultados_summary)
    
    # Guardar resumen
    summary_file = output_dir / f"resumen_experimentos_{timestamp}.csv"
    df_summary.to_csv(summary_file, index=False)
    print(f"Resumen guardado en: {summary_file}")
    
    # Consolidar todos los dataframes
    df_consolidado = pd.concat(dataframes_completos, ignore_index=True)
    consolidado_file = output_dir / f"datos_consolidados_{timestamp}.csv"
    df_consolidado.to_csv(consolidado_file, index=False)
    print(f"Datos consolidados guardados en: {consolidado_file}")
    
    # Mostrar resumen por estrategia
    print(f"\n{'='*70}")
    print("RESUMEN POR ESTRATEGIA")
    print(f"{'='*70}\n")
    
    summary_by_strategy = df_summary.groupby('estrategia').agg({
        'pico_infectados': ['mean', 'std'],
        'tasa_ataque': ['mean', 'std'],
        'mosquitos_finales': ['mean', 'std']
    }).round(2)
    
    print(summary_by_strategy)
    print()
    
    # Guardar configuración usada
    config_file = output_dir / f"configuracion_{timestamp}.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump({
            'config_original': config,
            'seeds': args.seeds,
            'procesos': args.processes,
            'timestamp': timestamp
        }, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Configuración guardada en: {config_file}")
    print(f"\n{'='*70}")
    print("EXPERIMENTO COMPLETADO EXITOSAMENTE")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
