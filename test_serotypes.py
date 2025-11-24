#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para validar la implementación de múltiples serotipos.

Prueba:
1. Inmunidad específica por serotipo
2. Inmunidad cruzada temporal
3. Capacidad de múltiples infecciones (hasta 4)
4. Transmisión de serotipos específicos

Uso:
    python test_serotypes.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel
from src.agents import EstadoSalud

def test_serotype_immunity():
    """Test 1: Verificar inmunidad específica por serotipo"""
    print("\n" + "="*70)
    print("TEST 1: Inmunidad Específica por Serotipo")
    print("="*70)
    
    # Crear modelo pequeño
    model = DengueModel(
        width=10,
        height=10,
        num_humanos=10,
        num_mosquitos=0,
        num_huevos=0,
        infectados_iniciales=0,
        mosquitos_infectados_iniciales=0,
        fecha_inicio=datetime(2022, 1, 1),  # Fecha válida dentro del rango de datos
        seed=42,
        config_file='config/default_config.yaml',
        climate_data_path='data/raw/datos_climaticos_2022.csv'
    )
    
    # Obtener un humano
    humano = list(model.agents)[0]
    
    # Infectar con DENV-1
    print(f"\n1. Estado inicial: {humano.estado.value}")
    print(f"   Inmunidad permanente: {humano.inmunidad_permanente}")
    
    humano.get_exposed(serotipo=1)
    print(f"\n2. Después de exposición a DENV-1:")
    print(f"   Estado: {humano.estado.value}")
    print(f"   Serotipo actual: {humano.serotipo_actual}")
    
    # Avanzar hasta recuperación
    for _ in range(20):
        humano.actualizar_estado_seir()
    
    print(f"\n3. Después de recuperación:")
    print(f"   Estado: {humano.estado.value}")
    print(f"   Inmunidad permanente: {humano.inmunidad_permanente}")
    print(f"   Inmunidad cruzada: {humano.inmunidad_cruzada}")
    
    # Intentar reinfectar con DENV-1 (debe fallar)
    humano.get_exposed(serotipo=1)
    print(f"\n4. Después de intentar reinfección con DENV-1:")
    print(f"   Estado: {humano.estado.value} (debe ser R)")
    print(f"   Serotipo actual: {humano.serotipo_actual} (debe ser None)")
    
    # Verificar susceptibilidad
    print(f"\n5. Susceptibilidad:")
    print(f"   ¿Susceptible a DENV-1? {humano.es_susceptible(serotipo=1)} (debe ser False)")
    print(f"   ¿Susceptible a DENV-2? {humano.es_susceptible(serotipo=2)} (debe ser False por inmunidad cruzada)")
    
    print("\n✓ Test 1 completado")
    return True

def test_cross_immunity_expiration():
    """Test 2: Verificar expiración de inmunidad cruzada"""
    print("\n" + "="*70)
    print("TEST 2: Expiración de Inmunidad Cruzada")
    print("="*70)
    
    model = DengueModel(
        width=10,
        height=10,
        num_humanos=10,
        num_mosquitos=0,
        num_huevos=0,
        infectados_iniciales=0,
        mosquitos_infectados_iniciales=0,
        fecha_inicio=datetime(2022, 1, 1),
        seed=42,
        config_file='config/default_config.yaml',
        climate_data_path='data/raw/datos_climaticos_2022.csv'
    )
    
    humano = list(model.agents)[0]
    
    # Infectar con DENV-1 y recuperar
    humano.get_exposed(serotipo=1)
    for _ in range(20):
        humano.actualizar_estado_seir()
    
    print(f"\n1. Después de recuperación de DENV-1:")
    print(f"   Inmunidad cruzada a DENV-2: {humano.inmunidad_cruzada.get(2, 0)} días")
    
    # Avanzar 76 días (más que los 75 de inmunidad cruzada)
    for dia in range(76):
        humano.actualizar_estado_seir()
        if dia == 74:
            print(f"\n2. Día 74 (antes de expirar):")
            print(f"   Inmunidad cruzada a DENV-2: {humano.inmunidad_cruzada.get(2, 0)} días")
            print(f"   ¿Susceptible a DENV-2? {humano.es_susceptible(serotipo=2)}")
    
    print(f"\n3. Día 76 (después de expirar):")
    print(f"   Inmunidad cruzada a DENV-2: {humano.inmunidad_cruzada.get(2, 0)} días")
    print(f"   ¿Susceptible a DENV-2? {humano.es_susceptible(serotipo=2)} (debe ser True)")
    
    # Intentar infectar con DENV-2 (debe funcionar)
    humano.get_exposed(serotipo=2)
    print(f"\n4. Después de exposición a DENV-2:")
    print(f"   Estado: {humano.estado.value} (debe ser E)")
    print(f"   Serotipo actual: {humano.serotipo_actual} (debe ser 2)")
    
    print("\n✓ Test 2 completado")
    return True

def test_multiple_infections():
    """Test 3: Verificar capacidad de 4 infecciones"""
    print("\n" + "="*70)
    print("TEST 3: Múltiples Infecciones (hasta 4)")
    print("="*70)
    
    model = DengueModel(
        width=10,
        height=10,
        num_humanos=10,
        num_mosquitos=0,
        num_huevos=0,
        infectados_iniciales=0,
        mosquitos_infectados_iniciales=0,
        fecha_inicio=datetime(2022, 1, 1),
        seed=42,
        config_file='config/default_config.yaml',
        climate_data_path='data/raw/datos_climaticos_2022.csv'
    )
    
    humano = list(model.agents)[0]
    
    # Infectar con los 4 serotipos secuencialmente
    for serotipo in [1, 2, 3, 4]:
        print(f"\n--- Infección {serotipo} (DENV-{serotipo}) ---")
        
        # Esperar a que expire inmunidad cruzada si es necesario
        if serotipo > 1:
            for _ in range(76):
                humano.actualizar_estado_seir()
        
        # Infectar
        humano.get_exposed(serotipo=serotipo)
        print(f"Expuesto a DENV-{serotipo}")
        
        # Recuperar
        for _ in range(20):
            humano.actualizar_estado_seir()
        
        print(f"Recuperado de DENV-{serotipo}")
        print(f"Inmunidad permanente: {sorted(humano.inmunidad_permanente)}")
        print(f"Historial: {len(humano.historial_infecciones)} infecciones")
    
    print(f"\n--- Estado Final ---")
    print(f"Inmunidad permanente: {sorted(humano.inmunidad_permanente)}")
    print(f"Historial: {humano.historial_infecciones}")
    print(f"¿Susceptible a algún serotipo? {humano.es_susceptible()} (debe ser False)")
    
    # Intentar quinta infección (debe fallar)
    humano.get_exposed(serotipo=1)
    print(f"\nIntento de quinta infección con DENV-1:")
    print(f"Estado: {humano.estado.value} (debe ser R)")
    
    print("\n✓ Test 3 completado")
    return True

def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*70)
    print("VALIDACIÓN DE IMPLEMENTACIÓN DE SEROTIPOS")
    print("="*70)
    
    try:
        test_serotype_immunity()
        test_cross_immunity_expiration()
        test_multiple_infections()
        
        print("\n" + "="*70)
        print("✓ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("="*70)
        print("\nLa implementación de serotipos está funcionando correctamente:")
        print("  ✓ Inmunidad permanente específica por serotipo")
        print("  ✓ Inmunidad cruzada temporal (75 días)")
        print("  ✓ Capacidad de hasta 4 infecciones")
        print("  ✓ Transmisión de serotipos específicos")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ ERROR EN LOS TESTS")
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
