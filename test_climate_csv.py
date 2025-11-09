"""
Script de prueba para verificar la carga de datos climáticos desde CSV.

Este script prueba el módulo ClimateDataLoader y el modelo DengueModel
con datos climáticos reales desde archivo CSV.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.climate_data import ClimateDataLoader
from src.model.dengue_model import DengueModel


def test_climate_loader():
    """Prueba básica del cargador de datos climáticos."""
    print("=" * 60)
    print("PRUEBA 1: Cargador de datos climáticos")
    print("=" * 60)
    
    csv_path = "data/raw/datos_climaticos_2022.csv"
    
    try:
        # Cargar datos
        loader = ClimateDataLoader(csv_path)
        print(f"✓ Datos climáticos cargados exitosamente desde {csv_path}")
        
        # Obtener rango de fechas
        fecha_min, fecha_max = loader.get_date_range()
        print(f"✓ Rango de datos: {fecha_min.date()} a {fecha_max.date()}")
        
        # Probar obtener datos para algunas fechas
        test_dates = [
            datetime(2022, 1, 1),
            datetime(2022, 6, 15),
            datetime(2022, 12, 31)
        ]
        
        print("\nDatos climáticos de ejemplo:")
        for date in test_dates:
            temp, precip = loader.get_climate_data(date)
            print(f"  {date.date()}: Temp={temp:.1f}°C, Precip={precip:.1f}mm")
        
        print("\n✓ Prueba del cargador completada exitosamente\n")
        return True
        
    except Exception as e:
        print(f"✗ Error en prueba del cargador: {e}\n")
        return False


def test_model_with_csv():
    """Prueba el modelo con datos climáticos desde CSV."""
    print("=" * 60)
    print("PRUEBA 2: Modelo con datos climáticos desde CSV")
    print("=" * 60)
    
    try:
        # Crear modelo con datos climáticos desde CSV
        model = DengueModel(
            width=10,
            height=10,
            num_humanos=50,
            num_mosquitos=100,
            num_huevos=50,
            infectados_iniciales=2,
            mosquitos_infectados_iniciales=2,
            fecha_inicio=datetime(2022, 1, 1),
            climate_data_path="data/raw/datos_climaticos_2022.csv",
            seed=42
        )
        
        print(f"✓ Modelo creado exitosamente")
        print(f"  - Usando datos CSV: {model.use_csv_climate}")
        print(f"  - Fecha inicial: {model.fecha_actual.date()}")
        print(f"  - Temperatura inicial: {model.temperatura_actual:.1f}°C")
        print(f"  - Precipitación inicial: {model.precipitacion_actual:.1f}mm")
        
        # Ejecutar algunos pasos
        print("\nEjecutando 10 días de simulación...")
        for i in range(10):
            model.step()
            if i % 3 == 0:
                print(f"  Día {i+1}: Temp={model.temperatura_actual:.1f}°C, "
                      f"Precip={model.precipitacion_actual:.1f}mm")
        
        print(f"\n✓ Simulación completada")
        print(f"  - Fecha final: {model.fecha_actual.date()}")
        print(f"  - Infectados: {sum(1 for a in model.agents if hasattr(a, 'estado') and a.estado.name == 'INFECTADO')}")
        print(f"  - Mosquitos: {sum(1 for a in model.agents if hasattr(a, 'tipo') and a.tipo == 'mosquito' and a.etapa_vida.name == 'ADULTO')}")
        
        print("\n✓ Prueba del modelo completada exitosamente\n")
        return True
        
    except Exception as e:
        print(f"✗ Error en prueba del modelo: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_model_with_config():
    """Prueba el modelo con archivo de configuración."""
    print("=" * 60)
    print("PRUEBA 3: Modelo con archivo de configuración")
    print("=" * 60)
    
    try:
        # Crear modelo usando archivo de configuración
        model = DengueModel(
            width=10,
            height=10,
            num_humanos=50,
            num_mosquitos=100,
            fecha_inicio=datetime(2022, 1, 1),
            config_file="config/simulation_config.yaml",
            seed=42
        )
        
        print(f"✓ Modelo creado desde configuración")
        print(f"  - Usando datos CSV: {model.use_csv_climate}")
        print(f"  - Temperatura inicial: {model.temperatura_actual:.1f}°C")
        
        # Ejecutar un paso
        model.step()
        print(f"  - Temperatura día 1: {model.temperatura_actual:.1f}°C")
        
        print("\n✓ Prueba con configuración completada exitosamente\n")
        return True
        
    except Exception as e:
        print(f"✗ Error en prueba con configuración: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRUEBAS DE DATOS CLIMÁTICOS DESDE CSV")
    print("=" * 60 + "\n")
    
    results = []
    
    # Ejecutar pruebas
    results.append(("Cargador de datos", test_climate_loader()))
    results.append(("Modelo con CSV", test_model_with_csv()))
    results.append(("Modelo con configuración", test_model_with_config()))
    
    # Resumen
    print("=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASÓ" if result else "✗ FALLÓ"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} pruebas pasaron")
    print("=" * 60 + "\n")
    
    # Salir con código apropiado
    sys.exit(0 if all(r for _, r in results) else 1)
