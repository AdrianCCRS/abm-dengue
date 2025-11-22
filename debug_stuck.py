# -*- coding: utf-8 -*-
"""
Script de debugging para identificar dónde se traba la simulación.

Monitorea el progreso en tiempo real y detecta operaciones lentas.
"""

import signal
import sys
import traceback
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.model.dengue_model import DengueModel
from src.agents.mosquito_agent import MosquitoAgent
from src.agents.human_agent import HumanAgent
from datetime import datetime
import time


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    """Handler para timeout"""
    print("\n⏱️  TIMEOUT DETECTADO!")
    print("La simulación se trabó. Imprimiendo stack trace:")
    traceback.print_stack(frame)
    raise TimeoutException()


def monitor_simulation(config_path, num_steps=200, timeout_seconds=30):
    """
    Ejecuta simulación con monitoreo de tiempo por operación.
    
    Parameters
    ----------
    config_path : str
        Ruta al archivo de configuración
    num_steps : int
        Número de pasos a simular
    timeout_seconds : int
        Timeout en segundos por paso (detecta trabas)
    """
    print("="*80)
    print("DEBUGGING DE TRABAS - ABM DENGUE")
    print("="*80)
    
    # Cargar configuración
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    climate_data_path = config.get('climate_data_path', 'data/raw/datos_climaticos_2022.csv')
    if not Path(climate_data_path).is_absolute():
        climate_data_path = str(root_dir / climate_data_path)
    
    print(f"\nCreando modelo...")
    model = DengueModel(
        config_file=str(config_path),
        climate_data_path=climate_data_path,
        fecha_inicio=datetime(2022, 1, 1)
    )
    
    print(f"Ejecutando {num_steps} pasos con monitoreo de timeout ({timeout_seconds}s/paso)...\n")
    
    # Configurar handler de timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    
    for step in range(num_steps):
        print(f"\n{'='*80}")
        print(f"PASO {step+1}/{num_steps}")
        print(f"{'='*80}")
        
        # Contar agentes antes del step
        mosquitos_antes = sum(1 for a in model.agents if isinstance(a, MosquitoAgent))
        humanos_antes = sum(1 for a in model.agents if isinstance(a, HumanAgent))
        huevos_antes = model.egg_manager.count_eggs()
        
        print(f"Antes: Mosquitos={mosquitos_antes}, Humanos={humanos_antes}, Huevos={huevos_antes}")
        
        # Activar timeout
        signal.alarm(timeout_seconds)
        
        try:
            step_start = time.time()
            
            # Ejecutar step con monitoreo
            print("  [1/5] Actualizando clima...")
            t1 = time.time()
            model._actualizar_clima()
            print(f"    ✓ Completado en {time.time()-t1:.2f}s")
            
            print("  [2/5] Procesando desarrollo de huevos...")
            t2 = time.time()
            model.egg_manager.step()
            print(f"    ✓ Completado en {time.time()-t2:.2f}s")
            
            print("  [3/5] Aplicando mortalidad de huevos...")
            t3 = time.time()
            if model.egg_mortality_rate > 0:
                model.egg_manager.apply_mortality(model.egg_mortality_rate)
            print(f"    ✓ Completado en {time.time()-t3:.2f}s")
            
            print(f"  [4/5] Activando {len(model.agents)} agentes...")
            t4 = time.time()
            
            agentes_lista = list(model.agents)
            model.random.shuffle(agentes_lista)
            
            # Procesar en batches para detectar trabas
            batch_size = 500
            for i in range(0, len(agentes_lista), batch_size):
                batch = agentes_lista[i:i+batch_size]
                batch_start = time.time()
                
                for agent in batch:
                    agent.step()
                
                batch_time = time.time() - batch_start
                if batch_time > 5:  # Batch lento
                    print(f"    ⚠️  Batch {i}-{i+len(batch)} tardó {batch_time:.2f}s")
            
            print(f"    ✓ Completado en {time.time()-t4:.2f}s")
            
            print("  [5/5] Recolectando datos...")
            t5 = time.time()
            model.datacollector.collect(model)
            print(f"    ✓ Completado en {time.time()-t5:.2f}s")
            
            # Desactivar timeout
            signal.alarm(0)
            
            step_time = time.time() - step_start
            
            # Contar agentes después
            mosquitos_despues = sum(1 for a in model.agents if isinstance(a, MosquitoAgent))
            humanos_despues = sum(1 for a in model.agents if isinstance(a, HumanAgent))
            huevos_despues = model.egg_manager.count_eggs()
            
            print(f"\nDespués: Mosquitos={mosquitos_despues}, Humanos={humanos_despues}, Huevos={huevos_despues}")
            print(f"Cambio: Mosquitos={mosquitos_despues-mosquitos_antes:+d}, Huevos={huevos_despues-huevos_antes:+d}")
            print(f"Tiempo total: {step_time:.2f}s")
            
            # Alertas
            if step_time > 15:
                print(f"🔴 PASO MUY LENTO: {step_time:.2f}s")
            
            if mosquitos_despues > 10000:
                print(f"🔴 POBLACIÓN EXCESIVA: {mosquitos_despues} mosquitos")
            
            # Incrementar día
            model.dia_simulacion += 1
            
        except TimeoutException:
            print(f"\n❌ PASO {step+1} SE TRABÓ (timeout después de {timeout_seconds}s)")
            print(f"Última operación conocida en progreso")
            print(f"Mosquitos: {mosquitos_antes}, Huevos: {huevos_antes}")
            
            # Información adicional de debugging
            print("\nInformación de debugging:")
            print(f"  - Total agentes: {len(model.agents)}")
            print(f"  - Egg batches: {len(model.egg_manager.egg_batches)}")
            print(f"  - Sitios de cría: {len(model.sitios_cria)}")
            
            return
        
        except Exception as e:
            signal.alarm(0)
            print(f"\n❌ ERROR en paso {step+1}: {e}")
            traceback.print_exc()
            return
    
    print("\n" + "="*80)
    print("SIMULACIÓN COMPLETADA SIN TRABAS")
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Debugging de trabas')
    parser.add_argument('--config', type=str, default='config/light_config.yaml',
                       help='Archivo de configuración')
    parser.add_argument('--steps', type=int, default=200,
                       help='Número de pasos')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout por paso en segundos')
    
    args = parser.parse_args()
    
    config_path = Path(__file__).parent / args.config
    
    try:
        monitor_simulation(str(config_path), args.steps, args.timeout)
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulación cancelada por usuario")
