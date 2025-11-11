"""
Modelo principal ABM del Dengue para Bucaramanga.

Este módulo implementa el modelo de simulación basado en agentes
con integración climática y estrategias de control.

Basado en Jindal & Rao (2017) adaptado a Bucaramanga, Colombia.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

from ..agents import (
    HumanAgent, MosquitoAgent,
    EstadoSalud, EstadoMosquito, TipoMovilidad, EtapaVida
)
from .celda import Celda, TipoCelda
from ..utils.climate_data import ClimateDataLoader


class DengueModel(Model):
    """
    Modelo ABM del Dengue con integración climática y control.
    
    Simula la dinámica de transmisión del dengue en Bucaramanga con:
    - Población humana con estados SEIR y movilidad diferenciada
    - Población de mosquitos con estados SI y ciclo de vida completo
    - Clima dinámico (temperatura y precipitación desde datos históricos CSV)
    - Estrategias de control: LSM (control larvario) e ITN/IRS (camas/insecticidas)
    
    Parameters
    ----------
    width : int, default=50
        Ancho del grid (celdas)
    height : int, default=50
        Alto del grid (celdas)
    num_humanos : int, default=1000
        Número inicial de humanos
    num_mosquitos : int, default=2000
        Número inicial de mosquitos adultos
    num_huevos : int, default=500
        Número inicial de huevos
    infectados_iniciales : int, default=10
        Humanos infectados al inicio
    mosquitos_infectados_iniciales : int, default=5
        Mosquitos infectados al inicio
    usar_lsm : bool, default=False
        Activar estrategia LSM (control larvario)
    usar_itn_irs : bool, default=False
        Activar estrategia ITN/IRS (camas/insecticidas)
    fecha_inicio : datetime, default=datetime(2024, 1, 1)
        Fecha de inicio de simulación (para clima)
    climate_data_path : str, optional
        Ruta al archivo CSV con datos climáticos históricos
    seed : Optional[int], default=None
        Semilla para reproducibilidad
        
    Attributes
    ----------
    grid : MultiGrid
        Grid espacial 50×50 con múltiples agentes por celda
    schedule : RandomActivation
        Scheduler de activación aleatoria de agentes
    datacollector : DataCollector
        Recolector de métricas por paso
    temperatura_actual : float
        Temperatura diaria en °C
    precipitacion_actual : float
        Precipitación diaria en mm
    fecha_actual : datetime
        Fecha simulada actual
    dia_simulacion : int
        Contador de días transcurridos
    climate_loader : ClimateDataLoader, optional
        Cargador de datos climáticos desde CSV
    """
    
    def __init__(
        self,
        width: int = 50,
        height: int = 50,
        num_humanos: int = 1000,
        num_mosquitos: int = 2000,
        num_huevos: int = 500,
        infectados_iniciales: int = 10,
        mosquitos_infectados_iniciales: int = 5,
        usar_lsm: bool = False,
        usar_itn_irs: bool = False,
        fecha_inicio: datetime = datetime(2024, 1, 1),
        climate_data_path: Optional[str] = None,
        seed: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None
    ):
        super().__init__()
        
        # Configuración del modelo
        self.width = width
        self.height = height
        self.num_humanos = num_humanos
        self.num_mosquitos = num_mosquitos
        self.num_huevos = num_huevos
        
        # Inicializar variable de cargador de clima (antes de cargar configuración)
        self.climate_loader = None
        
        # Cargar configuración desde archivo si se proporciona
        if config_file:
            cfg_dict = self._cargar_configuracion_archivo(config_file)
            self._cargar_configuracion(cfg_dict)
        # Cargar configuración desde diccionario si se proporciona
        elif config:
            self._cargar_configuracion(config)
        else:
            self._cargar_configuracion_default()
        
        # Semilla de aleatoriedad
        if seed is not None:
            self.random.seed(seed)
            np.random.seed(seed)
        
        # Grid espacial (múltiples agentes por celda, sin toroide)
        self.grid = MultiGrid(width, height, torus=False)
        
        # Activación aleatoria de agentes (Mesa 2.3.4: self.agents.shuffle().do())
        # El contador de steps se maneja manualmente para compatibilidad con batch_run
        self.steps = 0

        # Variables climáticas
        self.fecha_inicio = fecha_inicio
        self.fecha_actual = fecha_inicio
        self.dia_simulacion = 0
        self.temperatura_actual = 25.0  # °C (valor inicial)
        self.precipitacion_actual = 0.0  # mm (valor inicial)
        
        # Cargar datos climáticos desde CSV (OBLIGATORIO)
        if not climate_data_path:
            raise ValueError(
                "Debe proporcionar climate_data_path al crear el modelo. "
                "El modelo solo funciona con datos climáticos reales desde CSV."
            )
        
        try:
            self.climate_loader = ClimateDataLoader(climate_data_path)
            
            # Validar que la fecha de inicio esté en el rango de datos
            if not self.climate_loader.has_date(fecha_inicio):
                date_min, date_max = self.climate_loader.get_date_range()
                raise ValueError(
                    f"La fecha de inicio {fecha_inicio.date()} no está en el rango "
                    f"de datos disponibles ({date_min.date()} a {date_max.date()}). "
                    f"Por favor, ajuste fecha_inicio para que esté dentro de este rango."
                )
            
            print(f"Datos climáticos cargados desde: {climate_data_path}")
            date_min, date_max = self.climate_loader.get_date_range()
            print(f"  Rango de fechas: {date_min.date()} a {date_max.date()}")
            
        except Exception as e:
            raise RuntimeError(
                f"Error al cargar datos climáticos desde '{climate_data_path}': {e}"
            )
        
        # Estrategias de control
        self.usar_lsm = usar_lsm
        self.usar_itn_irs = usar_itn_irs
        self.lsm_activo = False
        self.itn_irs_activo = False
        
        # Sitios de cría temporales (charcos post-lluvia)
        # Diccionario: {posicion: dias_restantes}
        self.sitios_cria_temporales = {}
        
        # Mapa de celdas con tipos (urbana, parque, agua)
        self.mapa_celdas = self._inicializar_mapa_celdas()
        
        # Sitios de cría (desde mapa de celdas)
        self.sitios_cria = self._generar_sitios_cria()
        
        # Índice espacial para búsqueda rápida de sitios de cría
        # Divide el grid en sectores de tamaño sector_size x sector_size
        self.sector_size = 10  # Cada sector es 10x10 celdas
        self.indice_sitios = self._crear_indice_espacial_sitios()
        
        # Cache de parques para búsqueda rápida (evita iterar sobre todas las celdas)
        self.parques = self._generar_lista_parques()
        
        # Cache de celdas urbanas para asignación eficiente de hogares/destinos
        self.celdas_urbanas = self._generar_lista_urbanas()
        
        # Contador de IDs único
        self._next_id = 0
        
        # Crear agentes
        self._crear_humanos(num_humanos, self.infectados_iniciales)
        self._crear_mosquitos(num_mosquitos, self.mosquitos_infectados_iniciales)
        self._crear_huevos(num_huevos)
        
        # DataCollector para métricas
        self.datacollector = DataCollector(
            model_reporters={
                "Susceptibles": lambda m: self._contar_humanos_estado(EstadoSalud.SUSCEPTIBLE),
                "Expuestos": lambda m: self._contar_humanos_estado(EstadoSalud.EXPUESTO),
                "Infectados": lambda m: self._contar_humanos_estado(EstadoSalud.INFECTADO),
                "Recuperados": lambda m: self._contar_humanos_estado(EstadoSalud.RECUPERADO),
                "Mosquitos_S": lambda m: self._contar_mosquitos_estado(EstadoMosquito.SUSCEPTIBLE),
                "Mosquitos_I": lambda m: self._contar_mosquitos_estado(EstadoMosquito.INFECTADO),
                "Mosquitos_Total": lambda m: self._contar_mosquitos_adultos(),
                "Huevos": lambda m: self._contar_huevos(),
                "Temperatura": lambda m: m.temperatura_actual,
                "Precipitacion": lambda m: m.precipitacion_actual,
                "Sitios_Temporales": lambda m: len(m.sitios_cria_temporales),
                "LSM_Activo": lambda m: m.lsm_activo,
                "ITN_IRS_Activo": lambda m: m.itn_irs_activo,
            },
            agent_reporters={
                "Estado": "estado",
                "Tipo": lambda a: a.tipo if hasattr(a, 'tipo') else None,
                "Posicion": "pos"
            }
        )
        
        # Recolectar estado inicial
        self.datacollector.collect(self)
        
        self.running = True

    def _cargar_configuracion_archivo(self, ruta: str) -> Dict[str, Any]:
        """
        Carga configuración desde archivo YAML o JSON y retorna un dict.
        
        Parameters
        ----------
        ruta : str
            Ruta al archivo de configuración (.yaml/.yml o .json)
        
        Returns
        -------
        Dict[str, Any]
            Diccionario con la configuración cargada
        """
        import os
        import json
        try:
            ext = os.path.splitext(ruta)[1].lower()
            with open(ruta, 'r', encoding='utf-8') as f:
                if ext in ('.yaml', '.yml'):
                    import yaml  # lazy import
                    return yaml.safe_load(f) or {}
                elif ext == '.json':
                    return json.load(f) or {}
                else:
                    # Intentar YAML por defecto
                    try:
                        import yaml
                        f.seek(0)
                        return yaml.safe_load(f) or {}
                    except Exception:
                        f.seek(0)
                        return json.load(f) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {ruta}")
        except Exception as e:
            raise RuntimeError(f"Error cargando configuración desde '{ruta}': {e}")
    
    def _cargar_configuracion(self, config: Dict[str, Any]):
        """
        Carga parámetros desde el diccionario de configuración.
        
        Establece atributos del modelo que serán accedidos por los agentes.
        """
        # Parámetros de simulación
        simulation = config.get('simulation', {})
        self.infectados_iniciales = simulation.get('infectados_iniciales', 5)
        self.mosquitos_infectados_iniciales = simulation.get('mosquitos_infectados_iniciales', 2)
        
        # Parámetros de enfermedad humana (SEIR)
        human_disease = config.get('human_disease', {})
        self.incubation_period = human_disease.get('incubation_period', 5.0)
        self.infectious_period = human_disease.get('infectious_period', 6.0)
        
        # Parámetros de enfermedad mosquito (SI)
        mosquito_disease = config.get('mosquito_disease', {})
        self.mortality_rate = mosquito_disease.get('mortality_rate', 0.05)
        self.sensory_range = mosquito_disease.get('sensory_range', 3)
        
        # Parámetros de transmisión
        transmission = config.get('transmission', {})
        self.mosquito_to_human_prob = transmission.get('mosquito_to_human_prob', 0.6)  # α
        self.human_to_mosquito_prob = transmission.get('human_to_mosquito_prob', 0.275)  # β
        
        # Parámetros de movilidad humana (probabilidades diarias por tipo)
        mobility = config.get('mobility', {})
        
        # Estudiantes (Tipo 1)
        student_probs = mobility.get('student_daily_probabilities', {})
        self.student_prob_home = student_probs.get('home', 0.55)
        self.student_prob_destination = student_probs.get('destination', 0.35)
        self.student_prob_park = student_probs.get('park', 0.10)
        
        # Trabajadores (Tipo 2)
        worker_probs = mobility.get('worker_daily_probabilities', {})
        self.worker_prob_home = worker_probs.get('home', 0.60)
        self.worker_prob_destination = worker_probs.get('destination', 0.35)
        self.worker_prob_park = worker_probs.get('park', 0.05)
        
        # Móviles continuos (Tipo 3)
        mobile_probs = mobility.get('mobile_daily_probabilities', {})
        self.mobile_prob_home = mobile_probs.get('home', 0.40)
        self.mobile_prob_destination = mobile_probs.get('destination', 0.0)
        self.mobile_prob_park = mobile_probs.get('park', 0.20)
        self.mobile_prob_random = mobile_probs.get('random', 0.40)
        
        # Estacionarios (Tipo 4)
        stationary_probs = mobility.get('stationary_daily_probabilities', {})
        self.stationary_prob_home = stationary_probs.get('home', 0.95)
        self.stationary_prob_destination = stationary_probs.get('destination', 0.0)
        self.stationary_prob_park = stationary_probs.get('park', 0.05)
        self.stationary_prob_random = stationary_probs.get('random', 0.0)
        
        # Parámetros de reproducción de mosquitos
        breeding = config.get('mosquito_breeding', {})
        self.eggs_per_female = breeding.get('eggs_per_female', 100)
        self.mating_probability = breeding.get('mating_probability', 0.6)
        self.female_ratio = breeding.get('female_ratio', 0.5)
        
        # Modelo de grados-día acumulados (GDD) para desarrollo inmaduro
        # Basado en Tun-Lin et al. (1999) para Aedes aegypti
        self.immature_development_threshold = breeding.get('immature_development_threshold', 8.3)  # T_base_inmaduro (°C)
        self.immature_thermal_constant = breeding.get('immature_thermal_constant', 181.2)  # K_inmaduro (°C·día)
        
        self.rainfall_threshold = breeding.get('rainfall_threshold', 0.0)
        self.breeding_site_ratio = breeding.get('breeding_site_ratio', 0.2)
        
        # Ciclo gonotrófico (días entre puestas)
        self.gonotrophic_cycle_days = breeding.get('gonotrophic_cycle_days', 3)
        
        # Sitios de cría temporales (charcos post-lluvia)
        temp_sites = breeding.get('temporary_sites', {})
        self.temp_site_min_rainfall = temp_sites.get('min_rainfall', 5.0)  # mm mínimos
        self.temp_site_sites_per_mm = temp_sites.get('sites_per_mm', 0.5)  # charcos/mm
        self.temp_site_duration_days = temp_sites.get('duration_days', 7)  # días de persistencia
        self.temp_site_max_sites = temp_sites.get('max_sites', 100)  # límite máximo
        
        # Distribución de tipos de movilidad
        mobility_dist = config.get('population', {}).get('mobility_distribution', {})
        self.mobility_distribution_student = mobility_dist.get('student', 0.30)
        self.mobility_distribution_worker = mobility_dist.get('worker', 0.40)
        self.mobility_distribution_mobile = mobility_dist.get('mobile', 0.20)
        self.mobility_distribution_stationary = mobility_dist.get('stationary', 0.10)
        
        # Parámetros del entorno (tipos de celdas)
        environment = config.get('environment', {})
        cell_types = environment.get('cell_types', {})
        self.water_ratio = cell_types.get('water_ratio', 0.05)
        self.park_ratio = cell_types.get('park_ratio', 0.10)
        
        # Tamaños de zonas
        zone_sizes = environment.get('zone_sizes', {})
        self.water_min = zone_sizes.get('water_min', 2)
        self.water_max = zone_sizes.get('water_max', 4)
        self.park_min = zone_sizes.get('park_min', 3)
        self.park_max = zone_sizes.get('park_max', 6)
        
        # Parámetros de vuelo de mosquitos
        mosquito_flight = environment.get('mosquito_flight', {})
        self.max_range = mosquito_flight.get('max_range', 5)
        
        # Parámetros de generación del grid
        grid_generation = environment.get('grid_generation', {})
        self.max_placement_failures = grid_generation.get('max_placement_failures', 50)
        self.max_total_attempts = grid_generation.get('max_total_attempts', 500)
        
        # Parámetros de control LSM
        control = config.get('control', {})
        lsm = control.get('lsm', {})
        self.lsm_frequency_days = lsm.get('frequency_days', 7)
        self.lsm_coverage = lsm.get('coverage', 0.7)
        self.lsm_effectiveness = lsm.get('effectiveness', 0.8)
        
        # Parámetros de control ITN/IRS
        itn_irs = control.get('itn_irs', {})
        self.itn_irs_duration_days = itn_irs.get('duration_days', 90)
        self.itn_irs_coverage = itn_irs.get('coverage', 0.6)
        self.itn_irs_effectiveness = itn_irs.get('effectiveness', 0.7)
        
        # Parámetros de comportamiento humano
        human_behavior = config.get('human_behavior', {})
        self.isolation_probability = human_behavior.get('isolation_probability', 0.7)
        self.infected_mobility_radius = human_behavior.get('infected_mobility_radius', 1)
        
        # Validar que las probabilidades de movilidad sumen 1.0 para cada tipo
        self._validar_probabilidades_movilidad()
    
    def _validar_probabilidades_movilidad(self):
        """
        Valida que las probabilidades de movilidad diarias sumen 1.0 para cada tipo.
        
        Lanza ValueError si alguna suma de probabilidades es inválida (|suma - 1.0| > 0.01).
        Esto previene errores de configuración que causarían comportamiento indefinido.
        """
        tolerancia = 0.01  # Tolerancia para errores de redondeo
        
        tipos_validar = [
            ("Estudiante", self.student_prob_home, self.student_prob_destination, 
             self.student_prob_park, 0.0),
            ("Trabajador", self.worker_prob_home, self.worker_prob_destination, 
             self.worker_prob_park, 0.0),
            ("Móvil Continuo", self.mobile_prob_home, self.mobile_prob_destination, 
             self.mobile_prob_park, self.mobile_prob_random),
            ("Estacionario", self.stationary_prob_home, self.stationary_prob_destination, 
             self.stationary_prob_park, self.stationary_prob_random)
        ]
        
        for nombre, p_home, p_dest, p_park, p_random in tipos_validar:
            suma = p_home + p_dest + p_park + p_random
            if abs(suma - 1.0) > tolerancia:
                raise ValueError(
                    f"Probabilidades de movilidad para '{nombre}' no suman 1.0: "
                    f"home={p_home}, destination={p_dest}, park={p_park}, random={p_random} "
                    f"(suma={suma:.4f}). Revise la configuración."
                )
    
    def _cargar_configuracion_default(self):
        """Carga configuración por defecto si no se proporciona config."""
        # Parámetros de simulación
        self.infectados_iniciales = 5
        self.mosquitos_infectados_iniciales = 2
        
        # Parámetros de enfermedad humana (SEIR)
        self.incubation_period = 5.0  # Ne = 5 días
        self.infectious_period = 6.0  # Ni = 6 días
        
        # Parámetros de enfermedad mosquito (SI)
        self.mortality_rate = 0.05  # Mr = 0.05 por día
        self.sensory_range = 3  # Sr = 3 celdas
        
        # Parámetros de transmisión
        self.mosquito_to_human_prob = 0.6  # α = 0.6
        self.human_to_mosquito_prob = 0.275  # β = 0.275
        
        # Parámetros de movilidad humana (probabilidades diarias por tipo)
        # Estudiantes (Tipo 1)
        self.student_prob_home = 0.55
        self.student_prob_destination = 0.35
        self.student_prob_park = 0.10
        
        # Trabajadores (Tipo 2)
        self.worker_prob_home = 0.60
        self.worker_prob_destination = 0.35
        self.worker_prob_park = 0.05
        
        # Móviles continuos (Tipo 3)
        self.mobile_prob_home = 0.40
        self.mobile_prob_destination = 0.0
        self.mobile_prob_park = 0.20
        self.mobile_prob_random = 0.40
        
        # Estacionarios (Tipo 4)
        self.stationary_prob_home = 0.95
        self.stationary_prob_destination = 0.0
        self.stationary_prob_park = 0.05
        self.stationary_prob_random = 0.0
        
        # Parámetros de reproducción de mosquitos
        self.eggs_per_female = 100
        self.mating_probability = 0.6
        self.female_ratio = 0.5
        
        # Modelo de grados-día acumulados (GDD) para desarrollo inmaduro
        self.immature_development_threshold = 8.3  # T_base_inmaduro (°C)
        self.immature_thermal_constant = 181.2  # K_inmaduro (°C·día)
        
        self.rainfall_threshold = 0.0
        self.breeding_site_ratio = 0.2
        
        # Ciclo gonotrófico (días entre puestas)
        self.gonotrophic_cycle_days = 3  # 2-4 días según literatura
        
        # Sitios de cría temporales (charcos post-lluvia)
        self.temp_site_min_rainfall = 5.0  # mm mínimos
        self.temp_site_sites_per_mm = 0.5  # charcos/mm
        self.temp_site_duration_days = 7  # días de persistencia
        self.temp_site_max_sites = 100  # límite máximo
        
        # Distribución de tipos de movilidad
        self.mobility_distribution_student = 0.30
        self.mobility_distribution_worker = 0.40
        self.mobility_distribution_mobile = 0.20
        self.mobility_distribution_stationary = 0.10
        
        # Parámetros del entorno (tipos de celdas)
        self.water_ratio = 0.05  # 5% agua
        self.park_ratio = 0.10  # 10% parques
        
        # Tamaños de zonas
        self.water_min = 2
        self.water_max = 4
        self.park_min = 3
        self.park_max = 6
        
        # Parámetros de vuelo de mosquitos
        self.max_range = 5  # 5 celdas (~190m si celda=38m)
        
        # Parámetros de generación del grid
        self.max_placement_failures = 50  # Límite de fallos consecutivos
        self.max_total_attempts = 500  # Límite total de intentos
        
        # Parámetros de control LSM
        self.lsm_frequency_days = 7
        self.lsm_coverage = 0.7
        self.lsm_effectiveness = 0.8
        
        # Parámetros de control ITN/IRS
        self.itn_irs_duration_days = 90
        self.itn_irs_coverage = 0.6
        self.itn_irs_effectiveness = 0.7
        
        # Parámetros de comportamiento humano
        self.isolation_probability = 0.7  # 70% se aíslan
        self.infected_mobility_radius = 1  # 1 celda de radio
        
        # Validar que las probabilidades de movilidad sumen 1.0 para cada tipo
        self._validar_probabilidades_movilidad()
    
    def step(self):
        """
        Ejecuta un paso de simulación (1 día).
        
        Secuencia diaria (10 pasos según el paper):
        1. Actualizar fecha
        2. Actualizar clima (temperatura, precipitación)
        3. Aplicar estrategias de control si corresponde
        4. Activar agentes (humanos y mosquitos)
        5. Procesar interacciones (picaduras, transmisión)
        6. Reproducción de mosquitos
        7. Eclosión de huevos
        8. Actualizar estados SEIR/SI
        9. Remover agentes muertos
        10. Recolectar métricas
        """
        self.dia_simulacion += 1
        self.steps += 1  # Incrementar contador de steps
        self.fecha_actual = self.fecha_inicio + timedelta(days=self.dia_simulacion)
        
        # 1. Actualizar clima
        self._actualizar_clima()
        
        # 2. Actualizar sitios de cría temporales (charcos post-lluvia)
        self._actualizar_sitios_cria_temporales()
         
        # 3. Aplicar estrategias de control
        #self._aplicar_control()
        
        # 4. Activar todos los agentes (actualiza estados, movimiento, interacciones)
        print(f"\n🔄 Activando {len(self.agents)} agentes...", flush=True)
        import time
        start_time = time.time()
        
        # Contar tipos de agentes
        from src.agents.human_agent import HumanAgent
        from src.agents.mosquito_agent import MosquitoAgent
        humanos = sum(1 for a in self.agents if isinstance(a, HumanAgent))
        mosquitos = sum(1 for a in self.agents if isinstance(a, MosquitoAgent))
        print(f"   👥 Humanos: {humanos}, 🦟 Mosquitos: {mosquitos}", flush=True)
        
        agentes_lista = list(self.agents)
        self.random.shuffle(agentes_lista)
        
        for idx, agente in enumerate(agentes_lista):
            if idx % 500 == 0:
                elapsed = time.time() - start_time
                print(f"   Procesando agente {idx}/{len(agentes_lista)} ({idx/len(agentes_lista)*100:.1f}%) - {elapsed:.2f}s", flush=True)
            agente.step()
        
        elapsed = time.time() - start_time
        print(f"✅ Agentes activados en {elapsed:.2f}s", flush=True)
        
        # 4. Recolectar datos
        self.datacollector.collect(self)
    
    def _actualizar_clima(self):
        """
        Actualiza temperatura y precipitación diarias desde el archivo CSV.
        
        Este método requiere que climate_loader esté configurado correctamente.
        Si no hay datos disponibles para la fecha actual, lanza un error.
        
        Raises
        ------
        ValueError
            Si no se ha configurado el cargador de datos climáticos
        KeyError
            Si no hay datos para la fecha actual
        """
        if not self.climate_loader:
            raise ValueError(
                "No se ha configurado el cargador de datos climáticos. "
                "Debe proporcionar climate_data_path al crear el modelo."
            )
        
        try:
            # Obtener datos desde CSV
            temp, precip = self.climate_loader.get_climate_data(self.fecha_actual)
            self.temperatura_actual = temp
            self.precipitacion_actual = precip
        except KeyError:
            raise KeyError(
                f"No hay datos climáticos disponibles para la fecha {self.fecha_actual.date()}. "
                f"Verifique que la fecha esté dentro del rango del archivo CSV."
            )
    
    def _actualizar_sitios_cria_temporales(self):
        """
        Gestiona sitios de cría temporales (charcos post-lluvia).
        
        Lógica:
        1. Crear nuevos charcos si precipitación >= umbral
        2. Decrementar días restantes de charcos existentes
        3. Eliminar charcos secos (días_restantes = 0)
        
        Parámetros:
        - temp_site_min_rainfall: mm mínimos para crear charcos (5.0)
        - temp_site_sites_per_mm: charcos por mm de lluvia (0.5)
        - temp_site_duration_days: días que persiste un charco (7)
        - temp_site_max_sites: límite máximo de charcos simultáneos (100)
        """
        # 1. Crear nuevos charcos si hay suficiente lluvia
        if self.precipitacion_actual >= self.temp_site_min_rainfall:
            # Calcular número de charcos a crear
            num_nuevos = int(self.precipitacion_actual * self.temp_site_sites_per_mm)
            
            # Limitar al máximo permitido
            espacio_disponible = self.temp_site_max_sites - len(self.sitios_cria_temporales)
            num_nuevos = min(num_nuevos, espacio_disponible)
            
            # Crear charcos en posiciones aleatorias
            for _ in range(num_nuevos):
                pos = (self.random.randrange(self.width),
                      self.random.randrange(self.height))
                # Reiniciar duración si el sitio ya existe (lluvia renueva charco)
                self.sitios_cria_temporales[pos] = self.temp_site_duration_days
        
        # 2. Decrementar días restantes y eliminar charcos secos
        sitios_a_eliminar = []
        for pos, dias_restantes in self.sitios_cria_temporales.items():
            dias_restantes -= 1
            if dias_restantes <= 0:
                sitios_a_eliminar.append(pos)
            else:
                self.sitios_cria_temporales[pos] = dias_restantes
        
        # 3. Eliminar charcos secos
        for pos in sitios_a_eliminar:
            del self.sitios_cria_temporales[pos]
    
    def _aplicar_control(self):
        """
        Aplica estrategias de control según configuración.
        
        LSM (Larval Source Management):
        - Frecuencia: lsm_frequency_days (por defecto 7 días)
        - Cobertura: lsm_coverage (por defecto 70%)
        - Efectividad: lsm_effectiveness (por defecto 80%)
        
        ITN/IRS (Insecticide-Treated Nets / Indoor Residual Spraying):
        - Duración: itn_irs_duration_days (por defecto 90 días)
        - Cobertura: itn_irs_coverage (por defecto 60% hogares)
        - Efectividad: itn_irs_effectiveness (por defecto 70%)
        """
        # LSM: Aplicar según frecuencia configurada
        if self.usar_lsm and self.dia_simulacion % self.lsm_frequency_days == 0:
            self._aplicar_lsm()
        
        # ITN/IRS: Activar según necesidad
        if self.usar_itn_irs:
            self._aplicar_itn_irs()
    
    def _aplicar_lsm(self):
        """
        Aplica control larvario (LSM).
        
        Elimina huevos en sitios de cría con cobertura y efectividad configurables
        (por defecto: 70% cobertura × 80% efectividad = 56% reducción).
        """
        self.lsm_activo = True
        
        # Obtener todos los huevos
        huevos = [a for a in self.agents 
                 if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.HUEVO]
        
        # Aplicar reducción: cobertura × efectividad
        reduccion = self.lsm_coverage * self.lsm_effectiveness
        for huevo in huevos:
            if self.random.random() < reduccion:
                huevo.remove()
                self.agents.remove(huevo)
    
    def _aplicar_itn_irs(self):
        """
        Aplica protección con redes/insecticidas (ITN/IRS).
        
        Reduce probabilidad de picadura en 70% para 60% de humanos.
        NOTA: La reducción se aplica directamente en la interacción mosquito-humano.
        """
        self.itn_irs_activo = True
        # La lógica de reducción se implementa en MosquitoAgent.intentar_picar()
    
    def _inicializar_mapa_celdas(self) -> Dict[Tuple[int, int], 'Celda']:
        """
        Crea mapa de celdas con tipos asignados.
        
        Distribución desde configuración (por defecto):
        - 5% agua (criaderos permanentes como zonas)
        - 10% parques (zonas recreativas contiguas)
        - 85% urbana (viviendas, oficinas, escuelas)
        
        Los parques y cuerpos de agua se crean como ZONAS contiguas (clusters),
        no como celdas aisladas, para mayor realismo.
        
        Returns
        -------
        Dict[Tuple[int, int], Celda]
            Diccionario mapeando coordenadas a objetos Celda
        """
        from .celda import Celda, TipoCelda
        
        mapa = {}
        
        # Inicializar todo como urbano
        for x in range(self.width):
            for y in range(self.height):
                mapa[(x, y)] = Celda(TipoCelda.URBANA, (x, y))
        
        # Obtener proporciones desde configuración
        prop_agua = getattr(self, 'water_ratio', 0.05)
        prop_parques = getattr(self, 'park_ratio', 0.10)
        
        # Calcular cantidades totales
        total_celdas = self.width * self.height
        num_agua = int(total_celdas * prop_agua)
        num_parques = int(total_celdas * prop_parques)
        
        # Crear zonas de agua (clusters)
        celdas_ocupadas = set()
        self._crear_zonas_tipo(mapa, TipoCelda.AGUA, num_agua, celdas_ocupadas)
        
        # Crear zonas de parques (clusters)
        self._crear_zonas_tipo(mapa, TipoCelda.PARQUE, num_parques, celdas_ocupadas)
        
        return mapa
    
    def _crear_zonas_tipo(
        self,
        mapa: Dict[Tuple[int, int], 'Celda'],
        tipo: 'TipoCelda',
        num_celdas_objetivo: int,
        celdas_ocupadas: set
    ):
        """
        Crea zonas contiguas de un tipo específico.
        Versión optimizada con límites adaptativos.
        """
        from .celda import Celda
        
        celdas_asignadas = 0
        
        # Cachear tamaños fuera del loop
        if tipo.value == "agua":
            tamaño_min = self.water_min
            tamaño_max = self.water_max
        else:
            tamaño_min = self.park_min
            tamaño_max = self.park_max
        
        # Límite adaptativo: más intentos al inicio, menos cuando el grid está lleno
        intentos_consecutivos_fallidos = 0
        max_fallos_consecutivos = self.max_placement_failures  # Cargado desde configuración
        
        total_intentos = 0
        max_total_intentos = self.max_total_attempts  # Cargado desde configuración
        
        while celdas_asignadas < num_celdas_objetivo and total_intentos < max_total_intentos:
            total_intentos += 1
            
            # Rendirse si hay muchos fallos consecutivos (grid probablemente lleno)
            if intentos_consecutivos_fallidos >= max_fallos_consecutivos:
                print(f"Advertencia: No se pudo asignar todas las celdas de tipo {tipo.value}. "
                      f"Asignadas: {celdas_asignadas}/{num_celdas_objetivo}")
                break
            
            # Determinar tamaño de zona
            ancho = self.random.randint(tamaño_min, tamaño_max)
            alto = self.random.randint(tamaño_min, tamaño_max)
            
            # Validar bounds antes de generar
            max_x = self.width - ancho
            max_y = self.height - alto
            
            if max_x < 1 or max_y < 1:
                intentos_consecutivos_fallidos += 1
                continue
            
            # Elegir centro aleatorio
            centro_x = self.random.randint(1, max_x)
            centro_y = self.random.randint(1, max_y)
            
            # Generar lista de celdas
            celdas_zona = [
                (centro_x + dx, centro_y + dy)
                for dx in range(ancho)
                for dy in range(alto)
            ]
            
            # Validación rápida: si alguna está ocupada, rechazar
            if any(pos in celdas_ocupadas for pos in celdas_zona):
                intentos_consecutivos_fallidos += 1
                continue
            
            # Zona válida: asignar todas las celdas
            for pos in celdas_zona:
                mapa[pos] = Celda(tipo, pos)
                celdas_ocupadas.add(pos)
                celdas_asignadas += 1
                
                if celdas_asignadas >= num_celdas_objetivo:
                    return  # Éxito completo
            
            # Zona colocada con éxito, resetear contador de fallos
            intentos_consecutivos_fallidos = 0
        
        # Si llegamos aquí sin completar, advertir
        if celdas_asignadas < num_celdas_objetivo:
            print(f"Advertencia: Solo se asignaron {celdas_asignadas}/{num_celdas_objetivo} "
                  f"celdas de tipo {tipo.value}")
    
    def _generar_sitios_cria(self) -> List[Tuple[int, int]]:
        """
        Genera ubicaciones de sitios de cría de mosquitos desde mapa de celdas.
        
        Extrae las celdas tipo AGUA como criaderos permanentes.
        
        Returns
        -------
        List[Tuple[int, int]]
            Lista de coordenadas de sitios de cría permanentes
        """
        # Extraer celdas tipo AGUA del mapa
        sitios = [pos for pos, celda in self.mapa_celdas.items() 
                 if celda.tipo == TipoCelda.AGUA]
        
        return sitios
    
    def _crear_indice_espacial_sitios(self) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        """
        Crea un índice espacial dividiendo el grid en sectores.
        
        Cada sector contiene la lista de sitios de cría en esa región.
        Esto permite búsqueda O(1) en lugar de O(n) para encontrar sitios cercanos.
        
        Returns
        -------
        Dict[Tuple[int, int], List[Tuple[int, int]]]
            Diccionario {(sector_x, sector_y): [lista de sitios en ese sector]}
        """
        indice = {}
        
        # Asignar cada sitio a su sector correspondiente
        for sitio in self.sitios_cria:
            x, y = sitio
            sector_x = x // self.sector_size
            sector_y = y // self.sector_size
            sector = (sector_x, sector_y)
            
            if sector not in indice:
                indice[sector] = []
            indice[sector].append(sitio)
        
        return indice
    
    def obtener_sitios_cercanos(self, posicion: Tuple[int, int], 
                                 max_range: int) -> List[Tuple[int, int]]:
        """
        Obtiene sitios de cría cercanos usando el índice espacial.
        
        Solo busca en los sectores que podrían contener sitios dentro del rango.
        Esto reduce drásticamente el número de comparaciones de distancia.
        
        Parameters
        ----------
        posicion : Tuple[int, int]
            Posición desde donde buscar
        max_range : int
            Rango máximo de búsqueda
            
        Returns
        -------
        List[Tuple[int, int]]
            Lista de sitios de cría dentro del rango (permanentes + temporales)
        """
        x, y = posicion
        
        # Calcular sectores a revisar (sector actual + vecinos alcanzables)
        sector_x = x // self.sector_size
        sector_y = y // self.sector_size
        
        # Número de sectores a revisar en cada dirección
        # (max_range podría cruzar múltiples sectores)
        sectores_radio = (max_range // self.sector_size) + 1
        
        sitios_candidatos = []
        
        # Revisar solo sectores relevantes
        for dx in range(-sectores_radio, sectores_radio + 1):
            for dy in range(-sectores_radio, sectores_radio + 1):
                sector = (sector_x + dx, sector_y + dy)
                if sector in self.indice_sitios:
                    sitios_candidatos.extend(self.indice_sitios[sector])
        
        # Incluir sitios temporales (charcos post-lluvia)
        sitios_candidatos.extend(self.sitios_cria_temporales.keys())
        
        return sitios_candidatos
    
    def _generar_lista_parques(self) -> List[Tuple[int, int]]:
        """
        Genera lista de posiciones de parques para búsqueda rápida.
        
        Evita tener que filtrar todas las celdas cada vez que un humano
        busca un parque cercano.
        
        Returns
        -------
        List[Tuple[int, int]]
            Lista de coordenadas de parques
        """
        # Extraer celdas tipo PARQUE del mapa
        parques = [pos for pos, celda in self.mapa_celdas.items() 
                  if celda.tipo == TipoCelda.PARQUE]
        
        return parques
    
    def _generar_lista_urbanas(self) -> List[Tuple[int, int]]:
        """
        Genera lista de posiciones urbanas para asignación eficiente.
        
        Pre-calcula todas las celdas urbanas al inicio para evitar búsquedas
        repetitivas durante la creación de agentes. Con 3000 humanos, esto
        ahorra hasta 6000 búsquedas de coordenadas válidas.
        
        Returns
        -------
        List[Tuple[int, int]]
            Lista de coordenadas de celdas urbanas
        """
        # Extraer celdas tipo URBANA del mapa
        urbanas = [pos for pos, celda in self.mapa_celdas.items() 
                  if celda.tipo == TipoCelda.URBANA]
        
        return urbanas
    
    def _crear_humanos(self, num_humanos: int, infectados_iniciales: int):
        """
        Crea la población inicial de humanos.
        
        Distribución desde configuración (por defecto):
        - 30% Estudiantes (Tipo 1)
        - 40% Trabajadores (Tipo 2)
        - 20% Móviles continuos (Tipo 3)
        - 10% Estacionarios (Tipo 4)
        
        Parameters
        ----------
        num_humanos : int
            Número total de humanos
        infectados_iniciales : int
            Número de humanos infectados al inicio
        """
        # Usar distribución desde configuración
        tipos_dist = [
            (TipoMovilidad.ESTUDIANTE, self.mobility_distribution_student),
            (TipoMovilidad.TRABAJADOR, self.mobility_distribution_worker),
            (TipoMovilidad.MOVIL_CONTINUO, self.mobility_distribution_mobile),
            (TipoMovilidad.ESTACIONARIO, self.mobility_distribution_stationary)
        ]
        
        infectados_asignados = 0
        
        for i in range(num_humanos):
            # Determinar tipo de movilidad
            rand = self.random.random()
            acum = 0
            tipo = TipoMovilidad.ESTACIONARIO
            for t, prob in tipos_dist:
                acum += prob
                if rand < acum:
                    tipo = t
                    break
            
            # Asignar hogar en celda urbana (fija para toda la simulación)
            # Selección directa desde lista pre-calculada: O(1) vs O(100) del método anterior
            pos_hogar = self.random.choice(self.celdas_urbanas)
            
            # Asignar destino (escuela/trabajo) en celda urbana para estudiantes y trabajadores
            # Esta posición es FIJA (no cambia durante la simulación)
            # Las visitas al parque se manejan aparte en la lógica de movilidad del agente
            pos_destino = None
            if tipo in [TipoMovilidad.ESTUDIANTE, TipoMovilidad.TRABAJADOR]:
                pos_destino = self.random.choice(self.celdas_urbanas)
            
            # Crear agente
            unique_id = self.next_id()
            humano = HumanAgent(
                unique_id=unique_id,
                model=self,
                tipo_movilidad=tipo,
                pos_hogar=pos_hogar,
                pos_destino=pos_destino
            )
            
            # Asignar estado infectado a algunos
            if infectados_asignados < infectados_iniciales:
                humano.estado = EstadoSalud.INFECTADO
                infectados_asignados += 1
            
            # Colocar en grid y agregar a scheduler
            self.grid.place_agent(humano, pos_hogar)
            self.agents.add(humano)
    
    def _crear_mosquitos(self, num_mosquitos: int, infectados_iniciales: int):
        """
        Crea la población inicial de mosquitos adultos.
        
        Optimización: Solo crea hembras (100%), ya que los machos no aportan
        información al modelo epidemiológico (no pican, no transmiten, no ponen huevos).
        El apareamiento se modela implícitamente con mating_probability.
        
        Parameters
        ----------
        num_mosquitos : int
            Número total de mosquitos hembra
        infectados_iniciales : int
            Número de mosquitos infectados al inicio
        """
        infectados_asignados = 0
        
        for i in range(num_mosquitos):
            # Posición aleatoria
            pos = (self.random.randrange(self.width),
                  self.random.randrange(self.height))
            
            # Crear agente (solo hembras)
            unique_id = self.next_id()
            mosquito = MosquitoAgent(
                unique_id=unique_id,
                model=self,
                etapa=EtapaVida.ADULTO
            )
            
            # Asignar estado infectado a algunos
            if infectados_asignados < infectados_iniciales:
                mosquito.estado = EstadoMosquito.INFECTADO
                infectados_asignados += 1
            
            # Colocar en grid y agregar a scheduler
            self.grid.place_agent(mosquito, pos)
            self.agents.add(mosquito)
    
    def _crear_huevos(self, num_huevos: int):
        """
        Crea la población inicial de huevos (solo hembras).
        
        Los huevos se colocan en sitios de cría aleatorios.
        Solo se crean huevos hembra ya que los machos no aportan al modelo.
        
        Parameters
        ----------
        num_huevos : int
            Número total de huevos hembra a crear
        """
        for i in range(num_huevos):
            # Sitio de cría aleatorio
            if self.sitios_cria:
                sitio = self.random.choice(self.sitios_cria)
            else:
                sitio = (self.random.randrange(self.width),
                        self.random.randrange(self.height))
            
            # Crear huevo hembra
            unique_id = self.next_id()
            huevo = MosquitoAgent(
                unique_id=unique_id,
                model=self,
                etapa=EtapaVida.HUEVO,
                sitio_cria=sitio
            )
            
            # Agregar a scheduler (no al grid hasta eclosionar)
            self.agents.add(huevo)
    
    def next_id(self) -> int:
        """
        Genera el siguiente ID único para agentes.
        
        Returns
        -------
        int
            ID único incrementado
        """
        current_id = self._next_id
        self._next_id += 1
        return current_id
    
    def _contar_humanos_estado(self, estado: EstadoSalud) -> int:
        """Cuenta humanos en un estado epidemiológico específico."""
        return sum(1 for a in self.agents 
                  if isinstance(a, HumanAgent) and a.estado == estado)
    
    def _contar_mosquitos_estado(self, estado: EstadoMosquito) -> int:
        """Cuenta mosquitos adultos en un estado epidemiológico específico."""
        return sum(1 for a in self.agents 
                  if isinstance(a, MosquitoAgent) 
                  and a.etapa == EtapaVida.ADULTO 
                  and a.estado == estado)
    
    def _contar_mosquitos_adultos(self) -> int:
        """Cuenta total de mosquitos adultos."""
        return sum(1 for a in self.agents 
                  if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.ADULTO)
    
    def _contar_huevos(self) -> int:
        """Cuenta total de huevos."""
        return sum(1 for a in self.agents 
                  if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.HUEVO)
    
    def __repr__(self) -> str:
        """Representación en cadena del modelo."""
        return (f"DengueModel(dia={self.dia_simulacion}, "
                f"humanos={self.num_humanos}, "
                f"mosquitos={self._contar_mosquitos_adultos()}, "
                f"infectados={self._contar_humanos_estado(EstadoSalud.INFECTADO)})")
