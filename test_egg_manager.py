"""
Script de prueba simple para verificar la implementación de EggManager.

Prueba básica sin dependencias externas pesadas.
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.egg_manager import EggManager, EggBatch


class MockModel:
    """Modelo mock para testing"""
    def __init__(self):
        self.dia_simulacion = 0
        self.temperatura_actual = 25.0
        self.immature_development_threshold = 8.3
        self.immature_thermal_constant = 181.2
        self.grid = MockGrid()
        self.agents = MockAgentSet()
        self._next_id = 0
        
        class MockRandom:
            def random(self):
                return 0.5
        
        self.random = MockRandom()
    
    def next_id(self):
        self._next_id += 1
        return self._next_id


class MockGrid:
    def place_agent(self, agent, pos):
        pass


class MockAgentSet:
    def __init__(self):
        self.agents = []
    
    def add(self, agent):
        self.agents.append(agent)


def test_egg_batch_creation():
    """Test 1: Crear un lote de huevos"""
    print("Test 1: Crear EggBatch...")
    batch = EggBatch(
        sitio_cria=(10, 15),
        cantidad=50,
        grados_acumulados=0.0,
        dias_como_huevo=0,
        fecha_puesta=0
    )
    assert batch.cantidad == 50
    assert batch.sitio_cria == (10, 15)
    print("✓ EggBatch creado correctamente")


def test_egg_manager_add_eggs():
    """Test 2: Agregar huevos al gestor"""
    print("\nTest 2: Agregar huevos a EggManager...")
    model = MockModel()
    manager = EggManager(model)
    
    # Agregar primer lote
    manager.add_eggs((5, 5), 100)
    assert manager.count_eggs() == 100
    assert len(manager.egg_batches) == 1
    print(f"✓ Primer lote agregado: {manager.count_eggs()} huevos")
    
    # Agregar segundo lote en mismo sitio y mismo día (debe agruparse)
    manager.add_eggs((5, 5), 50)
    assert manager.count_eggs() == 150
    assert len(manager.egg_batches) == 1  # Agrupados en un solo lote
    print(f"✓ Segundo lote agrupado: {manager.count_eggs()} huevos, {len(manager.egg_batches)} lote(s)")
    
    # Agregar lote en diferente sitio
    manager.add_eggs((10, 10), 75)
    assert manager.count_eggs() == 225
    assert len(manager.egg_batches) == 2
    print(f"✓ Tercer lote en sitio diferente: {manager.count_eggs()} huevos, {len(manager.egg_batches)} lote(s)")


def test_egg_development():
    """Test 3: Desarrollo de huevos con modelo GDD"""
    print("\nTest 3: Desarrollo de huevos (modelo GDD)...")
    model = MockModel()
    manager = EggManager(model)
    
    # Agregar huevos
    manager.add_eggs((5, 5), 10)
    
    # Simular días de desarrollo
    # A 25°C: GD = 25 - 8.3 = 16.7 °C·día
    # Necesita 181.2 °C·día → ~11 días
    
    for dia in range(10):
        model.dia_simulacion = dia
        manager.step()
        print(f"  Día {dia+1}: {manager.count_eggs()} huevos, "
              f"{manager.egg_batches[0].grados_acumulados:.1f} °C·día acumulados" 
              if manager.egg_batches else "  (todos eclosionaron)")
    
    # Después de 10 días aún no deberían eclosionar
    assert manager.count_eggs() == 10
    print(f"✓ Después de 10 días: {manager.count_eggs()} huevos (aún no eclosionan)")
    
    # Día 11 deberían eclosionar
    model.dia_simulacion = 11
    manager.step()
    
    # Verificar que eclosionaron (huevos = 0, adultos creados)
    assert manager.count_eggs() == 0
    assert len(model.agents.agents) == 10
    print(f"✓ Día 11: Eclosionaron! {len(model.agents.agents)} mosquitos adultos creados")


def test_lsm_control():
    """Test 4: Control LSM"""
    print("\nTest 4: Control larvario (LSM)...")
    model = MockModel()
    manager = EggManager(model)
    
    # Agregar 1000 huevos
    manager.add_eggs((5, 5), 1000)
    print(f"  Huevos iniciales: {manager.count_eggs()}")
    
    # Aplicar LSM con 70% cobertura y 80% efectividad
    # Reducción esperada: ~56% (puede variar por aleatoriedad)
    manager.apply_lsm_control(coverage=0.7, effectiveness=0.8)
    
    huevos_restantes = manager.count_eggs()
    reduccion_pct = (1000 - huevos_restantes) / 1000 * 100
    print(f"  Huevos después de LSM: {huevos_restantes} ({reduccion_pct:.1f}% reducción)")
    
    # Debería haber reducción significativa
    assert huevos_restantes < 1000
    print("✓ LSM aplicado correctamente")


def test_mortality():
    """Test 5: Mortalidad de huevos"""
    print("\nTest 5: Mortalidad de huevos...")
    model = MockModel()
    manager = EggManager(model)
    
    # Agregar 1000 huevos
    manager.add_eggs((5, 5), 1000)
    print(f"  Huevos iniciales: {manager.count_eggs()}")
    
    # Aplicar mortalidad del 5% diario
    manager.apply_mortality(mortality_rate=0.05)
    
    huevos_restantes = manager.count_eggs()
    print(f"  Huevos después de mortalidad: {huevos_restantes}")
    
    # Debería haber ~950 huevos (95% supervivencia)
    assert 900 < huevos_restantes < 1000
    print("✓ Mortalidad aplicada correctamente")


def main():
    print("="*60)
    print("PRUEBAS DE EggManager")
    print("="*60)
    
    try:
        test_egg_batch_creation()
        test_egg_manager_add_eggs()
        test_egg_development()
        test_lsm_control()
        test_mortality()
        
        print("\n" + "="*60)
        print("✓ TODAS LAS PRUEBAS PASARON")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ PRUEBA FALLÓ: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
