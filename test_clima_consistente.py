"""
Test para verificar que los datos climáticos sean consistentes entre simulaciones.

Este script ejecuta la simulación dos veces con la misma semilla y compara
que la temperatura sea idéntica en ambas ejecuciones.
"""

from pathlib import Path
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from main import ejecutar_simulacion
import pandas as pd

def test_clima_consistente():
    """Verifica que la temperatura sea consistente entre simulaciones."""
    print("=" * 70)
    print("TEST: Consistencia de datos climáticos")
    print("=" * 70)
    
    # Ruta absoluta al CSV
    project_dir = Path(__file__).parent
    climate_csv_path = str(project_dir / 'data' / 'raw' / 'datos_climaticos_2022.csv')
    
    # Parámetros idénticos para ambas simulaciones
    params = {
        'steps': 20,
        'num_humanos': 50,
        'num_mosquitos': 100,
        'num_huevos': 30,
        'infectados_iniciales': 2,
        'seed': 42,  # Misma semilla
        'verbose': False,
        'climate_data_path': climate_csv_path
    }
    
    print("\n Ejecutando simulación 1...")
    modelo1 = ejecutar_simulacion(**params)
    datos1 = modelo1.datacollector.get_model_vars_dataframe()
    temp1 = datos1['Temperatura'].tolist()
    
    print("\n Ejecutando simulación 2...")
    modelo2 = ejecutar_simulacion(**params)
    datos2 = modelo2.datacollector.get_model_vars_dataframe()
    temp2 = datos2['Temperatura'].tolist()
    
    # Comparar temperaturas
    print("\n Comparando temperaturas...")
    print(f"   Simulación 1: {temp1[:5]} ...")
    print(f"   Simulación 2: {temp2[:5]} ...")
    
    diferencias = [abs(t1 - t2) for t1, t2 in zip(temp1, temp2)]
    max_diff = max(diferencias)
    
    print(f"\n Diferencia máxima: {max_diff:.6f}°C")
    
    if max_diff < 0.001:
        print("\n✅ ÉXITO: Las temperaturas son idénticas entre simulaciones")
        return True
    else:
        print("\n❌ ERROR: Las temperaturas difieren entre simulaciones")
        print(f"   Esto indica que se está usando clima sintético aleatorio")
        return False

if __name__ == "__main__":
    exito = test_clima_consistente()
    sys.exit(0 if exito else 1)
