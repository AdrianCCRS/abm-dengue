#!/usr/bin/env python3
"""
Test de rastreo de uso de parámetros de configuración.

Este script ejecuta una simulación corta y registra en logs detallados
cada vez que se usa un parámetro de configuración, mostrando:
- Qué parámetro se está usando
- En qué archivo y línea se usa
- Qué agente o clase lo está usando
- El valor actual del parámetro
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configurar logging detallado
log_dir = root_dir / "logs"
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"config_usage_test_{timestamp}.log"

# Configurar formato detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Ahora importar el modelo
from src.model.dengue_model import DengueModel
from src.agents import MosquitoAgent, HumanAgent, EtapaVida, EstadoSalud

def test_config_usage():
    """Test que rastrea el uso de todos los parámetros de configuración."""
    
    logger.info("=" * 80)
    logger.info("INICIANDO TEST DE USO DE PARÁMETROS DE CONFIGURACIÓN")
    logger.info("=" * 80)
    
    # Configuración de test con valores distintivos para rastrear
    config = {
        'simulation': {
            'steps': 5,
            'width': 20,
            'height': 20,
            'num_humanos': 50,
            'num_mosquitos': 100,
            'num_huevos': 30,
            'infectados_iniciales': 3,
            'mosquitos_infectados_iniciales': 2
        },
        'human_disease': {
            'incubation_period': 5.0,
            'infectious_period': 6.0
        },
        'mosquito_disease': {
            'mortality_rate': 0.05,
            'sensory_range': 3
        },
        'transmission': {
            'mosquito_to_human_prob': 0.6,
            'human_to_mosquito_prob': 0.275
        },
        'mobility': {
            'park_probability_student': 0.3,
            'park_probability_worker': 0.1,
            'park_probability_mobile': 0.15,
            'park_probability_stationary': 0.05,
            'school_start_hour': 7,
            'school_end_hour': 15,
            'work_start_hour': 7,
            'work_end_hour': 17,
            'park_start_hour': 16,
            'park_end_hour': 19,
            'mobile_move_interval_hours': 2,
            'mobile_active_start_hour': 7,
            'mobile_active_end_hour': 19
        },
        'mosquito_breeding': {
            'eggs_per_female': 100,
            'mating_probability': 0.6,
            'female_ratio': 0.7,  # Valor distintivo para rastrear
            'egg_maturation_base_days': 3,
            'egg_maturation_temp_optimal': 21.0,
            'egg_maturation_temp_sensitivity': 5.0,
            'egg_to_adult_base_days': 8,
            'egg_to_adult_temp_optimal': 25.0,
            'egg_to_adult_temp_sensitivity': 1.0,
            'rainfall_threshold': 0.0,
            'breeding_site_ratio': 0.2
        },
        'population': {
            'mobility_distribution': {
                'student': 0.25,
                'worker': 0.35,
                'mobile': 0.25,
                'stationary': 0.15
            }
        },
        'environment': {
            'cell_types': {
                'water_ratio': 0.05,
                'park_ratio': 0.10
            },
            'zone_sizes': {
                'water_min': 2,
                'water_max': 4,
                'park_min': 3,
                'park_max': 6
            },
            'mosquito_flight': {
                'max_range': 10
            },
            'synthetic_climate': {
                'rain_probability': 0.3,
                'rain_min_mm': 5.0,
                'rain_max_mm': 50.0
            }
        },
        'control': {
            'lsm': {
                'frequency_days': 7,
                'coverage': 0.7,
                'effectiveness': 0.8
            },
            'itn_irs': {
                'duration_days': 90,
                'coverage': 0.6,
                'effectiveness': 0.7
            }
        },
        'human_behavior': {
            'isolation_probability': 0.7,
            'infected_mobility_radius': 1
        }
    }
    
    logger.info("\n" + "=" * 80)
    logger.info("FASE 1: CREACIÓN DEL MODELO")
    logger.info("=" * 80)
    
    # Crear modelo
    model = DengueModel(
        width=20,
        height=20,
        num_humanos=50,
        num_mosquitos=100,
        num_huevos=30,
        infectados_iniciales=3,
        mosquitos_infectados_iniciales=2,
        config=config,
        seed=42
    )
    
    logger.info(f"\n✓ Modelo creado exitosamente")
    logger.info(f"  - Grid: {model.width}x{model.height}")
    logger.info(f"  - Humanos totales: {model.num_humanos}")
    logger.info(f"  - Mosquitos adultos: {len([a for a in model.agents if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.ADULTO])}")
    logger.info(f"  - Huevos iniciales: {len([a for a in model.agents if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.HUEVO])}")
    
    # Verificar parámetros cargados
    logger.info("\n" + "=" * 80)
    logger.info("FASE 2: VERIFICACIÓN DE PARÁMETROS CARGADOS EN EL MODELO")
    logger.info("=" * 80)
    
    params_to_check = {
        'human_disease': ['incubacion_humano', 'infeccioso_humano'],
        'mosquito_disease': ['mortalidad_mosquito', 'rango_sensorial_mosquito'],
        'transmission': ['prob_transmision_mosquito_humano', 'prob_transmision_humano_mosquito'],
        'mobility': ['prob_parque_estudiante', 'prob_parque_trabajador', 'prob_parque_movil', 
                     'prob_parque_estacionario', 'hora_inicio_escuela', 'hora_fin_escuela',
                     'hora_inicio_trabajo', 'hora_fin_trabajo'],
        'mosquito_breeding': ['huevos_por_hembra', 'prob_apareamiento_mosquito', 'proporcion_hembras',
                             'dias_base_maduracion_huevo', 'temp_optima_maduracion_huevo',
                             'dias_base_desarrollo_huevo', 'temp_optima_desarrollo_huevo'],
        'environment': ['proporcion_celdas_agua', 'proporcion_celdas_parques', 'rango_vuelo_max',
                       'prob_lluvia', 'lluvia_min_mm', 'lluvia_max_mm'],
        'control': ['lsm_frecuencia_dias', 'lsm_cobertura', 'lsm_efectividad',
                   'itn_irs_duracion_dias', 'itn_irs_cobertura', 'itn_irs_efectividad'],
        'human_behavior': ['prob_aislamiento', 'radio_mov_infectado']
    }
    
    for section, params in params_to_check.items():
        logger.info(f"\n[{section.upper()}]")
        for param in params:
            if hasattr(model, param):
                value = getattr(model, param)
                logger.info(f"  ✓ {param} = {value}")
            else:
                logger.warning(f"  ✗ {param} NO ENCONTRADO en model")
    
    # Verificar female_ratio en mosquitos
    logger.info("\n" + "=" * 80)
    logger.info("FASE 3: VERIFICACIÓN DE female_ratio EN MOSQUITOS CREADOS")
    logger.info("=" * 80)
    
    mosquitos_adultos = [a for a in model.agents if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.ADULTO]
    hembras = sum(1 for m in mosquitos_adultos if m.es_hembra)
    machos = sum(1 for m in mosquitos_adultos if not m.es_hembra)
    proporcion_real = hembras / len(mosquitos_adultos) if mosquitos_adultos else 0
    
    logger.info(f"  Parámetro configurado: female_ratio = {model.proporcion_hembras}")
    logger.info(f"  Mosquitos adultos totales: {len(mosquitos_adultos)}")
    logger.info(f"  Hembras: {hembras} ({proporcion_real:.2%})")
    logger.info(f"  Machos: {machos} ({(1-proporcion_real):.2%})")
    logger.info(f"  ✓ Proporción real vs configurada: {proporcion_real:.2f} vs {model.proporcion_hembras:.2f}")
    
    # Verificar huevos
    huevos = [a for a in model.agents if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.HUEVO]
    hembras_huevos = sum(1 for h in huevos if h.es_hembra)
    proporcion_huevos = hembras_huevos / len(huevos) if huevos else 0
    
    logger.info(f"\n  Huevos totales: {len(huevos)}")
    logger.info(f"  Huevos hembra: {hembras_huevos} ({proporcion_huevos:.2%})")
    logger.info(f"  ✓ Proporción en huevos: {proporcion_huevos:.2f} vs {model.proporcion_hembras:.2f}")
    
    # Verificar parámetros en agentes humanos
    logger.info("\n" + "=" * 80)
    logger.info("FASE 4: VERIFICACIÓN DE PARÁMETROS EN AGENTES HUMANOS")
    logger.info("=" * 80)
    
    humanos = [a for a in model.agents if isinstance(a, HumanAgent)]
    if humanos:
        humano_sample = humanos[0]
        logger.info(f"\n  Muestra de humano (ID={humano_sample.unique_id}):")
        logger.info(f"    - tipo: {humano_sample.tipo}")
        logger.info(f"    - estado: {humano_sample.estado}")
        logger.info(f"    - duracion_expuesto (Ne): {humano_sample.duracion_expuesto}")
        logger.info(f"    - duracion_infectado (Ni): {humano_sample.duracion_infectado}")
        logger.info(f"    - prob_aislamiento: {humano_sample.prob_aislamiento}")
        logger.info(f"    - radio_mov_infectado: {humano_sample.radio_mov_infectado}")
        logger.info(f"    - prob_parque: {humano_sample.prob_parque}")
        logger.info(f"    - hora_inicio_escuela: {humano_sample.hora_inicio_escuela}")
        logger.info(f"    - hora_fin_escuela: {humano_sample.hora_fin_escuela}")
    
    # Verificar parámetros en agentes mosquito
    logger.info("\n" + "=" * 80)
    logger.info("FASE 5: VERIFICACIÓN DE PARÁMETROS EN AGENTES MOSQUITO")
    logger.info("=" * 80)
    
    if mosquitos_adultos:
        mosquito_sample = mosquitos_adultos[0]
        logger.info(f"\n  Muestra de mosquito (ID={mosquito_sample.unique_id}):")
        logger.info(f"    - etapa: {mosquito_sample.etapa}")
        logger.info(f"    - es_hembra: {mosquito_sample.es_hembra}")
        logger.info(f"    - estado: {mosquito_sample.estado}")
        logger.info(f"    - mortalidad_mosquito: {mosquito_sample.mortalidad_mosquito}")
        logger.info(f"    - rango_sensorial: {mosquito_sample.rango_sensorial}")
        logger.info(f"    - huevos_por_hembra: {mosquito_sample.huevos_por_hembra}")
        logger.info(f"    - prob_apareamiento: {mosquito_sample.prob_apareamiento}")
        logger.info(f"    - proporcion_hembras: {mosquito_sample.proporcion_hembras}")
        logger.info(f"    - rango_vuelo_max: {mosquito_sample.rango_vuelo_max}")
    
    # Ejecutar simulación corta
    logger.info("\n" + "=" * 80)
    logger.info("FASE 6: EJECUCIÓN DE SIMULACIÓN (5 PASOS)")
    logger.info("=" * 80)
    
    for step in range(5):
        logger.info(f"\n--- PASO {step + 1} ---")
        
        # Log de clima antes de step
        logger.info(f"  Temperatura actual: {model.temperatura_actual:.1f}°C")
        logger.info(f"  Precipitación actual: {model.precipitacion_actual:.1f}mm")
        
        # Ejecutar step
        model.step()
        
        # Log de métricas post-step
        susceptibles = len([h for h in humanos if h.estado == EstadoSalud.SUSCEPTIBLE])
        infectados = len([h for h in humanos if h.estado == EstadoSalud.INFECTADO])
        expuestos = len([h for h in humanos if h.estado == EstadoSalud.EXPUESTO])
        recuperados = len([h for h in humanos if h.estado == EstadoSalud.RECUPERADO])
        
        logger.info(f"  Humanos S/E/I/R: {susceptibles}/{expuestos}/{infectados}/{recuperados}")
        logger.info(f"  Mosquitos totales: {len([m for m in model.agents if isinstance(m, MosquitoAgent) and m.etapa == EtapaVida.ADULTO])}")
        logger.info(f"  Huevos: {len([m for m in model.agents if isinstance(m, MosquitoAgent) and m.etapa == EtapaVida.HUEVO])}")
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETADO EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info(f"\nLog guardado en: {log_file}")
    
    return log_file

if __name__ == "__main__":
    try:
        log_path = test_config_usage()
        print(f"\n✓ Test completado. Revisa el log en: {log_path}")
    except Exception as e:
        logger.error(f"Error durante el test: {e}", exc_info=True)
        raise
