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
import json
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool, cpu_count
import pandas as pd
import numpy as np

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel


def convert_to_native_types(obj):
    """
    Convierte tipos de NumPy/Pandas a tipos nativos de Python para JSON.
    
    Args:
        obj: Objeto a convertir (puede ser dict, list, numpy type, etc.)
    
    Returns:
        Objeto con tipos nativos de Python
    """
    if isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj


def ejecutar_simulacion_individual(params):
    """
    Ejecuta una simulación individual con los parámetros dados.
    Guarda los resultados inmediatamente en su propia carpeta.
    
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
    output_dir = Path(params['output_dir'])
    
    # Identificar tipo de estrategia
    if not usar_lsm and not usar_itn_irs:
        estrategia = "sin_control"
    elif usar_lsm and not usar_itn_irs:
        estrategia = "lsm"
    elif not usar_lsm and usar_itn_irs:
        estrategia = "itn_irs"
    else:
        estrategia = "ambas"
    
    # Crear carpeta para esta simulación específica
    run_dir = output_dir / f"run_{run_id:03d}_{estrategia}_seed{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[Iniciando] Run {run_id} - Estrategia: {estrategia} - Semilla: {seed}")
    print(f"            Guardando en: {run_dir}")
    
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
        'carpeta': str(run_dir)
    }
    
    # *** GUARDAR INMEDIATAMENTE LOS RESULTADOS ***
    try:
        # 1. Guardar datos completos en CSV
        csv_file = run_dir / "datos_completos.csv"
        df.to_csv(csv_file, index=True)
        
        # 2. Guardar resumen en JSON (convertir tipos NumPy a nativos)
        resumen_file = run_dir / "resumen.json"
        resumen_json = {k: v for k, v in resultados.items() if k != 'carpeta'}
        resumen_json = convert_to_native_types(resumen_json)  # Convertir todos los tipos
        with open(resumen_file, 'w', encoding='utf-8') as f:
            json.dump(resumen_json, f, indent=2, ensure_ascii=False)
        
        # 3. Guardar parámetros de configuración
        params_file = run_dir / "parametros.yaml"
        with open(params_file, 'w', encoding='utf-8') as f:
            yaml.dump({
                'run_id': run_id,
                'seed': seed,
                'estrategia': estrategia,
                'usar_lsm': usar_lsm,
                'usar_itn_irs': usar_itn_irs,
                'config': config
            }, f, default_flow_style=False, allow_unicode=True)
        
        # 4. Marcar como completado
        completado_file = run_dir / ".completado"
        completado_file.touch()
        
        print(f"[Completado] Run {run_id} - {estrategia} - Pico: {resultados['pico_infectados']} - Tasa ataque: {resultados['tasa_ataque']:.2f}%")
        print(f"            ✓ Datos guardados en: {run_dir}")
        
    except Exception as e:
        print(f"[ERROR] Run {run_id} - Error al guardar resultados: {e}")
        # Crear archivo de error
        error_file = run_dir / ".error"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(str(e))
    
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
    
    # Crear directorio de salida con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir) / f"experimento_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar timestamp en archivo de referencia
    timestamp_file = output_dir / "timestamp.txt"
    with open(timestamp_file, 'w') as f:
        f.write(timestamp)
    
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
                'config': config,
                'output_dir': str(output_dir)  # Pasar directorio de salida
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
    
    # Consolidar resultados desde las carpetas guardadas
    print("Consolidando resultados...")
    resultados_summary = []
    dataframes_completos = []
    
    # Verificar qué simulaciones se completaron exitosamente
    completadas = 0
    fallidas = 0
    
    for resultado in resultados:
        # Eliminar carpeta del resultado para el summary
        carpeta = resultado.pop('carpeta', None)
        
        # Verificar si se completó
        if carpeta:
            run_dir = Path(carpeta)
            if (run_dir / ".completado").exists():
                completadas += 1
                # Leer datos desde archivo guardado
                df = pd.read_csv(run_dir / "datos_completos.csv", index_col=0)
                dataframes_completos.append(df)
            elif (run_dir / ".error").exists():
                fallidas += 1
                print(f"⚠ Run {resultado['run_id']} falló - ver {run_dir / '.error'}")
        
        # Agregar a resumen (sin importar si falló)
        resultados_summary.append(resultado)
    
    print(f"\n✓ Simulaciones completadas: {completadas}/{len(resultados)}")
    if fallidas > 0:
        print(f"✗ Simulaciones fallidas: {fallidas}")
    
    # Crear DataFrame resumen
    df_summary = pd.DataFrame(resultados_summary)
    
    # Guardar resumen consolidado
    summary_file = output_dir / "resumen_experimentos.csv"
    df_summary.to_csv(summary_file, index=False)
    print(f"\nResumen consolidado guardado en: {summary_file}")
    
    # Consolidar todos los dataframes (solo los que se completaron)
    if dataframes_completos:
        df_consolidado = pd.concat(dataframes_completos, ignore_index=True)
        consolidado_file = output_dir / "datos_consolidados.csv"
        df_consolidado.to_csv(consolidado_file, index=False)
        print(f"Datos consolidados guardados en: {consolidado_file}")
    else:
        print("⚠ No hay datos para consolidar")
    
    # Mostrar resumen por estrategia (solo si hay datos)
    if not df_summary.empty and 'estrategia' in df_summary.columns:
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
    config_file = output_dir / "configuracion.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump({
            'config_original': config,
            'seeds': args.seeds,
            'procesos': args.processes,
            'timestamp': timestamp,
            'total_simulaciones': len(resultados),
            'completadas': completadas,
            'fallidas': fallidas
        }, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Configuración guardada en: {config_file}")
    print(f"\n{'='*70}")
    print("EXPERIMENTO COMPLETADO")
    print(f"Resultados en: {output_dir}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
