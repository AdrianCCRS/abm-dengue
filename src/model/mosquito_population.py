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
        
        # Capacidad de carga por celda (se carga desde configuración)
        # Se inicializa en None y se establece cuando se pasa el modelo
        self.carrying_capacity_per_cell = None
    
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
        
        # 5. Aplicar capacidad de carga (evita crecimiento exponencial)
        self._apply_carrying_capacity(x, y, model)
    
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
        
        # Mortalidad por compartimento (binomial o aproximación normal)
        if self.S_m[x, y] > 0:
            deaths_S = self._safe_binomial(int(self.S_m[x, y]), mortality_rate)
            self.S_m[x, y] -= deaths_S
        
        if self.E_m[x, y] > 0:
            deaths_E = self._safe_binomial(int(self.E_m[x, y]), mortality_rate)
            self.E_m[x, y] -= deaths_E
        
        if self.I_m[x, y] > 0:
            deaths_I = self._safe_binomial(int(self.I_m[x, y]), mortality_rate)
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
        # Usar parámetro del modelo si existe, sino default 10 días
        eip = getattr(model, 'mosquito_incubation_period', 10)
        transition_rate = 1.0 / eip
        
        # Mosquitos que completan incubación
        transitions = self._safe_binomial(int(self.E_m[x, y]), transition_rate)
        
        self.E_m[x, y] -= transitions
        self.I_m[x, y] += transitions
    
    def _safe_binomial(self, n: int, p: float) -> int:
        """
        Muestreo binomial seguro que maneja poblaciones grandes.
        
        Para n grande, usa aproximación normal en vez de binomial
        para evitar overflow de numpy.
        
        Parameters
        ----------
        n : int
            Número de ensayos
        p : float
            Probabilidad de éxito
            
        Returns
        -------
        int
            Número de éxitos
        """
        if n <= 0:
            return 0
        
        if p <= 0:
            return 0
        
        if p >= 1:
            return n
        
        # Para n muy grande, usar aproximación normal
        # Binomial(n, p) ≈ Normal(μ=np, σ²=np(1-p))
        if n > 1000000:  # 1 millón
            mean = n * p
            std = np.sqrt(n * p * (1 - p))
            result = int(np.random.normal(mean, std))
            # Asegurar que está en rango válido
            return max(0, min(n, result))
        else:
            return np.random.binomial(n, p)
    
    def _process_biting_and_transmission(self, x: int, y: int, model: 'DengueModel'):
        """
        Procesa picaduras y transmisión bidireccional en una celda.
        
        IMPORTANTE: Los mosquitos en esta celda pueden picar humanos en un
        vecindario (Moore neighborhood), emulando el vuelo de mosquitos del
        modelo original sin simular trayectorias individuales.
        
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
        # Obtener humanos en vecindario Moore (radio = sensory_range)
        # Esto emula que los mosquitos vuelan para buscar humanos
        radius = model.sensory_range
        
        # Obtener vecinos en radio (incluye celda central)
        neighbors = model.grid.get_neighborhood(
            (x, y),
            moore=True,
            include_center=True,
            radius=radius
        )
        
        # Obtener todos los humanos en el vecindario
        humanos = []
        for neighbor_pos in neighbors:
            agents_in_cell = model.grid.get_cell_list_contents([neighbor_pos])
            from ..agents.human_agent import HumanAgent
            humanos.extend([a for a in agents_in_cell if isinstance(a, HumanAgent)])
        
        if not humanos:
            return
        
        # Parámetros de transmisión
        alpha = model.mosquito_to_human_prob  # α
        beta = model.human_to_mosquito_prob   # β
        
        # 1. Transmisión Mosquito → Humano
        if self.I_m[x, y] > 0:
            self._mosquito_to_human_transmission(x, y, humanos, alpha, model)
        
        # 2. Transmisión Humano → Mosquito
        if self.S_m[x, y] > 0:
            self._human_to_mosquito_transmission(x, y, humanos, beta, model)
    
    def _mosquito_to_human_transmission(self, x: int, y: int, humanos: List, 
                                       alpha: float, model: 'DengueModel'):
        """
        Transmisión de mosquitos infecciosos a humanos susceptibles.
        
        MODELO EXPLÍCITO DE PICADURA:
        1. Mosquitos infecciosos pican con probabilidad bite_rate
        2. Picaduras se distribuyen entre humanos (proporción susceptibles)
        3. Transmisión ocurre con probabilidad α dado que picó
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        humanos : List
            Lista de agentes humanos en el vecindario
        alpha : float
            Probabilidad de transmisión mosquito→humano (α) dado que picó
        model : DengueModel
            Modelo principal
        """
        I = int(self.I_m[x, y])
        if I <= 0:
            return

        susceptible_humans = [h for h in humanos if h.es_susceptible()]
        H_s = len(susceptible_humans)
        H_tot = len(humanos)

        if H_s == 0 or H_tot == 0:
            return

        # 1. Mosquitos infecciosos que pican hoy
        bite_rate = getattr(model, "bite_rate", 0.33)
        biting_I = self._safe_binomial(I, bite_rate)
        if biting_I == 0:
            return

        # 2. Picaduras sobre humanos susceptibles (proporcional a H_s/H_tot)
        p_susceptible = H_s / H_tot
        bites_on_sus = self._safe_binomial(biting_I, p_susceptible)
        if bites_on_sus == 0:
            return

        # 3. Transmisión exitosa (probabilidad α)
        new_infections = self._safe_binomial(bites_on_sus, alpha)
        if new_infections <= 0:
            return

        # 4. Limitar a humanos susceptibles disponibles
        new_infections = min(new_infections, H_s)

        # 5. Infectar humanos seleccionados aleatoriamente
        for human in model.random.sample(susceptible_humans, new_infections):
            human.get_exposed()
    
    def _human_to_mosquito_transmission(self, x: int, y: int, humanos: List,
                                       beta: float, model: 'DengueModel'):
        """
        Transmisión de humanos infecciosos a mosquitos susceptibles.
        
        MODELO EXPLÍCITO DE PICADURA:
        1. Mosquitos susceptibles pican con probabilidad bite_rate
        2. Picaduras se distribuyen entre humanos (proporción infecciosos)
        3. Transmisión ocurre con probabilidad β dado que picó
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        humanos : List
            Lista de agentes humanos en el vecindario
        beta : float
            Probabilidad de transmisión humano→mosquito (β) dado que picó
        model : DengueModel
            Modelo principal
        """
        S = int(self.S_m[x, y])
        if S <= 0:
            return

        infectious_humans = [h for h in humanos if h.es_infeccioso()]
        H_i = len(infectious_humans)
        H_tot = len(humanos)

        if H_tot == 0 or H_i == 0:
            return

        # 1. Mosquitos susceptibles que pican hoy
        bite_rate = getattr(model, "bite_rate", 0.33)
        biting_S = self._safe_binomial(S, bite_rate)
        if biting_S == 0:
            return

        # 2. Picaduras sobre humanos infecciosos (proporcional a H_i/H_tot)
        p_infectious = H_i / H_tot
        bites_on_inf = self._safe_binomial(biting_S, p_infectious)
        if bites_on_inf == 0:
            return

        # 3. Transmisión exitosa (probabilidad β)
        new_E = self._safe_binomial(bites_on_inf, beta)
        if new_E <= 0:
            return

        # 4. Limitar a mosquitos susceptibles disponibles
        new_E = min(new_E, S)
        self.S_m[x, y] -= new_E
        self.E_m[x, y] += new_E
    
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
        eggs_per_female = model.eggs_per_female
        gonotrophic_cycle = model.gonotrophic_cycle_days
        
        # Hembras en la celda
        females = int(total_mosquitos * female_ratio)
        
        if females == 0:
            return
        
        # Hembras que se reproducen (ciclo gonotrófico)
        # Probabilidad diaria = 1 / gonotrophic_cycle_days
        reproduction_prob = 1.0 / gonotrophic_cycle
        reproducing_females = self._safe_binomial(int(females), reproduction_prob)
        
        if reproducing_females == 0:
            return
        
        # Huevos puestos (agregar a EggManager)
        eggs = reproducing_females * eggs_per_female
        
        if eggs > 0:
            # Agregar huevos al sitio de cría más cercano
            # (simplificación: usar la celda actual como sitio)
            model.egg_manager.add_eggs((x, y), eggs)
    
    def _apply_carrying_capacity(self, x: int, y: int, model: 'DengueModel'):
        """
        Aplica capacidad de carga a una celda.
        
        Si la población excede la capacidad, reduce proporcionalmente
        todos los compartimentos.
        
        Parameters
        ----------
        x, y : int
            Coordenadas de la celda
        model : DengueModel
            Modelo principal (para obtener carrying_capacity_per_cell)
        """
        total = self.S_m[x, y] + self.E_m[x, y] + self.I_m[x, y]
        
        # Obtener capacidad de carga desde modelo
        capacity = getattr(model, 'carrying_capacity_per_cell', 3000)
        
        if total > capacity:
            # Reducir proporcionalmente
            factor = capacity / total
            self.S_m[x, y] = int(self.S_m[x, y] * factor)
            self.E_m[x, y] = int(self.E_m[x, y] * factor)
            self.I_m[x, y] = int(self.I_m[x, y] * factor)
    
    def __repr__(self) -> str:
        """Representación en cadena del grid"""
        total = self.total_mosquitos()
        infectious = self.total_infectious()
        return f"MosquitoPopulationGrid(total={total}, infectious={infectious}, grid={self.width}×{self.height})"
