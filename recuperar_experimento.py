#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para recuperar y consolidar resultados de experimentos parcialmente completados.

Uso:
    python recuperar_experimento.py --dir results/experiments/experimento_20241124_150000

Este script busca todas las simulaciones que se completaron exitosamente
y genera los archivos consolidados.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander
"""

import json
import argparse
from pathlib import Path
import pandas as pd
import yaml


def recuperar_experimento(experiment_dir):
    """
    Recupera y consolida resultados de un experimento parcialmente completado.
    
    Parameters
    ----------
    experiment_dir : Path
        Directorio del experimento
    """
    experiment_dir = Path(experiment_dir)
    
    if not experiment_dir.exists():
        print(f"❌ Error: El directorio {experiment_dir} no existe")
        return
    
    print(f"\n{'='*70}")
    print(f"RECUPERANDO EXPERIMENTO")
    print(f"Directorio: {experiment_dir}")
    print(f"{'='*70}\n")
    
    # Buscar todas las carpetas de simulaciones (run_XXX_...)
    run_dirs = sorted([d for d in experiment_dir.iterdir() if d.is_dir() and d.name.startswith('run_')])
    
    if not run_dirs:
        print("❌ No se encontraron simulaciones en el directorio")
        return
    
    print(f"📁 Simulaciones encontradas: {len(run_dirs)}\n")
    
    # Analizar estado de cada simulación
    completadas = []
    fallidas = []
    en_progreso = []
    
    for run_dir in run_dirs:
        run_id = run_dir.name
        
        if (run_dir / ".completado").exists():
            completadas.append(run_dir)
            print(f"✓ {run_id} - COMPLETADA")
        elif (run_dir / ".error").exists():
            fallidas.append(run_dir)
            print(f"✗ {run_id} - FALLIDA")
            # Mostrar error si existe
            with open(run_dir / ".error", 'r') as f:
                error_msg = f.read().strip()
                print(f"  Error: {error_msg}")
        else:
            en_progreso.append(run_dir)
            print(f"⏳ {run_id} - EN PROGRESO/INCOMPLETA")
    
    print(f"\n{'='*70}")
    print(f"RESUMEN")
    print(f"{'='*70}")
    print(f"✓ Completadas:  {len(completadas)}/{len(run_dirs)}")
    print(f"✗ Fallidas:     {len(fallidas)}/{len(run_dirs)}")
    print(f"⏳ En progreso: {len(en_progreso)}/{len(run_dirs)}")
    print(f"{'='*70}\n")
    
    if not completadas:
        print("❌ No hay simulaciones completadas para consolidar")
        return
    
    # Consolidar resultados de las simulaciones completadas
    print("📊 Consolidando resultados...")
    
    resultados_summary = []
    dataframes_completos = []
    
    for run_dir in completadas:
        try:
            # Leer resumen JSON
            with open(run_dir / "resumen.json", 'r', encoding='utf-8') as f:
                resumen = json.load(f)
            
            resultados_summary.append(resumen)
            
            # Leer datos completos
            df = pd.read_csv(run_dir / "datos_completos.csv", index_col=0)
            dataframes_completos.append(df)
            
        except Exception as e:
            print(f"⚠ Error al leer {run_dir.name}: {e}")
    
    # Crear DataFrame resumen
    df_summary = pd.DataFrame(resultados_summary)
    
    # Guardar resumen consolidado
    summary_file = experiment_dir / "resumen_experimentos_recuperado.csv"
    df_summary.to_csv(summary_file, index=False)
    print(f"✓ Resumen guardado en: {summary_file}")
    
    # Consolidar todos los dataframes
    if dataframes_completos:
        df_consolidado = pd.concat(dataframes_completos, ignore_index=True)
        consolidado_file = experiment_dir / "datos_consolidados_recuperado.csv"
        df_consolidado.to_csv(consolidado_file, index=False)
        print(f"✓ Datos consolidados guardados en: {consolidado_file}")
    
    # Mostrar resumen por estrategia
    if not df_summary.empty and 'estrategia' in df_summary.columns:
        print(f"\n{'='*70}")
        print("RESUMEN POR ESTRATEGIA")
        print(f"{'='*70}\n")
        
        summary_by_strategy = df_summary.groupby('estrategia').agg({
            'pico_infectados': ['mean', 'std', 'count'],
            'tasa_ataque': ['mean', 'std'],
            'mosquitos_finales': ['mean', 'std']
        }).round(2)
        
        print(summary_by_strategy)
        print()
    
    # Guardar metadata de recuperación
    metadata_file = experiment_dir / "recuperacion_metadata.yaml"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        yaml.dump({
            'total_simulaciones': len(run_dirs),
            'completadas': len(completadas),
            'fallidas': len(fallidas),
            'en_progreso': len(en_progreso),
            'simulaciones_completadas': [d.name for d in completadas],
            'simulaciones_fallidas': [d.name for d in fallidas],
            'simulaciones_en_progreso': [d.name for d in en_progreso]
        }, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✓ Metadata de recuperación guardada en: {metadata_file}")
    
    print(f"\n{'='*70}")
    print("RECUPERACIÓN COMPLETADA")
    print(f"{'='*70}\n")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Recuperar y consolidar resultados de experimentos parcialmente completados'
    )
    parser.add_argument(
        '--dir',
        type=str,
        required=True,
        help='Directorio del experimento a recuperar'
    )
    
    args = parser.parse_args()
    recuperar_experimento(args.dir)


if __name__ == '__main__':
    main()
