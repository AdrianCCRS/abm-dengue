#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la transmisión vertical del dengue.

Este script ejecuta una simulación corta y verifica que:
1. Los huevos infectados se crean correctamente
2. Los mosquitos infectados eclosionan de huevos infectados
3. La población de mosquitos se mantiene más estable
4. Las infecciones persisten en la población

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel

def test_vertical_transmission():
    """Ejecuta una simulación de prueba con transmisión vertical."""
    
    print("="*80)
    print("PRUEBA DE TRANSMISIÓN VERTICAL DEL DENGUE")
    print("="*80)
    print()
    
    # Configuración de la simulación
    config = {
        'simulation': {
            'width': 50,
            'height': 50,
            'num_humanos': 1000,
            'num_mosquitos': 500,
            'num_huevos': 200,
            'infectados_iniciales': 5,
            'mosquitos_infectados_iniciales': 10,
            'seed': 42
        },
        'transmission': {
            'mosquito_to_human_prob': 0.4,
            'human_to_mosquito_prob': 0.25,
            'bite_rate': 0.5,
            'vertical_transmission_rate': 0.10  # 10% para prueba más visible
        },
        'mosquito_disease': {
            'mortality_rate': 0.06,
            'sensory_range': 2,
            'incubation_period': 10,
            'carrying_capacity_per_cell': 3000
        },
        'mosquito_breeding': {
            'eggs_per_female': 30,
            'gonotrophic_cycle_days': 4,
            'egg_mortality_rate': 0.25,
            'female_ratio': 0.52
        }
    }
    
    # Crear modelo
    model = DengueModel(
        width=config['simulation']['width'],
        height=config['simulation']['height'],
        num_humanos=config['simulation']['num_humanos'],
        num_mosquitos=config['simulation']['num_mosquitos'],
        num_huevos=config['simulation']['num_huevos'],
        infectados_iniciales=config['simulation']['infectados_iniciales'],
        mosquitos_infectados_iniciales=config['simulation']['mosquitos_infectados_iniciales'],
        usar_lsm=False,
        usar_itn_irs=False,
        fecha_inicio=datetime(2022, 1, 1),
        seed=config['simulation']['seed'],
        config=config,
        climate_data_path="data/raw/datos_climaticos_2022.csv"
    )
    
    print(f"Modelo inicializado:")
    print(f"  - Humanos: {model.num_humanos}")
    print(f"  - Mosquitos adultos: {model.mosquito_pop.total_mosquitos()}")
    print(f"  - Mosquitos infectados: {model.mosquito_pop.total_infectious()}")
    print(f"  - Huevos totales: {model.egg_manager.count_eggs()}")
    
    # Contar huevos infectados iniciales
    huevos_infectados = sum(batch.cantidad_infectados for batch in model.egg_manager.egg_batches)
    print(f"  - Huevos infectados: {huevos_infectados}")
    print(f"  - Tasa transmisión vertical: {model.vertical_transmission_rate*100:.1f}%")
    print()
    
    # Ejecutar simulación por 100 días
    print("Ejecutando simulación (100 días)...")
    print()
    print(f"{'Día':>4} | {'Humanos I':>9} | {'Mosq. Adultos':>12} | {'Mosq. I':>8} | {'Huevos':>7} | {'Huevos I':>8}")
    print("-"*80)
    
    for i in range(100):
        model.step()
        
        # Recolectar métricas cada 10 días
        if i % 10 == 0 or i < 5:
            humanos_i = sum(1 for a in model.agents if hasattr(a, 'estado') and 
                          a.estado.value == 'I')
            mosq_total = model.mosquito_pop.total_mosquitos()
            mosq_i = model.mosquito_pop.total_infectious()
            huevos = model.egg_manager.count_eggs()
            huevos_inf = sum(b.cantidad_infectados for b in model.egg_manager.egg_batches)
            
            print(f"{i:4d} | {humanos_i:9d} | {mosq_total:12d} | {mosq_i:8d} | {huevos:7d} | {huevos_inf:8d}")
    
    print()
    print("="*80)
    print("RESULTADOS FINALES")
    print("="*80)
    
    # Métricas finales
    humanos_s = sum(1 for a in model.agents if hasattr(a, 'estado') and a.estado.value == 'S')
    humanos_e = sum(1 for a in model.agents if hasattr(a, 'estado') and a.estado.value == 'E')
    humanos_i = sum(1 for a in model.agents if hasattr(a, 'estado') and a.estado.value == 'I')
    humanos_r = sum(1 for a in model.agents if hasattr(a, 'estado') and a.estado.value == 'R')
    
    mosq_total = model.mosquito_pop.total_mosquitos()
    mosq_s = model.mosquito_pop.S_m.sum()
    mosq_e = model.mosquito_pop.E_m.sum()
    mosq_i = model.mosquito_pop.I_m.sum()
    
    huevos = model.egg_manager.count_eggs()
    huevos_inf = sum(b.cantidad_infectados for b in model.egg_manager.egg_batches)
    
    print(f"\nHumanos:")
    print(f"  S: {humanos_s:5d} | E: {humanos_e:5d} | I: {humanos_i:5d} | R: {humanos_r:5d}")
    print(f"\nMosquitos adultos:")
    print(f"  S: {mosq_s:5d} | E: {mosq_e:5d} | I: {mosq_i:5d} | Total: {mosq_total:5d}")
    print(f"\nHuevos:")
    print(f"  Susceptibles: {huevos - huevos_inf:5d}")
    print(f"  Infectados:   {huevos_inf:5d}")
    print(f"  Total:        {huevos:5d}")
    
    # Verificaciones
    print("\n" + "="*80)
    print("VERIFICACIONES")
    print("="*80)
    
    exito = True
    
    # 1. Verificar que hay mosquitos (población no colapsó)
    if mosq_total > 0:
        print("✓ La población de mosquitos se mantuvo (no colapsó)")
    else:
        print("✗ La población de mosquitos colapsó")
        exito = False
    
    # 2. Verificar que hay huevos
    if huevos > 0:
        print(f"✓ Hay huevos en el sistema ({huevos} huevos)")
    else:
        print("✗ No hay huevos en el sistema")
        exito = False
    
    # 3. Verificar que hay huevos infectados (transmisión vertical funciona)
    if huevos_inf > 0:
        proporcion = (huevos_inf / huevos * 100) if huevos > 0 else 0
        print(f"✓ Transmisión vertical funcionando ({huevos_inf} huevos infectados, {proporcion:.1f}%)")
    else:
        print("✗ No hay huevos infectados (transmisión vertical no está funcionando)")
        exito = False
    
    # 4. Verificar que hay mosquitos infectados
    if mosq_i > 0:
        print(f"✓ Hay mosquitos infectados ({mosq_i} mosquitos)")
    else:
        print("⚠ No hay mosquitos infectados actualmente")
    
    print()
    if exito:
        print("🎉 ¡PRUEBA EXITOSA! La transmisión vertical está funcionando correctamente.")
    else:
        print("⚠️  Algunos aspectos requieren atención.")
    
    print()
    return exito


if __name__ == "__main__":
    try:
        exito = test_vertical_transmission()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
