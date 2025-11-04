"""
Modelo principal ABM del Dengue para Bucaramanga.

Este módulo implementa el modelo de simulación basado en agentes
con integración climática y estrategias de control.

Basado en Jindal & Rao (2017) adaptado a Bucaramanga, Colombia.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

from mesa import Model
#from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import requests

from ..agents import (
    HumanAgent, MosquitoAgent,
    EstadoSalud, EstadoMosquito, TipoMovilidad, EtapaVida
)
from .celda import Celda, TipoCelda


class DengueModel(Model):
    """
    Modelo ABM del Dengue con integración climática y control.
    
    Simula la dinámica de transmisión del dengue en Bucaramanga con:
    - Población humana con estados SEIR y movilidad diferenciada
    - Población de mosquitos con estados SI y ciclo de vida completo
    - Clima dinámico (temperatura y precipitación vía Meteostat)
    - Estrategias de control: LSM (control larvario) e ITN/IRS (camas/insecticidas)
    - Grid espacial 50×50 sin GIS
    
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
        seed: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        
        # Configuración del modelo
        self.width = width
        self.height = height
        self.num_humanos = num_humanos
        self.num_mosquitos = num_mosquitos
        self.num_huevos = num_huevos
        
        # Cargar configuración desde diccionario si se proporciona
        if config:
            self._cargar_configuracion(config)
        else:
            self._cargar_configuracion_default()
        
        # Semilla de aleatoriedad
        if seed is not None:
            self.random.seed(seed)
            np.random.seed(seed)
        
        # Grid espacial (50×50, múltiples agentes por celda, sin toroide)
        self.grid = MultiGrid(width, height, torus=False)
        
        # Scheduler de activación aleatoria
        #self.schedule = RandomActivation(self)
        
        # Contador de steps propio (reemplaza schedule.steps en Mesa 2.1)
        self.steps = 0

        # Variables climáticas
        self.fecha_inicio = fecha_inicio
        self.fecha_actual = fecha_inicio
        self.dia_simulacion = 0
        self.temperatura_actual = 25.0  # °C (valor inicial)
        self.precipitacion_actual = 0.0  # mm (valor inicial)
        
        # Estrategias de control
        self.usar_lsm = usar_lsm
        self.usar_itn_irs = usar_itn_irs
        self.lsm_activo = False
        self.itn_irs_activo = False
        
        # Mapa de celdas con tipos (urbana, parque, agua)
        self.mapa_celdas = self._inicializar_mapa_celdas()
        
        # Sitios de cría (desde mapa de celdas)
        self.sitios_cria = self._generar_sitios_cria()
        
        # Contador de IDs único
        self._next_id = 0
        
        # Crear agentes
        self._crear_humanos(num_humanos, infectados_iniciales)
        self._crear_mosquitos(num_mosquitos, mosquitos_infectados_iniciales)
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
    
    def _cargar_configuracion(self, config: Dict[str, Any]):
        """
        Carga parámetros desde el diccionario de configuración.
        
        Establece atributos del modelo que serán accedidos por los agentes.
        """
        # Parámetros de enfermedad humana (SEIR)
        human_disease = config.get('human_disease', {})
        self.incubacion_humano = human_disease.get('incubation_period', 5.0)
        self.infeccioso_humano = human_disease.get('infectious_period', 6.0)
        
        # Parámetros de enfermedad mosquito (SI)
        mosquito_disease = config.get('mosquito_disease', {})
        self.mortalidad_mosquito = mosquito_disease.get('mortality_rate', 0.05)
        self.rango_sensorial_mosquito = mosquito_disease.get('sensory_range', 3)
        
        # Parámetros de transmisión
        transmission = config.get('transmission', {})
        self.prob_transmision_mosquito_humano = transmission.get('mosquito_to_human_prob', 0.6)  # α
        self.prob_transmision_humano_mosquito = transmission.get('human_to_mosquito_prob', 0.275)  # β
        
        # Parámetros de movilidad humana
        mobility = config.get('mobility', {})
        self.prob_parque_estudiante = mobility.get('park_probability_student', 0.3)
        self.prob_parque_trabajador = mobility.get('park_probability_worker', 0.1)
        self.prob_parque_movil = mobility.get('park_probability_mobile', 0.15)
        self.prob_parque_estacionario = mobility.get('park_probability_stationary', 0.05)
        
        self.hora_inicio_escuela = mobility.get('school_start_hour', 7)
        self.hora_fin_escuela = mobility.get('school_end_hour', 15)
        self.hora_inicio_trabajo = mobility.get('work_start_hour', 7)
        self.hora_fin_trabajo = mobility.get('work_end_hour', 17)
        self.hora_inicio_parque = mobility.get('park_start_hour', 16)
        self.hora_fin_parque = mobility.get('park_end_hour', 19)
        
        self.intervalo_movimiento_horas = mobility.get('mobile_move_interval_hours', 2)
        self.hora_inicio_movil_activo = mobility.get('mobile_active_start_hour', 7)
        self.hora_fin_movil_activo = mobility.get('mobile_active_end_hour', 19)
        
        # Parámetros de reproducción de mosquitos
        breeding = config.get('mosquito_breeding', {})
        self.huevos_por_hembra = breeding.get('eggs_per_female', 100)
        self.prob_apareamiento_mosquito = breeding.get('mating_probability', 0.6)
        self.proporcion_hembras = breeding.get('female_ratio', 0.5)
        
        # Desarrollo dependiente de temperatura
        self.dias_base_maduracion_huevo = breeding.get('egg_maturation_base_days', 3)
        self.temp_optima_maduracion_huevo = breeding.get('egg_maturation_temp_optimal', 21.0)
        self.sensibilidad_temp_maduracion_huevo = breeding.get('egg_maturation_temp_sensitivity', 5.0)
        
        self.dias_base_desarrollo_huevo = breeding.get('egg_to_adult_base_days', 8)
        self.temp_optima_desarrollo_huevo = breeding.get('egg_to_adult_temp_optimal', 25.0)
        self.sensibilidad_temp_desarrollo_huevo = breeding.get('egg_to_adult_temp_sensitivity', 1.0)
        
        self.umbral_precipitacion_cria = breeding.get('rainfall_threshold', 0.0)
        self.proporcion_sitios_cria = breeding.get('breeding_site_ratio', 0.2)
        
        # Distribución de tipos de movilidad
        mobility_dist = config.get('population', {}).get('mobility_distribution', {})
        self.dist_estudiantes = mobility_dist.get('student', 0.25)
        self.dist_trabajadores = mobility_dist.get('worker', 0.35)
        self.dist_moviles = mobility_dist.get('mobile', 0.25)
        self.dist_estacionarios = mobility_dist.get('stationary', 0.15)
        
        # Parámetros del entorno (tipos de celdas)
        environment = config.get('environment', {})
        cell_types = environment.get('cell_types', {})
        self.proporcion_celdas_agua = cell_types.get('water_ratio', 0.05)
        self.proporcion_celdas_parques = cell_types.get('park_ratio', 0.10)
        
        # Tamaños de zonas
        zone_sizes = environment.get('zone_sizes', {})
        self.agua_min = zone_sizes.get('water_min', 2)
        self.agua_max = zone_sizes.get('water_max', 4)
        self.parque_min = zone_sizes.get('park_min', 3)
        self.parque_max = zone_sizes.get('park_max', 6)
        
        # Parámetros de vuelo de mosquitos
        mosquito_flight = environment.get('mosquito_flight', {})
        self.rango_vuelo_max = mosquito_flight.get('max_range', 10)
        
        # Parámetros de comportamiento humano
        human_behavior = config.get('human_behavior', {})
        self.prob_aislamiento = human_behavior.get('isolation_probability', 0.7)
        self.radio_mov_infectado = human_behavior.get('infected_mobility_radius', 1)
    
    def _cargar_configuracion_default(self):
        """Carga configuración por defecto si no se proporciona config."""
        # Parámetros de enfermedad humana (SEIR)
        self.incubacion_humano = 5.0  # Ne = 5 días
        self.infeccioso_humano = 6.0  # Ni = 6 días
        
        # Parámetros de enfermedad mosquito (SI)
        self.mortalidad_mosquito = 0.05  # Mr = 0.05 por día
        self.rango_sensorial_mosquito = 3  # Sr = 3 celdas
        
        # Parámetros de transmisión
        self.prob_transmision_mosquito_humano = 0.6  # α = 0.6
        self.prob_transmision_humano_mosquito = 0.275  # β = 0.275
        
        # Parámetros de movilidad humana
        self.prob_parque_estudiante = 0.3
        self.prob_parque_trabajador = 0.1
        self.prob_parque_movil = 0.15
        self.prob_parque_estacionario = 0.05
        
        self.hora_inicio_escuela = 7
        self.hora_fin_escuela = 15
        self.hora_inicio_trabajo = 7
        self.hora_fin_trabajo = 17
        self.hora_inicio_parque = 16
        self.hora_fin_parque = 19
        
        self.intervalo_movimiento_horas = 2
        self.hora_inicio_movil_activo = 7
        self.hora_fin_movil_activo = 19
        
        # Parámetros de reproducción de mosquitos
        self.huevos_por_hembra = 100
        self.prob_apareamiento_mosquito = 0.6
        self.proporcion_hembras = 0.5
        
        self.dias_base_maduracion_huevo = 3
        self.temp_optima_maduracion_huevo = 21.0
        self.sensibilidad_temp_maduracion_huevo = 5.0
        
        self.dias_base_desarrollo_huevo = 8
        self.temp_optima_desarrollo_huevo = 25.0
        self.sensibilidad_temp_desarrollo_huevo = 1.0
        
        self.umbral_precipitacion_cria = 0.0
        self.proporcion_sitios_cria = 0.2
        
        # Distribución de tipos de movilidad
        self.dist_estudiantes = 0.25
        self.dist_trabajadores = 0.35
        self.dist_moviles = 0.25
        self.dist_estacionarios = 0.15
        
        # Parámetros del entorno (tipos de celdas)
        self.proporcion_celdas_agua = 0.05  # 5% agua
        self.proporcion_celdas_parques = 0.10  # 10% parques
        
        # Tamaños de zonas
        self.agua_min = 2
        self.agua_max = 4
        self.parque_min = 3
        self.parque_max = 6
        
        # Parámetros de vuelo de mosquitos
        self.rango_vuelo_max = 10  # ~350m si celda=35m
        
        # Parámetros de comportamiento humano
        self.prob_aislamiento = 0.7  # 70% se aíslan
        self.radio_mov_infectado = 1  # 1 celda de radio
    
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
        
        # 2. Aplicar estrategias de control
        self._aplicar_control()
        
        # 3. Activar todos los agentes (actualiza estados, movimiento, interacciones)
        self.agents.shuffle().do("step")
        
        # 4. Recolectar datos
        self.datacollector.collect(self)
    
    def _actualizar_clima(self):
        """
        Actualiza temperatura y precipitación diarias.
        
        Opciones:
        1. Datos reales: API de Meteostat (requiere conexión)
        2. Fallback: Modelo sintético basado en promedios de Bucaramanga
        
        Bucaramanga:
        - Temperatura promedio: 22-24°C
        - Precipitación: variable según época (seca vs lluviosa)
        """
        try:
            # Intentar obtener datos reales de Meteostat
            temp, precip = self._obtener_clima_meteostat()
            self.temperatura_actual = temp
            self.precipitacion_actual = precip
        except Exception:
            # Fallback: modelo sintético
            self.temperatura_actual = self._generar_temperatura_sintetica()
            self.precipitacion_actual = self._generar_precipitacion_sintetica()
    
    def _obtener_clima_meteostat(self) -> Tuple[float, float]:
        """
        Obtiene datos climáticos reales vía Meteostat API.
        
        Bucaramanga: lat=7.1254, lon=-73.1198
        
        Returns
        -------
        Tuple[float, float]
            (temperatura en °C, precipitación en mm)
            
        Raises
        ------
        Exception
            Si falla la conexión o no hay datos
        """
        # TODO: Implementar conexión real con Meteostat
        # Por ahora lanzar excepción para usar modelo sintético
        raise Exception("Meteostat no implementado aún")
    
    def _generar_temperatura_sintetica(self) -> float:
        """
        Genera temperatura sintética para Bucaramanga.
        
        Modelo simple:
        - Base: 23°C
        - Variación diaria: ±3°C
        - Ruido: ±1°C
        
        Returns
        -------
        float
            Temperatura en °C
        """
        # Variación estacional (simplificada: sinusoidal anual)
        dia_anio = self.dia_simulacion % 365
        variacion_estacional = 2 * np.sin(2 * np.pi * dia_anio / 365)
        
        # Ruido aleatorio
        ruido = self.random.gauss(0, 1)
        
        # Temperatura final
        temp = 23.0 + variacion_estacional + ruido
        return max(15, min(35, temp))  # Limitar a rango realista
    
    def _generar_precipitacion_sintetica(self) -> float:
        """
        Genera precipitación sintética para Bucaramanga.
        
        Modelo simple:
        - Probabilidad de lluvia: 0.3
        - Cantidad si llueve: 5-50mm
        
        Returns
        -------
        float
            Precipitación en mm
        """
        if self.random.random() < 0.3:  # 30% probabilidad de lluvia
            return self.random.uniform(5, 50)
        return 0.0
    
    def _aplicar_control(self):
        """
        Aplica estrategias de control según configuración.
        
        LSM (Larval Source Management):
        - Frecuencia: cada 7 días
        - Cobertura: 70%
        - Efectividad: 80% reducción de larvas
        
        ITN/IRS (Insecticide-Treated Nets / Indoor Residual Spraying):
        - Duración: 90 días por aplicación
        - Cobertura: 60% hogares
        - Efectividad: 70% reducción de picaduras
        """
        # LSM: Aplicar cada 7 días
        if self.usar_lsm and self.dia_simulacion % 7 == 0:
            self._aplicar_lsm()
        
        # ITN/IRS: Activar según necesidad
        if self.usar_itn_irs:
            self._aplicar_itn_irs()
    
    def _aplicar_lsm(self):
        """
        Aplica control larvario (LSM).
        
        Elimina huevos en sitios de cría con cobertura 70% y efectividad 80%.
        """
        self.lsm_activo = True
        
        # Obtener todos los huevos
        huevos = [a for a in self.agents 
                 if isinstance(a, MosquitoAgent) and a.etapa == EtapaVida.HUEVO]
        
        # Aplicar reducción: 70% cobertura × 80% efectividad = 56% reducción
        reduccion = 0.56
        for huevo in huevos:
            if self.random.random() < reduccion:
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
        prop_agua = getattr(self, 'proporcion_celdas_agua', 0.05)
        prop_parques = getattr(self, 'proporcion_celdas_parques', 0.10)
        
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
        Crea zonas contiguas (clusters) de un tipo específico.
        
        Algoritmo:
        1. Elegir centro aleatorio disponible
        2. Expandir en forma de cuadrado/rectángulo
        3. Repetir hasta alcanzar num_celdas_objetivo
        
        Parameters
        ----------
        mapa : Dict[Tuple[int, int], Celda]
            Mapa de celdas a modificar
        tipo : TipoCelda
            Tipo de celda a crear (AGUA o PARQUE)
        num_celdas_objetivo : int
            Número total de celdas a asignar a este tipo
        celdas_ocupadas : set
            Set de posiciones ya ocupadas por otros tipos
        """
        from .celda import Celda
        
        celdas_asignadas = 0
        
        # Tamaño de zonas según tipo (desde configuración)
        if tipo.value == "agua":
            tamaño_min = getattr(self, 'agua_min', 2)
            tamaño_max = getattr(self, 'agua_max', 4)
        else:  # parques
            tamaño_min = getattr(self, 'parque_min', 3)
            tamaño_max = getattr(self, 'parque_max', 6)
        
        intentos = 0
        max_intentos = 1000
        
        while celdas_asignadas < num_celdas_objetivo and intentos < max_intentos:
            intentos += 1
            
            # Elegir centro aleatorio
            centro_x = self.random.randint(1, self.width - tamaño_max - 1)
            centro_y = self.random.randint(1, self.height - tamaño_max - 1)
            
            # Verificar si centro está disponible
            if (centro_x, centro_y) in celdas_ocupadas:
                continue
            
            # Determinar tamaño de esta zona
            ancho = self.random.randint(tamaño_min, tamaño_max)
            alto = self.random.randint(tamaño_min, tamaño_max)
            
            # Verificar si toda la zona está disponible
            zona_disponible = True
            celdas_zona = []
            
            for dx in range(ancho):
                for dy in range(alto):
                    x = centro_x + dx
                    y = centro_y + dy
                    
                    if x >= self.width or y >= self.height:
                        zona_disponible = False
                        break
                    
                    if (x, y) in celdas_ocupadas:
                        zona_disponible = False
                        break
                    
                    celdas_zona.append((x, y))
                
                if not zona_disponible:
                    break
            
            # Si la zona está disponible, asignarla
            if zona_disponible and celdas_zona:
                for pos in celdas_zona:
                    mapa[pos] = Celda(tipo, pos)
                    celdas_ocupadas.add(pos)
                    celdas_asignadas += 1
                    
                    if celdas_asignadas >= num_celdas_objetivo:
                        break
    
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
    
    def _crear_humanos(self, num_humanos: int, infectados_iniciales: int):
        """
        Crea la población inicial de humanos.
        
        Distribución desde configuración (por defecto):
        - 25% Estudiantes (Tipo 1)
        - 35% Trabajadores (Tipo 2)
        - 25% Móviles continuos (Tipo 3)
        - 15% Estacionarios (Tipo 4)
        
        Parameters
        ----------
        num_humanos : int
            Número total de humanos
        infectados_iniciales : int
            Número de humanos infectados al inicio
        """
        # Usar distribución desde configuración
        tipos_dist = [
            (TipoMovilidad.ESTUDIANTE, self.dist_estudiantes),
            (TipoMovilidad.TRABAJADOR, self.dist_trabajadores),
            (TipoMovilidad.MOVIL_CONTINUO, self.dist_moviles),
            (TipoMovilidad.ESTACIONARIO, self.dist_estacionarios)
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
            
            # Posiciones aleatorias
            pos_hogar = (self.random.randrange(self.width), 
                        self.random.randrange(self.height))
            
            # Destino según tipo
            pos_destino = None
            if tipo in [TipoMovilidad.ESTUDIANTE, TipoMovilidad.TRABAJADOR]:
                pos_destino = (self.random.randrange(self.width),
                             self.random.randrange(self.height))
            
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
        
        Distribución:
        - 50% hembras, 50% machos (Pf = 0.5)
        
        Parameters
        ----------
        num_mosquitos : int
            Número total de mosquitos adultos
        infectados_iniciales : int
            Número de mosquitos infectados al inicio
        """
        infectados_asignados = 0
        
        for i in range(num_mosquitos):
            # Determinar sexo: Pf = 0.5
            es_hembra = self.random.random() < 0.5
            
            # Posición aleatoria
            pos = (self.random.randrange(self.width),
                  self.random.randrange(self.height))
            
            # Crear agente
            unique_id = self.next_id()
            mosquito = MosquitoAgent(
                unique_id=unique_id,
                model=self,
                etapa=EtapaVida.ADULTO,
                es_hembra=es_hembra
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
        Crea la población inicial de huevos.
        
        Los huevos se colocan en sitios de cría aleatorios.
        
        Parameters
        ----------
        num_huevos : int
            Número total de huevos
        """
        for i in range(num_huevos):
            # Determinar sexo futuro: Pf = 0.5
            es_hembra = self.random.random() < 0.5
            
            # Sitio de cría aleatorio
            if self.sitios_cria:
                sitio = self.random.choice(self.sitios_cria)
            else:
                sitio = (self.random.randrange(self.width),
                        self.random.randrange(self.height))
            
            # Crear huevo
            unique_id = self.next_id()
            huevo = MosquitoAgent(
                unique_id=unique_id,
                model=self,
                etapa=EtapaVida.HUEVO,
                es_hembra=es_hembra,
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
