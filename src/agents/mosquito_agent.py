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
from typing import Tuple, Optional, List


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
        
        # Parámetros desde configuración del modelo (con valores por defecto)
        self.tasa_mortalidad = getattr(model, 'mortalidad_mosquito', 0.05)  # Mr = 0.05 por día
        self.rango_sensorial = getattr(model, 'rango_sensorial_mosquito', 3)  # Sr = 3 celdas
        self.prob_apareamiento = getattr(model, 'prob_apareamiento_mosquito', 0.6)  # Pm = 0.6
        self.huevos_por_hembra = getattr(model, 'huevos_por_hembra', 100)  # 100 huevos por puesta
    
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
        
        Por defecto: μ = 8 + |θ - 25| * 1.0 días
        
        Donde θ es la temperatura diaria del modelo.
        """
        self.dias_como_huevo += 1
        
        # Obtener temperatura actual del modelo
        temperatura = self.model.temperatura_actual if hasattr(self.model, 'temperatura_actual') else 25
        
        # Obtener parámetros de desarrollo desde el modelo
        base_dias = getattr(self.model, 'dias_base_desarrollo_huevo', 8)
        temp_optima = getattr(self.model, 'temp_optima_desarrollo_huevo', 25.0)
        sensibilidad = getattr(self.model, 'sensibilidad_temp_desarrollo_huevo', 1.0)
        
        # Calcular días necesarios para eclosión
        dias_desarrollo = base_dias + abs(temperatura - temp_optima) * sensibilidad
        
        # Eclosionar si se cumplió el tiempo
        if self.dias_como_huevo >= dias_desarrollo:
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
        
        # 1. Mortalidad diaria (usar parámetro del modelo)
        if self.random.random() < self.tasa_mortalidad:
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
        - Si detecta humano dentro del rango sensorial (Sr = 3): moverse hacia él
        - Si no: caminata aleatoria (Moore neighborhood)
        """
        # Verificar que el mosquito tenga posición (huevos no tienen posición)
        if self.pos is None:
            return
        
        # Buscar humanos cercanos
        humano_cercano = self.buscar_humano_cercano()
        
        if humano_cercano:
            # Moverse hacia el humano detectado
            self.mover_hacia(humano_cercano.pos)
        else:
            # Caminata aleatoria
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
        
        # Filtrar solo humanos
        humanos = [agente for agente in vecinos if agente.__class__.__name__ == 'HumanAgent']
        
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
        humanos = [a for a in agentes_celda if a.__class__.__name__ == 'HumanAgent']
        
        if not humanos:
            return
        
        # Elegir un humano aleatoriamente
        humano = self.random.choice(humanos)
        self.ha_picado_hoy = True
        
        # Obtener probabilidades de transmisión desde el modelo
        alpha = getattr(self.model, 'prob_transmision_mosquito_humano', 0.6)  # α
        beta = getattr(self.model, 'prob_transmision_humano_mosquito', 0.275)  # β
        
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
                    if a.__class__.__name__ == 'MosquitoAgent' 
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
        
        Resultado: huevos_por_hembra (según configuración, por defecto 100)
        Sexo: determinado por female_ratio (por defecto Pf = 0.5)
        """
        # Verificar precipitación (necesaria para sitios de cría activos)
        precipitacion = self.model.precipitacion_actual if hasattr(self.model, 'precipitacion_actual') else 0
        umbral_lluvia = getattr(self.model, 'umbral_precipitacion_cria', 0.0)
        
        if precipitacion < umbral_lluvia:
            return
        
        # Buscar sitio de cría cercano
        sitio = self._buscar_sitio_cria()
        if not sitio:
            return
        
        # Obtener parámetros desde el modelo
        prob_hembra = getattr(self.model, 'proporcion_hembras', 0.5)  # Pf = 0.5
        
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
        # Nota: hembra puede volver a reproducir en próximo ciclo
    
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
        base_dias = getattr(self.model, 'dias_base_maduracion_huevo', 3)
        temp_optima = getattr(self.model, 'temp_optima_maduracion_huevo', 21.0)
        sensibilidad = getattr(self.model, 'sensibilidad_temp_maduracion_huevo', 5.0)
        
        return int(base_dias + abs(temperatura - temp_optima) / sensibilidad)
    
    def _buscar_sitio_cria(self) -> Optional[Tuple[int, int]]:
        """
        Busca sitio de cría activo cercano (celdas tipo AGUA).
        
        Busca dentro del rango máximo de vuelo del mosquito (Fr).
        
        Returns
        -------
        Optional[Tuple[int, int]]
            Coordenadas del sitio de cría más cercano o None
        """
        from ..model.celda import TipoCelda
        
        # Sitios permanentes (celdas tipo AGUA)
        sitios_agua = [pos for pos, celda in self.model.mapa_celdas.items()
                       if celda.tipo == TipoCelda.AGUA]
        
        # Sitios temporales (charcos post-lluvia) - si existen
        sitios_temp = []
        if hasattr(self.model, 'sitios_cria_temporales'):
            sitios_temp = list(self.model.sitios_cria_temporales.keys())
        
        # Combinar todos los sitios disponibles
        sitios_disponibles = sitios_agua + sitios_temp
        
        if not sitios_disponibles:
            return None
        
        # Filtrar por rango de vuelo máximo (Fr = ~350m)
        rango_max = getattr(self.model, 'rango_vuelo_max', 10)  # 10 celdas por defecto
        sitios_alcanzables = [s for s in sitios_disponibles 
                              if self._distancia(s) <= rango_max]
        
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
