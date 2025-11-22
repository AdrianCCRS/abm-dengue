# -*- coding: utf-8 -*-
"""
Agente Humano para el modelo ABM del Dengue.

Este módulo implementa el agente humano con estados SEIR y comportamiento
de movilidad basado en Jindal & Rao (2017).

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

from mesa import Agent
import numpy as np
from enum import Enum
from typing import Tuple, Optional


class EstadoSalud(Enum):
    """Estados epidemiológicos del modelo SEIR."""
    SUSCEPTIBLE = "S"
    EXPUESTO = "E"
    INFECTADO = "I"
    RECUPERADO = "R"


class TipoMovilidad(Enum):
    """Tipos de movilidad según rutina diaria."""
    ESTUDIANTE = 1      # Hogar → Escuela → Hogar (+parque)
    TRABAJADOR = 2      # Hogar → Oficina → Hogar (+parque)
    MOVIL_CONTINUO = 3  # Movimiento constante cada 2 horas
    ESTACIONARIO = 4    # Permanece en hogar


class HumanAgent(Agent):
    """
    Agente humano con estados SEIR y movilidad diaria.
    
    Representa un individuo humano en la simulación con:
    - Estados epidemiológicos: S (Susceptible), E (Expuesto), I (Infectado), R (Recuperado)
    - Patrones de movilidad según tipo (estudiante, trabajador, móvil, estacionario)
    - Rutinas diarias hogar-trabajo-parque
    
    Parameters
    ----------
    unique_id : int
        Identificador único del agente
    model : Model
        Modelo al que pertenece el agente
    tipo_movilidad : TipoMovilidad
        Tipo de movilidad del agente
    pos_hogar : Tuple[int, int]
        Posición de la celda del hogar
    pos_destino : Optional[Tuple[int, int]], default=None
        Posición de escuela/oficina según tipo
        
    Attributes
    ----------
    estado : EstadoSalud
        Estado epidemiológico actual (S, E, I, R)
    dias_en_estado : int
        Días transcurridos en el estado actual
    tipo : TipoMovilidad
        Tipo de movilidad del agente
    pos_hogar : Tuple[int, int]
        Coordenadas del hogar
    pos_destino : Optional[Tuple[int, int]]
        Coordenadas de destino (escuela/oficina)
    pos_actual : Tuple[int, int]
        Posición actual en la cuadrícula
    num_picaduras : int
        Número de picaduras recibidas (para métricas)
    prob_aislamiento : float
        Probabilidad de aislamiento del agente,
    en_aislamiento : bool
        Indica si el agente está en aislamiento debido a infección
    """
    
    def __init__(
        self,
        unique_id: int,
        model,
        tipo_movilidad: TipoMovilidad,
        pos_hogar: Tuple[int, int],
        pos_destino: Optional[Tuple[int, int]] = None
    ):
        super().__init__(unique_id, model)
        
        # Estado epidemiológico
        self.estado = EstadoSalud.SUSCEPTIBLE
        self.dias_en_estado = 0
        
        # Movilidad
        self.tipo = tipo_movilidad
        self.pos_hogar = pos_hogar
        self.pos_destino = pos_destino  # Escuela/oficina
        self.pos_actual = pos_hogar
        self.prob_aislamiento = getattr(model, 'isolation_probability', 0.7)  # 70% por defecto
        self.en_aislamiento = False
        
        # Métricas
        self.num_picaduras = 0
        
        # Parámetros del modelo SEIR (cacheados para rendimiento)
        self.incubation_period = model.incubation_period  # Ne = 5 días
        self.infectious_period = model.infectious_period  # Ni = 6 días
        self.infected_mobility_radius = model.infected_mobility_radius  # Radio restringido cuando infectado
        
        # Probabilidades diarias de ubicación por tipo (cacheadas)
        if tipo_movilidad == TipoMovilidad.ESTUDIANTE:
            self.prob_home = model.student_prob_home
            self.prob_destination = model.student_prob_destination
            self.prob_park = model.student_prob_park
            self.prob_random = 0.0  # Estudiantes no tienen movimiento aleatorio
        elif tipo_movilidad == TipoMovilidad.TRABAJADOR:
            self.prob_home = model.worker_prob_home
            self.prob_destination = model.worker_prob_destination
            self.prob_park = model.worker_prob_park
            self.prob_random = 0.0  # Trabajadores no tienen movimiento aleatorio
        elif tipo_movilidad == TipoMovilidad.MOVIL_CONTINUO:
            self.prob_home = model.mobile_prob_home
            self.prob_destination = model.mobile_prob_destination
            self.prob_park = model.mobile_prob_park
            self.prob_random = model.mobile_prob_random
        else:  # ESTACIONARIO
            self.prob_home = model.stationary_prob_home
            self.prob_destination = model.stationary_prob_destination
            self.prob_park = model.stationary_prob_park
            self.prob_random = model.stationary_prob_random
    
    def step(self):
        """
        Ejecuta un paso de simulación diario.
        
        Secuencia:
        1. Actualizar estado epidemiológico (transiciones SEIR)
        2. Determinar movilidad según tipo y estado
        3. Mover a destino correspondiente
        """
        self.actualizar_estado_seir()
        self.ejecutar_movilidad_diaria()
    

    def actualizar_estado_seir(self):
        """
        Actualiza el estado epidemiológico según el modelo SEIR.
        
        Transiciones:
        - S → E: Al ser picado por mosquito infectado (manejado en interacción)
        - E → I: Después de duracion_expuesto días
        - I → R: Después de duracion_infectado días
        - R → S: Probabilidad Prc = 0 (inmunidad permanente en este modelo)
        """
        self.dias_en_estado += 1
        
        if self.estado == EstadoSalud.EXPUESTO:
            if self.dias_en_estado >= self.incubation_period:
                self.estado = EstadoSalud.INFECTADO
                self.dias_en_estado = 0
                
        elif self.estado == EstadoSalud.INFECTADO:
            if self.dias_en_estado >= self.infectious_period:
                self.estado = EstadoSalud.RECUPERADO
                self.dias_en_estado = 0
                # Resetear flag de aislamiento para futuras reinfecciones
                if hasattr(self, '_aislamiento_decidido'):
                    self._aislamiento_decidido = False
    
    def get_exposed(self):
        """
        Transición S → E al ser picado por mosquito infectado.
        
        Solo aplicable si el humano está en estado Susceptible.
        La probabilidad de transmisión α = 0.6 se maneja en la interacción.
        """
        if self.estado == EstadoSalud.SUSCEPTIBLE:
            self.estado = EstadoSalud.EXPUESTO
            self.dias_en_estado = 0
            self.num_picaduras += 1
    
    def es_infeccioso(self) -> bool:
        """
        Indica si el humano puede infectar a un mosquito.
        
        Returns
        -------
        bool
            True si está en estado Infectado (I), False en caso contrario
        """
        return self.estado == EstadoSalud.INFECTADO
    
    def es_susceptible(self) -> bool:
        """
        Indica si el humano puede ser infectado.
        
        Returns
        -------
        bool
            True si está en estado Susceptible (S), False en caso contrario
        """
        return self.estado == EstadoSalud.SUSCEPTIBLE
    
    def ejecutar_movilidad_diaria(self):
        """
        Determina y ejecuta el movimiento diario según probabilidades.
        
        Reglas de movilidad (basadas en probabilidades diarias):
        - Tipo 1 (Estudiante): 55% hogar, 35% escuela, 10% parque
        - Tipo 2 (Trabajador): 60% hogar, 35% oficina, 5% parque
        - Tipo 3 (Móvil continuo): 40% hogar, 20% parque, 40% aleatorio
        - Tipo 4 (Estacionario): 95% hogar, 5% parque
        
        NOTA: Los infectados (estado I) tienen comportamiento especial:
        - Con prob_aislamiento: permanecen en casa (aislamiento completo)
        - Sin aislamiento: movilidad reducida (radio limitado)
        """
        # OPTIMIZACIÓN: Skip para estacionarios que ya están en casa
        # Estacionarios tienen 95% prob de quedarse en casa, si ya están allí, skip
        if (self.tipo == TipoMovilidad.ESTACIONARIO and 
            self.pos == self.pos_hogar and 
            self.estado != EstadoSalud.INFECTADO):
            # 95% de probabilidad de quedarse, solo procesar el 5% restante
            if self.random.random() < 0.95:
                return  # Skip movimiento
        
        # Infectados: decisión de aislamiento
        if self.estado == EstadoSalud.INFECTADO:
            # Decidir aislamiento al momento de infectarse (una sola vez)
            if not hasattr(self, '_aislamiento_decidido'):
                self.en_aislamiento = (self.random.random() < self.prob_aislamiento)
                self._aislamiento_decidido = True
            
            if self.en_aislamiento:
                # Aislamiento completo: permanece en casa
                self.mover_a(self.pos_hogar)
                return
            else:
                # Sin aislamiento: retorna a casa + movilidad local reducida
                # Primero ir a casa (directo), luego movilidad local allí
                distancia_a_casa = self._distancia_manhattan(self.pos_hogar)
                
                if distancia_a_casa <= self.infected_mobility_radius:
                    # Ya está en casa o muy cerca: movilidad local reducida
                    vecindad = self.model.grid.get_neighborhood(
                        self.pos,  # Movilidad local desde posición actual
                        moore=True,
                        include_center=True,
                        radius=self.infected_mobility_radius
                    )
                    nueva_pos = self.random.choice(vecindad)
                    self.mover_a(nueva_pos)
                else:
                    # Está lejos de casa: ir directo a casa
                    self.mover_a(self.pos_hogar)
                return
        
        # Agentes no infectados: usar probabilidades diarias
        # Generar número aleatorio [0, 1)
        rand = self.random.random()
        
        # Acumular probabilidades para selección ponderada
        if rand < self.prob_home:
            # Ir a casa
            self.mover_a(self.pos_hogar)
        elif rand < self.prob_home + self.prob_destination:
            # Ir a destino (escuela/oficina) si existe
            if self.pos_destino:
                self.mover_a(self.pos_destino)
            else:
                self.mover_a(self.pos_hogar)  # Fallback a casa
        elif rand < self.prob_home + self.prob_destination + self.prob_park:
            # Ir a parque
            parque = self._obtener_parque_cercano()
            if parque:
                self.mover_a(parque)
            else:
                self.mover_a(self.pos_hogar)  # Fallback a casa si no hay parque
        else:
            # Movimiento aleatorio (solo para móviles continuos)
            if self.prob_random > 0:
                nueva_pos = self._obtener_posicion_aleatoria()
                self.mover_a(nueva_pos)
            else:
                self.mover_a(self.pos_hogar)  # Fallback a casa
    
    def mover_a(self, nueva_pos: Tuple[int, int]):
        """
        Mueve el agente a una nueva posición en el grid.
        
        Parameters
        ----------
        nueva_pos : Tuple[int, int]
            Coordenadas (x, y) de destino
        """
        if self.pos != nueva_pos:
            self.model.grid.move_agent(self, nueva_pos)
            self.pos_actual = nueva_pos
    
    def _obtener_parque_cercano(self) -> Optional[Tuple[int, int]]:
        """
        Busca el parque más cercano en el modelo.
        
        Returns
        -------
        Optional[Tuple[int, int]]
            Coordenadas del parque más cercano o None si no hay parques
        """
        # Usar la lista de parques cacheada en el modelo (ya accesible directamente)
        if not self.model.parques:
            return None
        
        # Retornar el más cercano a la posición actual
        return min(self.model.parques, key=lambda p: self._distancia_manhattan(p))
    
    def _distancia_manhattan(self, pos: Tuple[int, int]) -> int:
        """
        Calcula distancia Manhattan entre posición actual y destino.
        
        Parameters
        ----------
        pos : Tuple[int, int]
            Posición destino
            
        Returns
        -------
        int
            Distancia Manhattan (suma de diferencias absolutas)
        """
        x1, y1 = self.pos
        x2, y2 = pos
        return abs(x2 - x1) + abs(y2 - y1)
    
    def _obtener_posicion_aleatoria(self) -> Tuple[int, int]:
        """
        Obtiene una posición aleatoria válida en el grid.
        
        Returns
        -------
        Tuple[int, int]
            Coordenadas (x, y) aleatorias dentro del grid
        """
        x = self.random.randrange(self.model.grid.width)
        y = self.random.randrange(self.model.grid.height)
        return (x, y)
    
    def __repr__(self) -> str:
        """Representación en cadena del agente."""
        return (f"HumanAgent(id={self.unique_id}, estado={self.estado.value}, "
                f"tipo={self.tipo.name}, pos={self.pos})")
