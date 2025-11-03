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
        
        # Métricas
        self.num_picaduras = 0
        
        # Parámetros del modelo SEIR (días) - desde configuración del modelo
        self.duracion_expuesto = getattr(model, 'incubacion_humano', 5)  # Ne = 5 días (por defecto)
        self.duracion_infectado = getattr(model, 'infeccioso_humano', 6)  # Ni = 6 días (por defecto)
        
        # Probabilidades de visita a parque según tipo - desde configuración del modelo
        park_probs = {
            TipoMovilidad.ESTUDIANTE: getattr(model, 'prob_parque_estudiante', 0.3),
            TipoMovilidad.TRABAJADOR: getattr(model, 'prob_parque_trabajador', 0.1),
            TipoMovilidad.MOVIL_CONTINUO: getattr(model, 'prob_parque_movil', 0.15),
            TipoMovilidad.ESTACIONARIO: getattr(model, 'prob_parque_estacionario', 0.05)
        }
        self.prob_parque = park_probs.get(tipo_movilidad, 0.1)
    
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
            if self.dias_en_estado >= self.duracion_expuesto:
                self.estado = EstadoSalud.INFECTADO
                self.dias_en_estado = 0
                
        elif self.estado == EstadoSalud.INFECTADO:
            if self.dias_en_estado >= self.duracion_infectado:
                self.estado = EstadoSalud.RECUPERADO
                self.dias_en_estado = 0
    
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
        Determina y ejecuta el movimiento diario según tipo y hora.
        
        Reglas de movilidad:
        - Tipo 1 (Estudiante): Hogar → Escuela (7AM-3PM) → Hogar (+parque opcional)
        - Tipo 2 (Trabajador): Hogar → Oficina (7AM-variable) → Hogar (+parque opcional)
        - Tipo 3 (Móvil continuo): Cambia ubicación cada 2 horas
        - Tipo 4 (Estacionario): Permanece en hogar
        
        NOTA: Los infectados (estado I) permanecen en casa.
        """
        # Los infectados no se mueven (permanecen en casa)
        if self.estado == EstadoSalud.INFECTADO:
            self.mover_a(self.pos_hogar)
            return
        
        # Obtener hora simulada (simplificado: usar paso del modelo)
        hora_del_dia = self.model.schedule.steps % 24 if hasattr(self.model, 'schedule') else 12
        
        if self.tipo == TipoMovilidad.ESTUDIANTE:
            self._movilidad_estudiante(hora_del_dia)
            
        elif self.tipo == TipoMovilidad.TRABAJADOR:
            self._movilidad_trabajador(hora_del_dia)
            
        elif self.tipo == TipoMovilidad.MOVIL_CONTINUO:
            self._movilidad_movil_continuo(hora_del_dia)
            
        elif self.tipo == TipoMovilidad.ESTACIONARIO:
            self.mover_a(self.pos_hogar)
    
    def _movilidad_estudiante(self, hora: int):
        """Patrón de movilidad para estudiantes (Tipo 1)."""
        # Obtener horarios desde configuración del modelo
        hora_inicio_escuela = getattr(self.model, 'hora_inicio_escuela', 7)
        hora_fin_escuela = getattr(self.model, 'hora_fin_escuela', 15)
        hora_inicio_parque = getattr(self.model, 'hora_inicio_parque', 16)
        hora_fin_parque = getattr(self.model, 'hora_fin_parque', 19)
        
        if hora_inicio_escuela <= hora < hora_fin_escuela:  # En escuela
            if self.pos_destino:
                self.mover_a(self.pos_destino)
        elif hora_inicio_parque <= hora < hora_fin_parque:  # Posible visita a parque
            if self.random.random() < self.prob_parque:
                parque = self._obtener_parque_cercano()
                if parque:
                    self.mover_a(parque)
            else:
                self.mover_a(self.pos_hogar)
        else:  # Resto del día: en hogar
            self.mover_a(self.pos_hogar)
    
    def _movilidad_trabajador(self, hora: int):
        """Patrón de movilidad para trabajadores (Tipo 2)."""
        # Obtener horarios desde configuración del modelo
        hora_inicio_trabajo = getattr(self.model, 'hora_inicio_trabajo', 7)
        hora_fin_trabajo = getattr(self.model, 'hora_fin_trabajo', 17)
        hora_inicio_parque = getattr(self.model, 'hora_inicio_parque', 17)
        hora_fin_parque = getattr(self.model, 'hora_fin_parque', 19)
        
        if hora_inicio_trabajo <= hora < hora_fin_trabajo:  # En oficina
            if self.pos_destino:
                self.mover_a(self.pos_destino)
        elif hora_inicio_parque <= hora < hora_fin_parque:  # Posible visita a parque
            if self.random.random() < self.prob_parque:
                parque = self._obtener_parque_cercano()
                if parque:
                    self.mover_a(parque)
            else:
                self.mover_a(self.pos_hogar)
        else:  # Resto del día: en hogar
            self.mover_a(self.pos_hogar)
    
    def _movilidad_movil_continuo(self, hora: int):
        """Patrón de movilidad para móviles continuos (Tipo 3)."""
        # Obtener parámetros desde configuración del modelo
        intervalo_movimiento = getattr(self.model, 'intervalo_movimiento_horas', 2)
        hora_inicio_activo = getattr(self.model, 'hora_inicio_movil_activo', 7)
        hora_fin_activo = getattr(self.model, 'hora_fin_movil_activo', 19)
        
        if hora_inicio_activo <= hora < hora_fin_activo:  # Horario activo
            # Cambiar ubicación según intervalo
            if hora % intervalo_movimiento == 0:
                nueva_pos = self._obtener_posicion_aleatoria()
                self.mover_a(nueva_pos)
        else:  # Resto del día: en hogar
            self.mover_a(self.pos_hogar)
    
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
            Coordenadas del parque o None si no hay parques
        """
        # TODO: Implementar búsqueda de celdas tipo "parque"
        # Por ahora retorna None (se implementará con el modelo completo)
        return None
    
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
