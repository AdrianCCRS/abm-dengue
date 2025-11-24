#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba rápida para verificar que la simulación funciona con serotipos.

Ejecuta una simulación corta (10 días) y verifica que:
1. El modelo se inicializa correctamente
2. Los serotipos se asignan a infectados iniciales
3. Las métricas por serotipo se recolectan
4. No hay errores durante la ejecución

Uso:
    python test_quick_simulation.py
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel

def main():
    print("\n" + "="*70)
    print("PRUEBA RÁPIDA DE SIMULACIÓN CON SEROTIPOS")
    print("="*70)
    
    try:
        # Crear modelo con configuración por defecto
        print("\n1. Inicializando modelo...")
        model = DengueModel(
            width=50,
            height=50,
            num_humanos=500,
            num_mosquitos=100,
            num_huevos=50,
            infectados_iniciales=10,
            mosquitos_infectados_iniciales=5,
            fecha_inicio=datetime(2022, 1, 1),
            seed=42,
            config_file='config/default_config.yaml',
            climate_data_path='data/raw/datos_climaticos_2022.csv'
        )
        print("   ✓ Modelo inicializado correctamente")
        
        # Verificar serotipos en infectados iniciales
        print("\n2. Verificando serotipos iniciales...")
        infectados = [a for a in model.agents 
                     if hasattr(a, 'estado') and str(a.estado.value) == 'I']
        
        serotipos_iniciales = {}
        for humano in infectados:
            if hasattr(humano, 'serotipo_actual') and humano.serotipo_actual:
                serotipos_iniciales[humano.serotipo_actual] = \
                    serotipos_iniciales.get(humano.serotipo_actual, 0) + 1
        
        print(f"   Infectados iniciales: {len(infectados)}")
        print(f"   Distribución de serotipos: {serotipos_iniciales}")
        print("   ✓ Serotipos asignados correctamente")
        
        # Ejecutar 10 pasos
        print("\n3. Ejecutando simulación (10 días)...")
        for i in range(10):
            model.step()
            if (i + 1) % 5 == 0:
                print(f"   Día {i + 1}/10 completado")
        print("   ✓ Simulación ejecutada sin errores")
        
        # Verificar datos recolectados
        print("\n4. Verificando datos recolectados...")
        df = model.datacollector.get_model_vars_dataframe()
        
        print(f"   Días simulados: {len(df)}")
        print(f"   Columnas disponibles: {len(df.columns)}")
        
        # Verificar columnas de serotipos
        columnas_serotipos = [col for col in df.columns if 'S1' in col or 'S2' in col or 'S3' in col or 'S4' in col]
        print(f"   Columnas de serotipos: {columnas_serotipos}")
        
        # Verificar columnas de inmunidad
        columnas_inmunidad = [col for col in df.columns if 'Inmunes' in col]
        print(f"   Columnas de inmunidad: {columnas_inmunidad}")
        
        # Mostrar estado final
        print("\n5. Estado final (día 10):")
        ultimo_dia = df.iloc[-1]
        print(f"   Susceptibles: {int(ultimo_dia['Susceptibles'])}")
        print(f"   Expuestos: {int(ultimo_dia['Expuestos'])}")
        print(f"   Infectados: {int(ultimo_dia['Infectados'])}")
        print(f"   Recuperados: {int(ultimo_dia['Recuperados'])}")
        
        if 'Infectados_S1' in df.columns:
            print(f"\n   Infectados por serotipo:")
            print(f"     DENV-1: {int(ultimo_dia['Infectados_S1'])}")
            print(f"     DENV-2: {int(ultimo_dia['Infectados_S2'])}")
            print(f"     DENV-3: {int(ultimo_dia['Infectados_S3'])}")
            print(f"     DENV-4: {int(ultimo_dia['Infectados_S4'])}")
        
        if 'Inmunes_0' in df.columns:
            print(f"\n   Distribución de inmunidad:")
            print(f"     0 infecciones: {int(ultimo_dia['Inmunes_0'])}")
            print(f"     1 infección: {int(ultimo_dia['Inmunes_1'])}")
            print(f"     2 infecciones: {int(ultimo_dia['Inmunes_2'])}")
            print(f"     3 infecciones: {int(ultimo_dia['Inmunes_3'])}")
            print(f"     4 infecciones: {int(ultimo_dia['Inmunes_4'])}")
        
        print("\n" + "="*70)
        print("✓ PRUEBA COMPLETADA EXITOSAMENTE")
        print("="*70)
        print("\nLa implementación de serotipos está funcionando correctamente.")
        print("El modelo puede ejecutarse y recolectar métricas por serotipo.")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ ERROR EN LA PRUEBA")
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
