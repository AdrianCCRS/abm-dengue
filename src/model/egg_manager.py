# -*- coding: utf-8 -*-
"""
Gestor de huevos de mosquito para el modelo ABM del Dengue.

Este módulo implementa una estructura de datos ligera para manejar huevos
sin crear agentes individuales, optimizando el rendimiento del modelo.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

from dataclasses import dataclass
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .dengue_model import DengueModel


@dataclass
class EggBatch:
    """
    Lote de huevos en un sitio de cría.
    
    Agrupa múltiples huevos en la misma ubicación para reducir overhead.
    En lugar de crear 100 agentes individuales, se crea un solo objeto
    que representa el lote completo.
    
    Attributes
    ----------
    sitio_cria : Tuple[int, int]
        Coordenadas (x, y) del sitio de cría donde se pusieron los huevos
    cantidad : int
        Número de huevos en el lote
    grados_acumulados : float
        Grados-día acumulados para desarrollo (modelo GDD)
    dias_como_huevo : int
        Días transcurridos desde la puesta
    fecha_puesta : int
        Día de simulación en que se pusieron los huevos
    """
    sitio_cria: Tuple[int, int]
    cantidad: int
    grados_acumulados: float = 0.0
    dias_como_huevo: int = 0
    fecha_puesta: int = 0


class EggManager:
    """
    Gestor centralizado de huevos de mosquito.
    
    Maneja el desarrollo de huevos usando el modelo de grados-día acumulados
    (GDD) sin crear agentes individuales, reduciendo drásticamente el overhead
    de memoria y CPU.
    
    El modelo GDD está basado en Tun-Lin et al. (1999) para Aedes aegypti:
    - Umbral térmico: 8.3°C (T_base_inmaduro)
    - Constante térmica: 181.2 °C·día (K_inmaduro)
    - Fórmula: GD_dia = max(T_dia - T_base, 0)
    
    Parameters
    ----------
    model : DengueModel
        Referencia al modelo principal
        
    Attributes
    ----------
    model : DengueModel
        Modelo al que pertenece el gestor
    egg_batches : List[EggBatch]
        Lista de lotes de huevos activos
    """
    
    def __init__(self, model: 'DengueModel'):
        """
        Inicializa el gestor de huevos.
        
        Parameters
        ----------
        model : DengueModel
            Modelo principal de la simulación
        """
        self.model = model
        self.egg_batches: List[EggBatch] = []
    
    def add_eggs(self, sitio_cria: Tuple[int, int], cantidad: int):
        """
        Agrega un lote de huevos a un sitio de cría.
        
        Si ya existe un lote en el mismo sitio con la misma edad (mismo día),
        se agregan al lote existente. Esto maximiza la agrupación y reduce
        el número de objetos.
        
        Parameters
        ----------
        sitio_cria : Tuple[int, int]
            Coordenadas (x, y) del sitio de cría
        cantidad : int
            Número de huevos a agregar
        """
        if cantidad <= 0:
            return
        
        # Buscar lote existente en el mismo sitio y mismo día
        dia_actual = self.model.dia_simulacion
        for batch in self.egg_batches:
            if batch.sitio_cria == sitio_cria and batch.fecha_puesta == dia_actual:
                batch.cantidad += cantidad
                return
        
        # Crear nuevo lote
        self.egg_batches.append(EggBatch(
            sitio_cria=sitio_cria,
            cantidad=cantidad,
            grados_acumulados=0.0,
            dias_como_huevo=0,
            fecha_puesta=dia_actual
        ))
    
    def step(self):
        """
        Procesa el desarrollo de todos los lotes de huevos.
        
        Aplica el modelo de grados-día acumulados (GDD) a cada lote:
        1. Calcula grados-día del día actual
        2. Acumula en cada lote
        3. Identifica lotes que alcanzaron la constante térmica
        4. Eclosiona los lotes maduros
        
        Este método se llama una vez por día de simulación.
        """
        # Obtener temperatura actual del modelo
        temperatura = self.model.temperatura_actual
        
        # Calcular contribución diaria de grados-día
        # GD_dia = max(T_dia - T_base_inmaduro, 0)
        umbral = self.model.immature_development_threshold  # 8.3°C
        grados_dia = max(temperatura - umbral, 0.0)
        
        # Lotes que alcanzaron madurez
        batches_to_hatch = []
        
        # Actualizar cada lote
        for batch in self.egg_batches:
            batch.grados_acumulados += grados_dia
            batch.dias_como_huevo += 1
            
            # Verificar si alcanzó la constante térmica (181.2 °C·día)
            if batch.grados_acumulados >= self.model.immature_thermal_constant:
                batches_to_hatch.append(batch)
        
        # Eclosionar lotes maduros (ordenados para reproducibilidad)
        # Ordenar por fecha de puesta y luego por sitio para determinismo con seed
        batches_to_hatch.sort(key=lambda b: (b.fecha_puesta, b.sitio_cria))
        
        for batch in batches_to_hatch:
            self._hatch_batch(batch)
            self.egg_batches.remove(batch)
    
    def _hatch_batch(self, batch: EggBatch):
        """
        Convierte un lote de huevos en mosquitos adultos.
        
        Crea agentes MosquitoAgent para cada huevo del lote y los coloca
        en el sitio de cría correspondiente.
        
        Parameters
        ----------
        batch : EggBatch
            Lote de huevos a eclosionar
        """
        from ..agents.mosquito_agent import MosquitoAgent, EtapaVida
        
        for _ in range(batch.cantidad):
            # Crear mosquito adulto
            mosquito = MosquitoAgent(
                unique_id=self.model.next_id(),
                model=self.model,
                etapa=EtapaVida.ADULTO,
                sitio_cria=batch.sitio_cria
            )
            
            # Colocar en el sitio de cría
            self.model.grid.place_agent(mosquito, batch.sitio_cria)
            self.model.agents.add(mosquito)
    
    def count_eggs(self) -> int:
        """
        Cuenta el total de huevos en todos los lotes.
        
        Returns
        -------
        int
            Número total de huevos
        """
        return sum(batch.cantidad for batch in self.egg_batches)
    
    def apply_mortality(self, mortality_rate: float):
        """
        Aplica mortalidad diaria a los huevos.
        
        Reduce la cantidad de huevos en cada lote según la tasa de mortalidad.
        Elimina lotes que quedan sin huevos.
        
        Parameters
        ----------
        mortality_rate : float
            Tasa de mortalidad diaria (0.0 a 1.0)
            Ejemplo: 0.03 = 3% de mortalidad por día
        """
        batches_to_remove = []
        
        for batch in self.egg_batches:
            # Calcular muertes (redondeo estocástico)
            muertes_esperadas = batch.cantidad * mortality_rate
            muertes = int(muertes_esperadas)
            
            # Probabilidad de muerte adicional (parte fraccionaria)
            if self.model.random.random() < (muertes_esperadas - muertes):
                muertes += 1
            
            batch.cantidad -= muertes
            
            # Marcar para eliminación si no quedan huevos
            if batch.cantidad <= 0:
                batches_to_remove.append(batch)
        
        # Eliminar lotes vacíos
        for batch in batches_to_remove:
            self.egg_batches.remove(batch)
    
    def apply_lsm_control(self, coverage: float, effectiveness: float):
        """
        Aplica control larvario (LSM) a los lotes de huevos.
        
        Elimina huevos según la cobertura y efectividad del control.
        La reducción total es: coverage × effectiveness
        
        Parameters
        ----------
        coverage : float
            Cobertura espacial del control (0.0 a 1.0)
            Ejemplo: 0.7 = 70% de sitios tratados
        effectiveness : float
            Efectividad del tratamiento (0.0 a 1.0)
            Ejemplo: 0.8 = 80% de reducción en sitios tratados
        """
        reduccion_total = coverage * effectiveness
        batches_to_remove = []
        
        for batch in self.egg_batches:
            # Decidir si este lote es afectado por el control
            if self.model.random.random() < reduccion_total:
                # Eliminar lote completo (tratamiento efectivo)
                batches_to_remove.append(batch)
            elif self.model.random.random() < coverage:
                # Lote tratado pero no completamente efectivo
                # Reducir cantidad según efectividad
                reduccion = int(batch.cantidad * effectiveness)
                batch.cantidad -= reduccion
                
                if batch.cantidad <= 0:
                    batches_to_remove.append(batch)
        
        # Eliminar lotes afectados
        for batch in batches_to_remove:
            self.egg_batches.remove(batch)
    
    def get_eggs_by_site(self, sitio: Tuple[int, int]) -> int:
        """
        Cuenta huevos en un sitio de cría específico.
        
        Útil para implementar capacidad máxima por sitio.
        
        Parameters
        ----------
        sitio : Tuple[int, int]
            Coordenadas del sitio de cría
            
        Returns
        -------
        int
            Número total de huevos en ese sitio
        """
        return sum(batch.cantidad for batch in self.egg_batches 
                   if batch.sitio_cria == sitio)
    
    def __repr__(self) -> str:
        """Representación en cadena del gestor."""
        total_eggs = self.count_eggs()
        num_batches = len(self.egg_batches)
        return f"EggManager(batches={num_batches}, total_eggs={total_eggs})"
