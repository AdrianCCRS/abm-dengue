"""
Celda del Grid para el modelo ABM del Dengue.

Este módulo define los tipos de celdas y sus propiedades espaciales
en el entorno sin GIS.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

from enum import Enum
from typing import Tuple


class TipoCelda(Enum):
    """
    Tipos de celdas en el entorno simulado.
    
    Attributes
    ----------
    URBANA : str
        Zonas residenciales, oficinas, escuelas (85% del grid)
    PARQUE : str
        Áreas recreativas con alta exposición a mosquitos (10% del grid)
    AGUA : str
        Criaderos permanentes: lagos, estanques, tanques (5% del grid)
    """
    URBANA = "urbana"
    PARQUE = "parque"
    AGUA = "agua"


class Celda:
    """
    Representa una celda del grid con propiedades espaciales.
    
    Cada celda tiene un tipo que determina:
    - Dónde se mueven los humanos (urbana, parque)
    - Dónde se reproducen los mosquitos (agua)
    - Densidad de contacto humano-mosquito
    
    Parameters
    ----------
    tipo : TipoCelda
        Tipo de celda (urbana, parque, agua)
    pos : Tuple[int, int]
        Coordenadas (x, y) en el grid
        
    Attributes
    ----------
    tipo : TipoCelda
        Tipo de celda
    pos : Tuple[int, int]
        Coordenadas en el grid
    es_criadero : bool
        True si es sitio de cría permanente (tipo AGUA)
    densidad_humanos : int
        Número de humanos en la celda (actualizado dinámicamente)
    
    Examples
    --------
    >>> celda = Celda(TipoCelda.PARQUE, (10, 15))
    >>> celda.tipo
    <TipoCelda.PARQUE: 'parque'>
    >>> celda.es_criadero
    False
    
    >>> celda_agua = Celda(TipoCelda.AGUA, (5, 5))
    >>> celda_agua.es_criadero
    True
    """
    
    def __init__(self, tipo: TipoCelda, pos: Tuple[int, int]):
        self.tipo = tipo
        self.pos = pos
        self.es_criadero = (tipo == TipoCelda.AGUA)
        self.densidad_humanos = 0
    
    def es_parque(self) -> bool:
        """
        Verifica si la celda es un parque.
        
        Returns
        -------
        bool
            True si es tipo PARQUE
        """
        return self.tipo == TipoCelda.PARQUE
    
    def es_agua(self) -> bool:
        """
        Verifica si la celda es cuerpo de agua.
        
        Returns
        -------
        bool
            True si es tipo AGUA
        """
        return self.tipo == TipoCelda.AGUA
    
    def es_urbana(self) -> bool:
        """
        Verifica si la celda es zona urbana.
        
        Returns
        -------
        bool
            True si es tipo URBANA
        """
        return self.tipo == TipoCelda.URBANA
    
    def __repr__(self) -> str:
        """Representación en cadena de la celda."""
        return f"Celda({self.tipo.value}, pos={self.pos}, humanos={self.densidad_humanos})"
    
    def __str__(self) -> str:
        """Representación amigable de la celda."""
        return f"{self.tipo.value.capitalize()} en {self.pos}"
