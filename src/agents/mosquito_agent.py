"""
Agente Mosquito para el modelo ABM del Dengue.

Este módulo implementa el agente mosquito con estados SI, reproducción
dependiente de temperatura y comportamiento de búsqueda de humanos.

Basado en Jindal & Rao (2017) con parámetros adaptados a Bucaramanga.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

from mesa import Agent
import numpy as np
from enum import Enum
from typing import Tuple, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .human_agent import HumanAgent


class EstadoMosquito(Enum):
    """Estados epidemiológicos del modelo SI (sin recuperación)."""
    SUSCEPTIBLE = "S"
    INFECTADO = "I"


class EtapaVida(Enum):
    """Etapas del ciclo de vida del mosquito."""
    HUEVO = "egg"           # Huevo en sitio de cría
    ADULTO = "adult"        # Mosquito adulto


class MosquitoAgent(Agent):
    """
    Agente mosquito con estados SI y reproducción dependiente de temperatura.
    
    Representa un mosquito Aedes aegypti en la simulación con:
    - Estados epidemiológicos: S (Susceptible), I (Infectado)
    - Ciclo de vida: huevo → adulto
    - Movimiento: caminata aleatoria con sensado de humanos
    - Reproducción: dependiente de temperatura, precipitación y apareamiento
    
    Parameters
    ----------
    unique_id : int
        Identificador único del agente
    model : Model
        Modelo al que pertenece el agente
    etapa : EtapaVida
        Etapa inicial (HUEVO o ADULTO)
    es_hembra : bool, default=True
        Si es mosquito hembra (solo hembras pican y ponen huevos)
    sitio_cria : Optional[Tuple[int, int]], default=None
        Posición del sitio de cría (para huevos)
        
    Attributes
    ----------
    estado : EstadoMosquito
        Estado epidemiológico (S o I)
    etapa : EtapaVida
        Etapa de vida actual
    es_hembra : bool
        Indicador de sexo (True = hembra, False = macho)
    dias_como_huevo : int
        Días transcurridos en etapa de huevo
    edad : int
        Edad en días desde que emergió como adulto
    ha_picado_hoy : bool
        Indica si ya picó un humano en el día actual
    esta_apareado : bool
        Indica si la hembra está apareada (necesario para reproducción)
    sitio_cria : Optional[Tuple[int, int]]
        Ubicación del sitio de cría (para huevos)
    rango_sensorial : int
        Distancia en celdas para detectar humanos (Sr = 3)
    """
    
    def __init__(
        self,
        unique_id: int,
        model,
        etapa: EtapaVida = EtapaVida.ADULTO,
        es_hembra: bool = True,
        sitio_cria: Optional[Tuple[int, int]] = None
    ):
        super().__init__(unique_id, model)
        
        # Estado epidemiológico
        self.estado = EstadoMosquito.SUSCEPTIBLE
        
        # Ciclo de vida
        self.etapa = etapa
        self.es_hembra = es_hembra
        self.dias_como_huevo = 0
        self.edad = 0
        
        # Comportamiento
        self.ha_picado_hoy = False
        self.esta_apareado = False if es_hembra else True  # Machos siempre "listos"
        self.sitio_cria = sitio_cria
        self.dias_desde_ultima_puesta = 0  # Control de cooldown de reproducción
        self.dias_cooldown_reproduccion = 3  # Mínimo 3 días entre puestas (ciclo gonotrófico)
        
        # Parámetros desde configuración del modelo (cacheados para rendimiento)
        self.tasa_mortalidad = model.mortalidad_mosquito
        self.rango_sensorial = model.rango_sensorial_mosquito
        self.prob_apareamiento = model.prob_apareamiento_mosquito
        self.huevos_por_hembra = model.huevos_por_hembra
        
        # Parámetros de desarrollo de huevos (cacheados)
        self.dias_base_desarrollo_huevo = model.dias_base_desarrollo_huevo
        self.temp_optima_desarrollo_huevo = model.temp_optima_desarrollo_huevo
        self.sensibilidad_temp_desarrollo_huevo = model.sensibilidad_temp_desarrollo_huevo
        
        # Parámetros de transmisión (cacheados)
        self.prob_transmision_mosquito_humano = model.prob_transmision_mosquito_humano  # α
        self.prob_transmision_humano_mosquito = model.prob_transmision_humano_mosquito  # β
        
        # Parámetros de reproducción (cacheados)
        self.umbral_precipitacion_cria = model.umbral_precipitacion_cria
        self.proporcion_hembras = model.proporcion_hembras
        self.dias_base_maduracion_huevo = model.dias_base_maduracion_huevo
        self.temp_optima_maduracion_huevo = model.temp_optima_maduracion_huevo
        self.sensibilidad_temp_maduracion_huevo = model.sensibilidad_temp_maduracion_huevo
        
        # Parámetros de movimiento (cacheados)
        self.rango_vuelo_max = model.rango_vuelo_max
    
    def step(self):
        """
        Ejecuta un paso de simulación diario.
        
        Secuencia según etapa:
        - HUEVO: Verificar si eclosiona (depende de temperatura)
        - ADULTO: Moverse, buscar humanos (hembras), aparearse, reproducir
        """
        if self.etapa == EtapaVida.HUEVO:
            self.procesar_desarrollo_huevo()
        else:  # ADULTO
            self.procesar_comportamiento_adulto()
    
    def procesar_desarrollo_huevo(self):
        """
        Procesa el desarrollo del huevo hasta eclosión.
        
        Fórmula de duración dependiente de temperatura:
        μ = base_dias + |θ - temp_optima| * sensibilidad
        
        Donde:
        - θ: temperatura actual (°C)
        - base_dias: 8 días a temperatura óptima
        - temp_optima: 25°C para Aedes aegypti
        - sensibilidad: 1.0 día por cada grado de desviación
        """
        temperatura = self.model.temperatura_actual
        duracion_dias = self.dias_base_desarrollo_huevo + abs(temperatura - self.temp_optima_desarrollo_huevo) * self.sensibilidad_temp_desarrollo_huevo
        
        # Incrementar días como huevo
        self.dias_como_huevo += 1
        
        # Verificar si debe eclosionar
        if self.dias_como_huevo >= duracion_dias:
            self.eclosionar()
    
    def eclosionar(self):
        """
        Transición de HUEVO a ADULTO.
        
        El mosquito emerge como adulto y se coloca en el sitio de cría.
        """
        self.etapa = EtapaVida.ADULTO
        self.dias_como_huevo = 0
        self.edad = 0
        
        # Colocar en el sitio de cría
        if self.sitio_cria and not self.pos:
            self.model.grid.place_agent(self, self.sitio_cria)
    
    def procesar_comportamiento_adulto(self):
        """
        Ejecuta el comportamiento del mosquito adulto.
        
        Secuencia diaria:
        1. Verificar mortalidad
        2. Moverse (caminata aleatoria o dirigida a humano)
        3. Intentar picar (solo hembras)
        4. Aparearse si encuentra pareja
        5. Reproducir si está apareada y hay sitio de cría
        """
        self.edad += 1
        self.ha_picado_hoy = False
        
        # Incrementar cooldown de reproducción
        if self.dias_desde_ultima_puesta < self.dias_cooldown_reproduccion:
            self.dias_desde_ultima_puesta += 1
        
        # 1. Mortalidad diaria (usar parámetro del modelo)
        if self.random.random() < self.tasa_mortalidad:
            # Solo remover del grid si tiene posición
            if self.pos is not None:
                self.model.grid.remove_agent(self)
            self.model.agents.remove(self)
            return
        
        # 2. Movimiento
        self.mover()
        
        # 3. Picar humano (solo hembras)
        if self.es_hembra:
            self.intentar_picar()
        
        # 4. Apareamiento
        if self.es_hembra and not self.esta_apareado:
            self.intentar_apareamiento()
        
        # 5. Reproducción (solo hembras apareadas)
        if self.es_hembra and self.esta_apareado and self.ha_picado_hoy:
            self.intentar_reproduccion()
    
    def mover(self):
        """
        Movimiento del mosquito: caminata aleatoria o dirigida.
        
        Lógica:
        - Solo hembras buscan humanos (machos no pican, no necesitan buscarlos)
        - Si hembra detecta humano dentro del rango sensorial (Sr = 3): moverse hacia él
        - Si no: caminata aleatoria (Moore neighborhood)
        """
        # Verificar que el mosquito tenga posición (huevos no tienen posición)
        if self.pos is None:
            return
        
        # Solo hembras buscan humanos activamente (OPTIMIZACIÓN: machos no pican)
        if self.es_hembra:
            humano_cercano = self.buscar_humano_cercano()
            if humano_cercano:
                # Moverse hacia el humano detectado
                self.mover_hacia(humano_cercano.pos)
                return
        
        # Caminata aleatoria (machos siempre, hembras si no detectan humano)
        self.mover_aleatorio()
    
    def mover_aleatorio(self):
        """Movimiento aleatorio a una celda vecina (Moore neighborhood)."""
        vecindad = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )
        nueva_pos = self.random.choice(vecindad)
        self.model.grid.move_agent(self, nueva_pos)
    
    def mover_hacia(self, destino: Tuple[int, int]):
        """
        Mueve el mosquito un paso hacia la posición destino.
        
        Parameters
        ----------
        destino : Tuple[int, int]
            Coordenadas (x, y) del objetivo
        """
        x_actual, y_actual = self.pos
        x_dest, y_dest = destino
        
        # Calcular dirección (un paso)
        dx = np.sign(x_dest - x_actual)
        dy = np.sign(y_dest - y_actual)
        
        # Nueva posición (máximo un paso)
        nueva_x = x_actual + dx
        nueva_y = y_actual + dy
        
        # Asegurar límites del grid
        nueva_x = max(0, min(nueva_x, self.model.grid.width - 1))
        nueva_y = max(0, min(nueva_y, self.model.grid.height - 1))
        
        self.model.grid.move_agent(self, (nueva_x, nueva_y))
    
    def buscar_humano_cercano(self) -> Optional['HumanAgent']:
        """
        Busca humanos dentro del rango sensorial.
        
        Returns
        -------
        Optional[HumanAgent]
            El humano más cercano si existe, None en caso contrario
        """
        # Verificar que el mosquito tenga posición
        if self.pos is None:
            return None
        
        # Obtener vecinos dentro del rango sensorial
        vecinos = self.model.grid.get_neighbors(
            self.pos,
            moore=True,
            include_center=False,
            radius=self.rango_sensorial
        )
        
        # Filtrar solo humanos (isinstance es más rápido que __class__.__name__)
        from .human_agent import HumanAgent
        humanos = [agente for agente in vecinos if isinstance(agente, HumanAgent)]
        
        if humanos:
            # Retornar el más cercano
            return min(humanos, key=lambda h: self._distancia(h.pos))
        return None
    
    def intentar_picar(self):
        """
        Intenta picar a un humano en la misma celda.
        
        Solo hembras pican. Puede resultar en:
        - Transmisión mosquito → humano (si mosquito infectado, humano susceptible)
        - Transmisión humano → mosquito (si mosquito susceptible, humano infectado)
        
        Probabilidades desde configuración del modelo:
        - α (mosquito → humano): mosquito_to_human_prob
        - β (humano → mosquito): human_to_mosquito_prob
        """
        if self.ha_picado_hoy:
            return
        
        # Verificar que el mosquito tenga posición
        if self.pos is None:
            return
        
        # Obtener agentes en la misma celda
        agentes_celda = self.model.grid.get_cell_list_contents([self.pos])
        from .human_agent import HumanAgent
        humanos = [a for a in agentes_celda if isinstance(a, HumanAgent)]
        
        if not humanos:
            return
        
        # Elegir un humano aleatoriamente
        humano = self.random.choice(humanos)
        self.ha_picado_hoy = True
        
        # Usar probabilidades de transmisión cacheadas
        alpha = self.prob_transmision_mosquito_humano  # α
        beta = self.prob_transmision_humano_mosquito  # β
        
        # Transmisión mosquito → humano (α)
        if self.estado == EstadoMosquito.INFECTADO and humano.es_susceptible():
            if self.random.random() < alpha:
                humano.get_exposed()
        
        # Transmisión humano → mosquito (β)
        elif self.estado == EstadoMosquito.SUSCEPTIBLE and humano.es_infeccioso():
            if self.random.random() < beta:
                self.estado = EstadoMosquito.INFECTADO
    
    def intentar_apareamiento(self):
        """
        Intenta aparearse con un macho en la misma celda.
        
        Probabilidad de éxito desde configuración: prob_apareamiento_mosquito
        Solo hembras no apareadas pueden aparearse.
        """
        # Verificar que el mosquito tenga posición
        if self.pos is None:
            return
        
        # Obtener mosquitos en la misma celda
        agentes_celda = self.model.grid.get_cell_list_contents([self.pos])
        mosquitos = [a for a in agentes_celda 
                    if isinstance(a, MosquitoAgent)
                    and a.etapa == EtapaVida.ADULTO 
                    and not a.es_hembra]
        
        if mosquitos and self.random.random() < self.prob_apareamiento:
            self.esta_apareado = True
    
    def intentar_reproduccion(self):
        """
        Intenta poner huevos en un sitio de cría cercano.
        
        Requisitos:
        - Ser hembra apareada
        - Haber picado (ingesta de sangre)
        - Encontrar sitio de cría activo
        - Condiciones climáticas favorables (precipitación >= umbral)
        - Haber pasado el período de cooldown (ciclo gonotrófico ~3 días)
        
        Resultado: huevos_por_hembra (según configuración, por defecto 100)
        Sexo: determinado por female_ratio (por defecto Pf = 0.5)
        """
        # Verificar cooldown (ciclo gonotrófico: tiempo entre puestas)
        if self.dias_desde_ultima_puesta < self.dias_cooldown_reproduccion:
            return
        
        # Verificar precipitación (necesaria para sitios de cría activos)
        precipitacion = self.model.precipitacion_actual if hasattr(self.model, 'precipitacion_actual') else 0
        
        if precipitacion < self.umbral_precipitacion_cria:
            return
        
        # Buscar sitio de cría cercano
        sitio = self._buscar_sitio_cria()
        if not sitio:
            return
        
        # Poner huevos con proporción de hembras cacheada
        prob_hembra = self.proporcion_hembras  # Pf = 0.5
        
        # Poner huevos
        for _ in range(self.huevos_por_hembra):
            # Determinar sexo según proporción de hembras
            es_hembra = self.random.random() < prob_hembra
            
            # Crear huevo
            unique_id = self.model.next_id()
            huevo = MosquitoAgent(
                unique_id=unique_id,
                model=self.model,
                etapa=EtapaVida.HUEVO,
                es_hembra=es_hembra,
                sitio_cria=sitio
            )
            
            # No agregar al grid (huevos no ocupan espacio hasta eclosionar)
            self.model.agents.add(huevo)
        
        # Resetear estado reproductivo
        self.ha_picado_hoy = False
        self.dias_desde_ultima_puesta = 0  # Reiniciar cooldown
        # Nota: hembra puede volver a reproducir después del cooldown
    
    def _calcular_dias_maduracion(self, temperatura: float) -> int:
        """
        Calcula días de maduración del huevo según temperatura.
        
        Fórmula desde configuración:
        τ = base_dias + |θ - temp_optima| / sensibilidad
        
        Por defecto: τ = 3 + |θ - 21| / 5
        
        Parameters
        ----------
        temperatura : float
            Temperatura en grados Celsius
            
        Returns
        -------
        int
            Días necesarios para maduración
        """
        return int(self.dias_base_maduracion_huevo + abs(temperatura - self.temp_optima_maduracion_huevo) / self.sensibilidad_temp_maduracion_huevo)
    
    def _buscar_sitio_cria(self) -> Optional[Tuple[int, int]]:
        """
        Busca sitio de cría activo cercano (celdas tipo AGUA).
        
        Busca dentro del rango máximo de vuelo del mosquito (Fr).
        
        Returns
        -------
        Optional[Tuple[int, int]]
            Coordenadas del sitio de cría más cercano o None
        """
        # Usar la lista de sitios permanentes cacheada en el modelo (OPTIMIZACIÓN)
        sitios_agua = self.model.sitios_cria
        
        # Sitios temporales (charcos post-lluvia) - si existen
        sitios_temp = []
        if hasattr(self.model, 'sitios_cria_temporales'):
            sitios_temp = list(self.model.sitios_cria_temporales.keys())
        
        # Combinar todos los sitios disponibles
        sitios_disponibles = sitios_agua + sitios_temp
        
        if not sitios_disponibles:
            return None
        
        # Filtrar por rango de vuelo máximo cacheado (Fr = ~350m)
        sitios_alcanzables = [s for s in sitios_disponibles 
                              if self._distancia(s) <= self.rango_vuelo_max]
        
        if not sitios_alcanzables:
            # Si ninguno alcanzable, retornar el más cercano aunque esté lejos
            return min(sitios_disponibles, key=lambda s: self._distancia(s))
        
        # Retornar el más cercano dentro del rango
        return min(sitios_alcanzables, key=lambda s: self._distancia(s))
    
    def _distancia(self, pos: Tuple[int, int]) -> float:
        """
        Calcula distancia euclidiana a una posición.
        
        Parameters
        ----------
        pos : Tuple[int, int]
            Posición destino
            
        Returns
        -------
        float
            Distancia euclidiana
        """
        x1, y1 = self.pos
        x2, y2 = pos
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def __repr__(self) -> str:
        """Representación en cadena del agente."""
        return (f"MosquitoAgent(id={self.unique_id}, estado={self.estado.value}, "
                f"etapa={self.etapa.value}, sexo={'F' if self.es_hembra else 'M'}, "
                f"pos={self.pos})")
