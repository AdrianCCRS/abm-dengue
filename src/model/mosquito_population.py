# -*- coding: utf-8 -*-
"""
Grid de poblaciones de mosquitos para modelo metapoblacional.

Este módulo implementa un modelo metapoblacional donde los mosquitos
se representan como contadores de población por celda en lugar de
agentes individuales, reduciendo la complejidad computacional de
O(n_mosquitos) a O(n_celdas).

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

import numpy as np
from typing import TYPE_CHECKING, Tuple, List
from enum import Enum

if TYPE_CHECKING:
    from .dengue_model import DengueModel


class MosquitoState(Enum):
    """Estados epidemiológicos de mosquitos"""
    SUSCEPTIBLE = "S"
    EXPOSED = "E"
    INFECTIOUS = "I"


class MosquitoPopulationGrid:
    """
    Grid de poblaciones de mosquitos por celda.
    
    Implementa un modelo metapoblacional donde cada celda mantiene
    contadores de mosquitos por estado epidemiológico (S, E, I).
    
    Esta aproximación reduce drásticamente la complejidad computacional
    al procesar celdas en lugar de agentes individuales, manteniendo
    la dinámica epidemiológica espacial.
    
    Attributes
    ----------
    S_m : np.ndarray
        Mosquitos susceptibles por celda (width × height)
    E_m : np.ndarray
        Mosquitos expuestos por celda (incubando virus)
    I_m : np.ndarray
        Mosquitos infecciosos por celda (pueden transmitir)
    width : int
        Ancho del grid
    height : int
        Alto del grid
    
    References
    ----------
    Keeling, M. J., & Rohani, P. (2008). Modeling infectious diseases
    in humans and animals. Princeton University Press.
    """
    
    def __init__(self, width: int, height: int):
        """
        Inicializa el grid de poblaciones de mosquitos.
        
        Parameters
        ----------
        width : int
            Ancho del grid (número de celdas)
        height : int
            Alto del grid (número de celdas)
        """
        self.width = width
        self.height = height
        
        # Arrays numpy para eficiencia (dtype=int32 para poblaciones grandes)
        self.S_m = np.zeros((width, height), dtype=np.int32)
        self.E_m = np.zeros((width, height), dtype=np.int32)
        self.I_m = np.zeros((width, height), dtype=np.int32)
    
    def add_mosquitos(self, pos: Tuple[int, int], count: int, state: MosquitoState = MosquitoState.SUSCEPTIBLE):
        """
        Agrega mosquitos a una celda específica.
        
        Parameters
        ----------
        pos : Tuple[int, int]
            Coordenadas (x, y) de la celda
        count : int
            Número de mosquitos a agregar
        state : MosquitoState
            Estado epidemiológico de los mosquitos
        """
        if count <= 0:
            return
        
        x, y = pos
        
        if state == MosquitoState.SUSCEPTIBLE:
            self.S_m[x, y] += count
        elif state == MosquitoState.EXPOSED:
            self.E_m[x, y] += count
        elif state == MosquitoState.INFECTIOUS:
            self.I_m[x, y] += count
    
    def get_total(self, pos: Tuple[int, int]) -> int:
        """
        Obtiene el total de mosquitos en una celda.
        
        Parameters
        ----------
        pos : Tuple[int, int]
            Coordenadas (x, y) de la celda
            
        Returns
        -------
        int
            Número total de mosquitos en la celda
        """
        x, y = pos
        return int(self.S_m[x, y] + self.E_m[x, y] + self.I_m[x, y])
    
    def get_state_count(self, pos: Tuple[int, int], state: MosquitoState) -> int:
        """
        Obtiene el número de mosquitos en un estado específico.
        
        Parameters
        ----------
        pos : Tuple[int, int]
            Coordenadas (x, y) de la celda
        state : MosquitoState
            Estado epidemiológico
            
        Returns
        -------
        int
            Número de mosquitos en ese estado
        """
        x, y = pos
        
        if state == MosquitoState.SUSCEPTIBLE:
            return int(self.S_m[x, y])
        elif state == MosquitoState.EXPOSED:
            return int(self.E_m[x, y])
        elif state == MosquitoState.INFECTIOUS:
            return int(self.I_m[x, y])
        
        return 0
    
    def total_mosquitos(self) -> int:
        """
        Calcula el total de mosquitos en todo el grid.
        
        Returns
        -------
        int
            Número total de mosquitos
        """
        return int(self.S_m.sum() + self.E_m.sum() + self.I_m.sum())
    
    def total_infectious(self) -> int:
        """
        Calcula el total de mosquitos infecciosos.
        
        Returns
        -------
        int
            Número total de mosquitos infecciosos
        """
        return int(self.I_m.sum())
    
    def step(self, model: 'DengueModel'):
        """
        Procesa un día de simulación para todas las celdas.
        
        Ejecuta la dinámica de mosquitos en cada celda:
        1. Mortalidad diaria
        2. Transiciones de estado (E → I)
        3. Picaduras y transmisión
        4. Reproducción
        
        Parameters
        ----------
        model : DengueModel
            Referencia al modelo principal para acceder a parámetros
        """
        # Procesar cada celda del grid
        for x in range(self.width):
            for y in range(self.height):
                self._process_cell(x, y, model)
    
    def _process_cell(self, x: int, y: int, model: 'DengueModel'):
        """
        Procesa la dinámica de mosquitos en una celda específica.
        
        Secuencia de operaciones:
        1. Mortalidad diaria (binomial por compartimento)
        2. Transiciones E → I (incubación completada)
        3. Picaduras y transmisión bidireccional
        4. Reproducción (hembras que han picado)
        
        Parameters
        ----------
        x : int
            Coordenada x de la celda
        y : int
            Coordenada y de la celda
        model : DengueModel
            Referencia al modelo principal
        """
        # Si no hay mosquitos en esta celda, skip
        if self.S_m[x, y] == 0 and self.E_m[x, y] == 0 and self.I_m[x, y] == 0:
            return
        
        # 1. Mortalidad diaria
        self._apply_mortality(x, y, model)
        
        # 2. Transiciones de estado
        self._apply_transitions(x, y, model)
        
        # 3. Picaduras y transmisión
        self._process_biting_and_transmission(x, y, model)
        
        # 4. Reproducción
        self._process_reproduction(x, y, model)
    
    def _apply_mortality(self, x: int, y: int, model: 'DengueModel'):
        """
        Aplica mortalidad diaria a mosquitos en una celda.
        
        Usa muestreo binomial para determinar muertes en cada compartimento.
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        model : DengueModel
            Modelo principal
        """
        mortality_rate = model.mortality_rate
        
        # Mortalidad por compartimento (binomial)
        if self.S_m[x, y] > 0:
            deaths_S = model.random.binomial(self.S_m[x, y], mortality_rate)
            self.S_m[x, y] -= deaths_S
        
        if self.E_m[x, y] > 0:
            deaths_E = model.random.binomial(self.E_m[x, y], mortality_rate)
            self.E_m[x, y] -= deaths_E
        
        if self.I_m[x, y] > 0:
            deaths_I = model.random.binomial(self.I_m[x, y], mortality_rate)
            self.I_m[x, y] -= deaths_I
    
    def _apply_transitions(self, x: int, y: int, model: 'DengueModel'):
        """
        Aplica transiciones de estado E → I.
        
        Mosquitos expuestos se vuelven infecciosos después del período
        de incubación extrínseca (EIP).
        
        Aproximación: tasa diaria = 1 / EIP
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        model : DengueModel
            Modelo principal
        """
        if self.E_m[x, y] == 0:
            return
        
        # Período de incubación extrínseca (días)
        # Aproximación: transición diaria proporcional
        eip = 10  # Típicamente 8-12 días para dengue
        transition_rate = 1.0 / eip
        
        # Mosquitos que completan incubación
        transitions = model.random.binomial(self.E_m[x, y], transition_rate)
        
        self.E_m[x, y] -= transitions
        self.I_m[x, y] += transitions
    
    def _process_biting_and_transmission(self, x: int, y: int, model: 'DengueModel'):
        """
        Procesa picaduras y transmisión bidireccional en una celda.
        
        Implementa:
        1. Mosquitos infecciosos → Humanos susceptibles
        2. Humanos infecciosos → Mosquitos susceptibles
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        model : DengueModel
            Modelo principal
        """
        # Obtener humanos en esta celda
        humanos = model.grid.get_cell_contents((x, y))
        if not humanos:
            return
        
        # Filtrar solo humanos (no mosquitos si hubiera agentes mixtos)
        from ..agents.human_agent import HumanAgent
        humanos = [a for a in humanos if isinstance(a, HumanAgent)]
        
        if not humanos:
            return
        
        # Parámetros de transmisión
        bite_prob = model.bite_probability
        transmission_prob = model.transmission_probability
        
        # 1. Transmisión Mosquito → Humano
        if self.I_m[x, y] > 0:
            self._mosquito_to_human_transmission(x, y, humanos, bite_prob, transmission_prob, model)
        
        # 2. Transmisión Humano → Mosquito
        if self.S_m[x, y] > 0:
            self._human_to_mosquito_transmission(x, y, humanos, bite_prob, transmission_prob, model)
    
    def _mosquito_to_human_transmission(self, x: int, y: int, humanos: List, 
                                       bite_prob: float, trans_prob: float, model: 'DengueModel'):
        """
        Transmisión de mosquitos infecciosos a humanos susceptibles.
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        humanos : List
            Lista de agentes humanos en la celda
        bite_prob : float
            Probabilidad de picar
        trans_prob : float
            Probabilidad de transmisión dado picadura
        model : DengueModel
            Modelo principal
        """
        # Mosquitos infecciosos que pican
        infectious_bites = model.random.binomial(self.I_m[x, y], bite_prob)
        
        if infectious_bites == 0:
            return
        
        # Humanos susceptibles en la celda
        susceptible_humans = [h for h in humanos if h.es_susceptible()]
        
        if not susceptible_humans:
            return
        
        # Distribuir picaduras entre humanos susceptibles
        # Cada humano tiene probabilidad proporcional de ser picado
        for _ in range(infectious_bites):
            if not susceptible_humans:
                break
            
            # Seleccionar humano al azar
            human = model.random.choice(susceptible_humans)
            
            # Transmisión con probabilidad trans_prob
            if model.random.random() < trans_prob:
                human.get_exposed()
                # Remover de susceptibles (ya no puede ser infectado de nuevo)
                susceptible_humans.remove(human)
    
    def _human_to_mosquito_transmission(self, x: int, y: int, humanos: List,
                                       bite_prob: float, trans_prob: float, model: 'DengueModel'):
        """
        Transmisión de humanos infecciosos a mosquitos susceptibles.
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        humanos : List
            Lista de agentes humanos en la celda
        bite_prob : float
            Probabilidad de picar
        trans_prob : float
            Probabilidad de transmisión dado picadura
        model : DengueModel
            Modelo principal
        """
        # Mosquitos susceptibles que pican
        susceptible_bites = model.random.binomial(self.S_m[x, y], bite_prob)
        
        if susceptible_bites == 0:
            return
        
        # Proporción de humanos infecciosos en la celda
        infectious_humans = sum(1 for h in humanos if h.es_infeccioso())
        
        if infectious_humans == 0:
            return
        
        p_infectious = infectious_humans / len(humanos)
        
        # Mosquitos que pican humanos infecciosos y se infectan
        new_exposed = model.random.binomial(susceptible_bites, p_infectious * trans_prob)
        
        if new_exposed > 0:
            self.S_m[x, y] -= new_exposed
            self.E_m[x, y] += new_exposed
    
    def _process_reproduction(self, x: int, y: int, model: 'DengueModel'):
        """
        Procesa reproducción de mosquitos en una celda.
        
        Solo hembras que han picado pueden reproducirse.
        Los huevos se agregan al EggManager.
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        model : DengueModel
            Modelo principal
        """
        total_mosquitos = self.S_m[x, y] + self.E_m[x, y] + self.I_m[x, y]
        
        if total_mosquitos == 0:
            return
        
        # Parámetros de reproducción
        female_ratio = model.female_ratio
        bite_prob = model.bite_probability
        eggs_per_female = model.eggs_per_female
        
        # Hembras en la celda
        females = int(total_mosquitos * female_ratio)
        
        if females == 0:
            return
        
        # Hembras que pican (necesario para reproducción)
        biting_females = model.random.binomial(females, bite_prob)
        
        if biting_females == 0:
            return
        
        # Huevos puestos (agregar a EggManager)
        eggs = biting_females * eggs_per_female
        
        if eggs > 0:
            # Agregar huevos al sitio de cría más cercano
            # (simplificación: usar la celda actual como sitio)
            model.egg_manager.add_eggs((x, y), eggs)
    
    def __repr__(self) -> str:
        """Representación en cadena del grid"""
        total = self.total_mosquitos()
        infectious = self.total_infectious()
        return f"MosquitoPopulationGrid(total={total}, infectious={infectious}, grid={self.width}×{self.height})"
