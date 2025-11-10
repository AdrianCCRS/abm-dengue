#!/usr/bin/env python3
"""
Batch runner script using Mesa batch_run (Mesa 2.3.4).

Usage:
  python scripts/batch_run.py --experiment config/experiments/example_batch.yaml --out results/batch1 --processes 4

The experiment YAML should contain:
  experiment:
    iterations: 3
    max_steps: 90
    fixed_params:
      width: 150
      height: 150
      climate_data_path: "data/clima_bucaramanga_2023.csv"
      config_file: "config/default_config.yaml"
    variable_params:
      num_humanos: [1000, 3000]
      num_mosquitos: [500, 1500]
"""
import argparse
import yaml
import os
import sys
from pathlib import Path
import multiprocessing
import json
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mesa import batch_run

# Import the model and enums
from src.model.dengue_model import DengueModel
from src.agents import EstadoSalud, EstadoMosquito


def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--experiment', required=True, help='YAML file describing experiment')
    p.add_argument('--out', default='results', help='Output directory')
    p.add_argument('--processes', type=int, default=max(1, multiprocessing.cpu_count() - 1))
    args = p.parse_args()

    exp = load_yaml(args.experiment)
    
    # Extract experiment config
    exp_config = exp.get('experiment', {})
    fixed_params = exp_config.get('fixed_params', {})
    variable_params = exp_config.get('variable_params', {})
    iterations = int(exp_config.get('iterations', 3))
    max_steps = int(exp_config.get('max_steps', 90))
    
    # Convert fecha_inicio from string to datetime if present
    if 'fecha_inicio' in fixed_params and isinstance(fixed_params['fecha_inicio'], str):
        fixed_params['fecha_inicio'] = datetime.strptime(fixed_params['fecha_inicio'], "%Y-%m-%d")
    
    # Load base config if config_file specified
    if 'config_file' in fixed_params:
        base_config_path = fixed_params['config_file']
        fixed_params['config_file'] = base_config_path  # Keep as path, model will load it

    # Prepare results dir
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Running batch_run with Mesa 2.3.4")
    print(f"   Iterations: {iterations}")
    print(f"   Max steps: {max_steps}")
    print(f"   Processes: {args.processes}")
    print(f"   Fixed params: {list(fixed_params.keys())}")
    print(f"   Variable params: {list(variable_params.keys())}")
    
    # Calculate total runs
    import itertools
    num_combinations = len(list(itertools.product(*variable_params.values())))
    total_runs = num_combinations * iterations
    print(f"   Total runs: {total_runs}\n")
    
    # Define model reporters
    model_reporters = {
        "Susceptibles": lambda m: m._contar_humanos_estado(EstadoSalud.SUSCEPTIBLE),
        "Expuestos": lambda m: m._contar_humanos_estado(EstadoSalud.EXPUESTO),
        "Infectados": lambda m: m._contar_humanos_estado(EstadoSalud.INFECTADO),
        "Recuperados": lambda m: m._contar_humanos_estado(EstadoSalud.RECUPERADO),
        "Mosquitos_S": lambda m: m._contar_mosquitos_estado(EstadoMosquito.SUSCEPTIBLE),
        "Mosquitos_I": lambda m: m._contar_mosquitos_estado(EstadoMosquito.INFECTADO),
        "Mosquitos_Total": lambda m: m._contar_mosquitos_adultos(),
        "Huevos": lambda m: m._contar_huevos(),
        "Temperatura": lambda m: m.temperatura_actual,
        "Precipitacion": lambda m: m.precipitacion_actual,
    }
    
    # Run batch_run (Mesa 2.3.4 API)
    print("⏳ Ejecutando simulaciones en paralelo...")
    results = batch_run(
        DengueModel,
        parameters={**fixed_params, **variable_params},
        iterations=iterations,
        max_steps=max_steps,
        number_processes=args.processes,
        data_collection_period=1,
        display_progress=True,
    )
    
    print(f"\n✅ Batch completado! {len(results)} filas de datos")
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Add model reporters manually (batch_run returns raw data)
    # Note: batch_run in Mesa 2.3.4 returns datacollector data directly
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_out = out_dir / f'batch_results_{timestamp}.csv'
    results_df.to_csv(csv_out, index=False)
    print(f"💾 Resultados guardados en: {csv_out}")
    
    # Save experiment config
    config_out = out_dir / f'batch_config_{timestamp}.yaml'
    with open(config_out, 'w', encoding='utf-8') as f:
        yaml.dump(exp, f, default_flow_style=False, allow_unicode=True)
    print(f"💾 Configuración guardada en: {config_out}")
    
    # Print summary
    print(f"\n📊 Resumen de resultados:")
    print(f"   Total filas: {len(results_df)}")
    print(f"   Columnas: {list(results_df.columns)}")
    
    print('\n✅ Proceso completado exitosamente!')


if __name__ == '__main__':
    main()
