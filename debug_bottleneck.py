# -*- coding: utf-8 -*-
"""
Script de debugging detallado para identificar cuellos de botella.

Agrega timing detallado a cada operación del step() para ver
exactamente dónde se pierde el tiempo.

Uso:
    python debug_bottleneck.py --steps 3
"""

import time
import sys
import os
from pathlib import Path
from collections import defaultdict

# Agregar directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Importar directamente desde src
from src.model.dengue_model import DengueModel
from src.agents.mosquito_agent import MosquitoAgent
from src.agents.human_agent import HumanAgent


class BottleneckDebugger:
    """Debugger para identificar cuellos de botella"""
    
    def __init__(self):
        self.timings = defaultdict(lambda: {'count': 0, 'total': 0.0, 'max': 0.0})
        self.step_timings = []
    
    def time_operation(self, operation_name, func, *args, **kwargs):
        """Ejecuta función y mide tiempo"""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        
        self.timings[operation_name]['count'] += 1
        self.timings[operation_name]['total'] += elapsed
        self.timings[operation_name]['max'] = max(
            self.timings[operation_name]['max'], 
            elapsed
        )
        
        return result
    
    def instrument_model(self, model):
        """Instrumenta el modelo para debugging"""
        # Guardar métodos originales
        original_mosquito_step = MosquitoAgent.step
        original_mosquito_mover = MosquitoAgent.mover
        original_mosquito_picar = MosquitoAgent.intentar_picar
        original_mosquito_reproduccion = MosquitoAgent.intentar_reproduccion
        original_mosquito_buscar_humano = MosquitoAgent.buscar_humano_cercano
        original_mosquito_buscar_sitio = MosquitoAgent._buscar_sitio_cria
        
        original_human_step = HumanAgent.step
        original_human_movilidad = HumanAgent.ejecutar_movilidad_diaria
        
        debugger = self
        
        # Instrumentar mosquitos
        def mosquito_step_debug(self):
            return debugger.time_operation('mosquito_step_total', original_mosquito_step, self)
        
        def mosquito_mover_debug(self):
            return debugger.time_operation('mosquito_mover', original_mosquito_mover, self)
        
        def mosquito_picar_debug(self):
            return debugger.time_operation('mosquito_picar', original_mosquito_picar, self)
        
        def mosquito_reproduccion_debug(self):
            return debugger.time_operation('mosquito_reproduccion', original_mosquito_reproduccion, self)
        
        def mosquito_buscar_humano_debug(self):
            return debugger.time_operation('mosquito_buscar_humano', original_mosquito_buscar_humano, self)
        
        def mosquito_buscar_sitio_debug(self):
            return debugger.time_operation('mosquito_buscar_sitio', original_mosquito_buscar_sitio, self)
        
        # Instrumentar humanos
        def human_step_debug(self):
            return debugger.time_operation('human_step_total', original_human_step, self)
        
        def human_movilidad_debug(self):
            return debugger.time_operation('human_movilidad', original_human_movilidad, self)
        
        # Aplicar instrumentación
        MosquitoAgent.step = mosquito_step_debug
        MosquitoAgent.mover = mosquito_mover_debug
        MosquitoAgent.intentar_picar = mosquito_picar_debug
        MosquitoAgent.intentar_reproduccion = mosquito_reproduccion_debug
        MosquitoAgent.buscar_humano_cercano = mosquito_buscar_humano_debug
        MosquitoAgent._buscar_sitio_cria = mosquito_buscar_sitio_debug
        
        HumanAgent.step = human_step_debug
        HumanAgent.ejecutar_movilidad_diaria = human_movilidad_debug
    
    def print_report(self):
        """Imprime reporte de timing"""
        print("\n" + "="*80)
        print("REPORTE DE CUELLOS DE BOTELLA")
        print("="*80)
        
        # Ordenar por tiempo total
        sorted_timings = sorted(
            self.timings.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )
        
        print(f"\n{'Operación':<30} {'Llamadas':>10} {'Total (s)':>12} {'Promedio (ms)':>15} {'Máximo (ms)':>15}")
        print("-"*80)
        
        total_time = sum(t['total'] for t in self.timings.values())
        
        for operation, stats in sorted_timings:
            avg_ms = (stats['total'] / stats['count'] * 1000) if stats['count'] > 0 else 0
            max_ms = stats['max'] * 1000
            percentage = (stats['total'] / total_time * 100) if total_time > 0 else 0
            
            print(f"{operation:<30} {stats['count']:>10} {stats['total']:>12.2f} "
                  f"{avg_ms:>15.2f} {max_ms:>15.2f}  ({percentage:>5.1f}%)")
        
        print(f"\n{'TOTAL':<30} {'':<10} {total_time:>12.2f}s")
        
        # Análisis de pasos
        if self.step_timings:
            print("\n" + "="*80)
            print("TIEMPO POR PASO DE SIMULACIÓN")
            print("="*80)
            
            for i, (step_time, mosquitos, humanos) in enumerate(self.step_timings, 1):
                print(f"Paso {i}: {step_time:.2f}s | Mosquitos: {mosquitos} | Humanos: {humanos}")
            
            avg_step = sum(t[0] for t in self.step_timings) / len(self.step_timings)
            print(f"\nPromedio: {avg_step:.2f}s/paso")


