#!/usr/bin/env python3
"""
Script de prueba para verificar que female_ratio se usa correctamente.
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Ahora importar desde src
from src.model.dengue_model import DengueModel
from src.agents import MosquitoAgent, EtapaVida

# Test 1: female_ratio = 0.5 (por defecto)
print("=" * 60)
print("Test 1: female_ratio = 0.5 (por defecto)")
print("=" * 60)

config1 = {
    'mosquito_breeding': {
        'female_ratio': 0.5
    }
}

model1 = DengueModel(
    width=20, 
    height=20, 
    num_humanos=10, 
    num_mosquitos=100,
    num_huevos=100,
    config=config1,
    seed=42
)

# Contar hembras y machos en mosquitos adultos
mosquitos_adultos = [a for a in model1.agents if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.ADULTO]
hembras = sum(1 for m in mosquitos_adultos if m.es_hembra)
machos = sum(1 for m in mosquitos_adultos if not m.es_hembra)
proporcion_hembras = hembras / len(mosquitos_adultos) if mosquitos_adultos else 0

print(f"Mosquitos adultos totales: {len(mosquitos_adultos)}")
print(f"Hembras: {hembras} ({proporcion_hembras:.2%})")
print(f"Machos: {machos} ({(1-proporcion_hembras):.2%})")
print(f"✓ Proporción esperada: 50% ± 10%")
print(f"✓ Proporción obtenida: {proporcion_hembras:.2%}")
assert 0.4 <= proporcion_hembras <= 0.6, "La proporción debería estar cerca de 0.5"
print("✓ Test 1 PASADO\n")

# Test 2: female_ratio = 0.8 (80% hembras)
print("=" * 60)
print("Test 2: female_ratio = 0.8 (80% hembras)")
print("=" * 60)

config2 = {
    'mosquito_breeding': {
        'female_ratio': 0.8
    }
}

model2 = DengueModel(
    width=20, 
    height=20, 
    num_humanos=10, 
    num_mosquitos=200,
    num_huevos=200,
    config=config2,
    seed=42
)

# Contar hembras y machos en mosquitos adultos
mosquitos_adultos2 = [a for a in model2.agents if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.ADULTO]
hembras2 = sum(1 for m in mosquitos_adultos2 if m.es_hembra)
machos2 = sum(1 for m in mosquitos_adultos2 if not m.es_hembra)
proporcion_hembras2 = hembras2 / len(mosquitos_adultos2) if mosquitos_adultos2 else 0

print(f"Mosquitos adultos totales: {len(mosquitos_adultos2)}")
print(f"Hembras: {hembras2} ({proporcion_hembras2:.2%})")
print(f"Machos: {machos2} ({(1-proporcion_hembras2):.2%})")
print(f"✓ Proporción esperada: 80% ± 10%")
print(f"✓ Proporción obtenida: {proporcion_hembras2:.2%}")
assert 0.7 <= proporcion_hembras2 <= 0.9, "La proporción debería estar cerca de 0.8"
print("✓ Test 2 PASADO\n")

# Test 3: female_ratio = 0.2 (20% hembras)
print("=" * 60)
print("Test 3: female_ratio = 0.2 (20% hembras)")
print("=" * 60)

config3 = {
    'mosquito_breeding': {
        'female_ratio': 0.2
    }
}

model3 = DengueModel(
    width=20, 
    height=20, 
    num_humanos=10, 
    num_mosquitos=200,
    num_huevos=200,
    config=config3,
    seed=42
)

# Contar hembras y machos en mosquitos adultos
mosquitos_adultos3 = [a for a in model3.agents if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.ADULTO]
hembras3 = sum(1 for m in mosquitos_adultos3 if m.es_hembra)
machos3 = sum(1 for m in mosquitos_adultos3 if not m.es_hembra)
proporcion_hembras3 = hembras3 / len(mosquitos_adultos3) if mosquitos_adultos3 else 0

print(f"Mosquitos adultos totales: {len(mosquitos_adultos3)}")
print(f"Hembras: {hembras3} ({proporcion_hembras3:.2%})")
print(f"Machos: {machos3} ({(1-proporcion_hembras3):.2%})")
print(f"✓ Proporción esperada: 20% ± 10%")
print(f"✓ Proporción obtenida: {proporcion_hembras3:.2%}")
assert 0.1 <= proporcion_hembras3 <= 0.3, "La proporción debería estar cerca de 0.2"
print("✓ Test 3 PASADO\n")

print("=" * 60)
print("✓✓✓ TODOS LOS TESTS PASARON ✓✓✓")
print("=" * 60)
print("\nConclusión: El parámetro female_ratio ahora se usa correctamente")
print("desde el archivo de configuración en todo el código.")
