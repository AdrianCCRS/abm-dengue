"""
Módulo de agentes para el modelo ABM del Dengue.

Contiene las implementaciones de agentes humanos y mosquitos.
"""

from .human_agent import HumanAgent, EstadoSalud, TipoMovilidad
from .mosquito_agent import MosquitoAgent, EstadoMosquito, EtapaVida

__version__ = "0.1.0"
__all__ = [
    'HumanAgent',
    'MosquitoAgent',
    'EstadoSalud',
    'EstadoMosquito',
    'TipoMovilidad',
    'EtapaVida'
]
