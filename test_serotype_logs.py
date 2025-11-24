#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar logs de serotipos.

Ejecuta una simulación de 30 días y muestra logs detallados
de la configuración y evolución de serotipos.

Uso:
    python test_serotype_logs.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel

def main():
    print("\n" + "="*70)
    print("PRUEBA DE LOGS DE SEROTIPOS")
    print("="*70)
    
    print("\nEjecutando simulación de 30 días con logs detallados...")
    print("Los logs mostrarán:")
    print("  • Configuración inicial de serotipos")
    print("  • Distribución de infectados por serotipo (cada 10 días)")
    print("  • Evolución de inmunidad poblacional")
    print("  • Reinfecciones detectadas")
    
    try:
        # Crear modelo
        model = DengueModel(
            width=50,
            height=50,
            num_humanos=1000,
            num_mosquitos=200,
            num_huevos=50,
            infectados_iniciales=20,
            mosquitos_infectados_iniciales=10,
            fecha_inicio=datetime(2022, 1, 1),
            seed=42,
            config_file='config/default_config.yaml',
            climate_data_path='data/raw/datos_climaticos_2022.csv'
        )
        
        # Ejecutar 30 pasos
        print("\n" + "="*70)
        print("INICIANDO SIMULACIÓN")
        print("="*70)
        
        for i in range(30):
            model.step()
        
        print("\n" + "="*70)
        print("SIMULACIÓN COMPLETADA")
        print("="*70)
        
        # Resumen final
        df = model.datacollector.get_model_vars_dataframe()
        ultimo_dia = df.iloc[-1]
        
        print(f"\nResumen final (día 30):")
        print(f"  Susceptibles: {int(ultimo_dia['Susceptibles'])}")
        print(f"  Expuestos: {int(ultimo_dia['Expuestos'])}")
        print(f"  Infectados: {int(ultimo_dia['Infectados'])}")
        print(f"  Recuperados: {int(ultimo_dia['Recuperados'])}")
        
        print(f"\n  Infectados por serotipo:")
        print(f"    DENV-1: {int(ultimo_dia['Infectados_S1'])}")
        print(f"    DENV-2: {int(ultimo_dia['Infectados_S2'])}")
        print(f"    DENV-3: {int(ultimo_dia['Infectados_S3'])}")
        print(f"    DENV-4: {int(ultimo_dia['Infectados_S4'])}")
        
        print(f"\n  Distribución de inmunidad:")
        print(f"    0 infecciones: {int(ultimo_dia['Inmunes_0'])}")
        print(f"    1 infección: {int(ultimo_dia['Inmunes_1'])}")
        print(f"    2 infecciones: {int(ultimo_dia['Inmunes_2'])}")
        print(f"    3 infecciones: {int(ultimo_dia['Inmunes_3'])}")
        print(f"    4 infecciones: {int(ultimo_dia['Inmunes_4'])}")
        
        print("\n✓ Prueba completada exitosamente")
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