def run_debug(num_steps=3):
    """Ejecuta simulación con debugging"""
    print("="*80)
    print("DEBUGGING DE CUELLOS DE BOTELLA - ABM DENGUE")
    print("="*80)
    
    root_dir = Path(__file__).parent
    config_path = root_dir / 'config' / 'default_config.yaml'
    
    print(f"\nCargando configuración desde {config_path}...")
    
    # Cargar configuración para obtener climate_data_path
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    climate_data_path = config.get('climate_data_path', 'data/raw/datos_climaticos_2022.csv')
    
    # Convertir a ruta absoluta si es relativa
    if not Path(climate_data_path).is_absolute():
        climate_data_path = str(root_dir / climate_data_path)
    
    # Override fecha_inicio para que coincida con los datos disponibles (2022)
    from datetime import datetime
    
    print(f"Creando modelo con datos climáticos: {climate_data_path}...")
    print(f"Nota: Usando fecha_inicio=2022-01-01 para coincidir con datos disponibles")
    
    model = DengueModel(
        config_file=str(config_path),
        climate_data_path=climate_data_path,
        fecha_inicio=datetime(2022, 1, 1)  # Override para usar datos de 2022
    )
    
    # Crear debugger e instrumentar
    debugger = BottleneckDebugger()
    debugger.instrument_model(model)
    
    print(f"Ejecutando {num_steps} pasos con debugging detallado...\n")
    
    for i in range(num_steps):
        print(f"--- Paso {i+1}/{num_steps} ---")
        
        step_start = time.time()
        model.step()
        step_elapsed = time.time() - step_start
        
        mosquitos = sum(1 for a in model.agents if isinstance(a, MosquitoAgent))
        humanos = sum(1 for a in model.agents if isinstance(a, HumanAgent))
        
        debugger.step_timings.append((step_elapsed, mosquitos, humanos))
        
        print(f"Completado en {step_elapsed:.2f}s | "
              f"Mosquitos: {mosquitos} | Humanos: {humanos}\n")
    
    # Imprimir reporte
    debugger.print_report()
    
    # Identificar top bottleneck
    print("\n" + "="*80)
    print("CONCLUSIÓN")
    print("="*80)
    
    sorted_timings = sorted(
        debugger.timings.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    if sorted_timings:
        top_bottleneck = sorted_timings[0]
        total_time = sum(t['total'] for t in debugger.timings.values())
        percentage = (top_bottleneck[1]['total'] / total_time * 100)
        
        print(f"\n🔴 CUELLO DE BOTELLA PRINCIPAL:")
        print(f"   {top_bottleneck[0]}")
        print(f"   Tiempo: {top_bottleneck[1]['total']:.2f}s ({percentage:.1f}% del total)")
        print(f"   Llamadas: {top_bottleneck[1]['count']}")
        print(f"   Promedio: {top_bottleneck[1]['total']/top_bottleneck[1]['count']*1000:.2f}ms por llamada")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Debugging de cuellos de botella')
    parser.add_argument('--steps', type=int, default=3, help='Número de pasos')
    args = parser.parse_args()
    
    run_debug(args.steps)
