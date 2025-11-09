"""
Ejemplo simple del uso del cargador de datos climáticos.

Este script demuestra cómo usar el ClimateDataLoader para
acceder a datos climáticos históricos desde archivos CSV.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.climate_data import ClimateDataLoader


def main():
    print("\n" + "=" * 70)
    print("EJEMPLO: Uso del Cargador de Datos Climáticos")
    print("=" * 70 + "\n")
    
    # 1. Cargar datos climáticos
    print("1. Cargando datos climáticos desde CSV...")
    csv_path = "data/raw/datos_climaticos_2022.csv"
    
    try:
        loader = ClimateDataLoader(csv_path)
        print(f"   ✓ Datos cargados exitosamente\n")
    except Exception as e:
        print(f"   ✗ Error al cargar datos: {e}")
        return
    
    # 2. Obtener rango de fechas disponible
    print("2. Rango de fechas disponibles:")
    fecha_min, fecha_max = loader.get_date_range()
    print(f"   Desde: {fecha_min.date()}")
    print(f"   Hasta: {fecha_max.date()}")
    print(f"   Total: {(fecha_max - fecha_min).days + 1} días\n")
    
    # 3. Obtener datos para fechas específicas
    print("3. Datos climáticos de ejemplo:\n")
    
    fechas_ejemplo = [
        (datetime(2022, 1, 15), "Enero - Época seca"),
        (datetime(2022, 4, 20), "Abril - Primera temporada de lluvias"),
        (datetime(2022, 7, 10), "Julio - Verano"),
        (datetime(2022, 10, 25), "Octubre - Segunda temporada de lluvias"),
    ]
    
    for fecha, descripcion in fechas_ejemplo:
        temp, precip = loader.get_climate_data(fecha)
        print(f"   {fecha.strftime('%Y-%m-%d')} ({descripcion})")
        print(f"   └─ Temperatura: {temp:5.1f}°C")
        print(f"   └─ Precipitación: {precip:5.1f} mm\n")
    
    # 4. Simular una semana de datos
    print("4. Simulación de una semana (ene 1-7, 2022):\n")
    print("   Fecha       | Temp (°C) | Precip (mm)")
    print("   " + "-" * 42)
    
    fecha_inicio = datetime(2022, 1, 1)
    for i in range(7):
        fecha = fecha_inicio + timedelta(days=i)
        temp, precip = loader.get_climate_data(fecha)
        print(f"   {fecha.strftime('%Y-%m-%d')} | {temp:8.1f}  | {precip:10.1f}")
    
    # 5. Estadísticas básicas
    print("\n5. Estadísticas del año 2022:")
    
    temperaturas = []
    precipitaciones = []
    dias_lluvia = 0
    
    fecha = fecha_min
    while fecha <= fecha_max:
        temp, precip = loader.get_climate_data(fecha)
        temperaturas.append(temp)
        precipitaciones.append(precip)
        if precip > 0:
            dias_lluvia += 1
        fecha += timedelta(days=1)
    
    temp_promedio = sum(temperaturas) / len(temperaturas)
    temp_min = min(temperaturas)
    temp_max = max(temperaturas)
    precip_total = sum(precipitaciones)
    precip_promedio = precip_total / len(precipitaciones)
    
    print(f"\n   Temperatura:")
    print(f"   └─ Promedio: {temp_promedio:.1f}°C")
    print(f"   └─ Mínima:   {temp_min:.1f}°C")
    print(f"   └─ Máxima:   {temp_max:.1f}°C")
    
    print(f"\n   Precipitación:")
    print(f"   └─ Total:    {precip_total:.1f} mm")
    print(f"   └─ Promedio: {precip_promedio:.1f} mm/día")
    print(f"   └─ Días con lluvia: {dias_lluvia} ({dias_lluvia/len(precipitaciones)*100:.1f}%)")
    
    # 6. Verificar disponibilidad de fecha
    print("\n6. Verificación de disponibilidad de fechas:")
    
    fechas_prueba = [
        datetime(2022, 6, 15),
        datetime(2023, 1, 1),
        datetime(2021, 12, 31),
    ]
    
    for fecha in fechas_prueba:
        disponible = loader.has_date(fecha)
        status = "✓ Disponible" if disponible else "✗ No disponible"
        print(f"   {fecha.strftime('%Y-%m-%d')}: {status}")
    
    print("\n" + "=" * 70)
    print("Ejemplo completado exitosamente")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
