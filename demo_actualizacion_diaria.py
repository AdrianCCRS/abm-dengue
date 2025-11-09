"""
Demostración de cómo el modelo actualiza el clima día a día desde CSV.

Este script muestra que cada paso de simulación obtiene automáticamente
los datos climáticos del CSV para ese día específico.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.climate_data import ClimateDataLoader


def simular_actualizacion_clima():
    """Simula cómo el modelo actualiza el clima cada día."""
    print("\n" + "=" * 70)
    print("DEMOSTRACIÓN: Actualización Diaria de Clima desde CSV")
    print("=" * 70 + "\n")
    
    # Cargar datos climáticos (esto es lo que hace el modelo internamente)
    csv_path = "data/raw/datos_climaticos_2022.csv"
    climate_loader = ClimateDataLoader(csv_path)
    print(f"✓ Cargador de datos inicializado con: {csv_path}\n")
    
    # Simular 30 días de simulación
    fecha_inicio = datetime(2022, 1, 1)
    print(f"Fecha de inicio de simulación: {fecha_inicio.date()}")
    print(f"Simulando 30 días...\n")
    
    print("=" * 70)
    print(f"{'Día':<5} | {'Fecha':<12} | {'Temp (°C)':<10} | {'Precip (mm)':<12} | Observaciones")
    print("-" * 70)
    
    # Variables para el modelo (simulando lo que hace DengueModel)
    use_csv_climate = True
    temperatura_actual = 25.0  # valor inicial
    precipitacion_actual = 0.0  # valor inicial
    
    for dia_simulacion in range(30):
        # Esto es lo que hace model.step() cada día:
        # 1. Calcular la fecha actual
        from datetime import timedelta
        fecha_actual = fecha_inicio + timedelta(days=dia_simulacion)
        
        # 2. Actualizar clima (esto es _actualizar_clima())
        if use_csv_climate and climate_loader:
            try:
                # Obtener datos desde CSV para esta fecha específica
                temp, precip = climate_loader.get_climate_data(fecha_actual)
                temperatura_actual = temp
                precipitacion_actual = precip
                observacion = "Datos desde CSV"
            except KeyError:
                # Fallback a modelo sintético
                observacion = "⚠ Sin datos, sintético"
        
        # 3. Determinar si hay lluvia
        lluvia = "☔ Lluvia" if precipitacion_actual > 0 else "☀ Seco"
        
        # Mostrar resultados
        print(f"{dia_simulacion+1:<5} | {fecha_actual.date()} | {temperatura_actual:10.1f} | "
              f"{precipitacion_actual:12.1f} | {lluvia} - {observacion}")
    
    print("=" * 70)
    print("\n✓ Como puedes ver, cada día obtiene datos diferentes del CSV")
    print("✓ La temperatura y precipitación varían según los datos reales de 2022")
    print("✓ Esto afecta directamente la reproducción y supervivencia de mosquitos\n")
    
    # Mostrar impacto en la simulación
    print("=" * 70)
    print("IMPACTO EN LA SIMULACIÓN")
    print("=" * 70)
    print("""
Los datos climáticos diarios afectan:

1. Reproducción de mosquitos:
   - Más lluvia → Más criaderos disponibles
   - Temperatura óptima (25°C) → Mayor tasa de reproducción

2. Maduración de huevos:
   - Temperatura alta → Desarrollo más rápido
   - Temperatura baja → Desarrollo más lento

3. Mortalidad de mosquitos:
   - Afectada por temperatura extrema
   - Condiciones desfavorables reducen supervivencia

4. Ciclo de transmisión:
   - Clima favorable → Mayor actividad de mosquitos
   - Mayor contacto → Mayor transmisión de dengue
""")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    simular_actualizacion_clima()
