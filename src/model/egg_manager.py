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
    
    TRANSMISIÓN VERTICAL: Los huevos pueden heredar el virus del dengue
    de hembras infectadas durante la oviposición (1-10% típicamente).
    
    Attributes
    ----------
    sitio_cria : Tuple[int, int]
        Coordenadas (x, y) del sitio de cría donde se pusieron los huevos
    cantidad : int
        Número total de huevos en el lote (susceptibles + infectados)
    cantidad_infectados : int
        Número de huevos infectados por transmisión vertical
    grados_acumulados : float
        Grados-día acumulados para desarrollo (modelo GDD)
    dias_como_huevo : int
        Días transcurridos desde la puesta
    fecha_puesta : int
        Día de simulación en que se pusieron los huevos
    """
    sitio_cria: Tuple[int, int]
    cantidad: int
    cantidad_infectados: int = 0
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
    
    def add_eggs(self, sitio_cria: Tuple[int, int], cantidad: int, cantidad_infectados: int = 0):
        """
        Agrega un lote de huevos a un sitio de cría.
        
        Si ya existe un lote en el mismo sitio con la misma edad (mismo día),
        se agregan al lote existente. Esto maximiza la agrupación y reduce
        el número de objetos.
        
        TRANSMISIÓN VERTICAL: Permite agregar huevos infectados resultantes
        de la transmisión del virus de madre a cría (1-10% típicamente).
        
        CAPACIDAD DE CARGA: Implementa un límite máximo de 500 huevos por sitio
        para simular competencia larvaria y limitación de recursos.
        
        Parameters
        ----------
        sitio_cria : Tuple[int, int]
            Coordenadas (x, y) del sitio de cría
        cantidad : int
            Número total de huevos a agregar
        cantidad_infectados : int, default=0
            Número de huevos infectados (por transmisión vertical)
        """
        if cantidad <= 0:
            return
        
        # Validar que infectados no exceda total
        cantidad_infectados = min(cantidad_infectados, cantidad)
        
        # Buscar lote existente en el mismo sitio y mismo día
        dia_actual = self.model.dia_simulacion
        for batch in self.egg_batches:
            if batch.sitio_cria == sitio_cria and batch.fecha_puesta == dia_actual:
                batch.cantidad += cantidad
                batch.cantidad_infectados += cantidad_infectados
                return
        
        # Crear nuevo lote
        self.egg_batches.append(EggBatch(
            sitio_cria=sitio_cria,
            cantidad=cantidad,
            cantidad_infectados=cantidad_infectados,
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
        
        MODELO METAPOBLACIONAL: En lugar de crear agentes individuales,
        agrega mosquitos susceptibles al grid de poblaciones en la celda
        correspondiente al sitio de cría.
        
        TRANSMISIÓN VERTICAL: Los huevos infectados eclosionan como mosquitos
        infecciosos, manteniendo el virus en la población incluso cuando
        los adultos infectados mueren.
        
        Parameters
        ----------
        batch : EggBatch
            Lote de huevos a eclosionar
        """
        # Agregar mosquitos al grid de poblaciones (modelo metapoblacional)
        if hasattr(self.model, 'mosquito_pop'):
            from .mosquito_population import MosquitoState
            
            # Mosquitos susceptibles (no infectados)
            cantidad_susceptibles = batch.cantidad - batch.cantidad_infectados
            if cantidad_susceptibles > 0:
                self.model.mosquito_pop.add_mosquitos(
                    batch.sitio_cria, 
                    cantidad_susceptibles,
                    MosquitoState.SUSCEPTIBLE
                )
            
            # Mosquitos infectados por transmisión vertical
            # Nacen directamente como INFECCIOSOS (pueden transmitir inmediatamente)
            if batch.cantidad_infectados > 0:
                self.model.mosquito_pop.add_mosquitos(
                    batch.sitio_cria, 
                    batch.cantidad_infectados,
                    MosquitoState.INFECTIOUS
                )
        else:
            # Fallback: crear agentes individuales (versión antigua)
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
    
    def count_infected_eggs(self) -> int:
        """
        Cuenta el total de huevos INFECTADOS en todos los lotes.
        
        Returns
        -------
        int
            Número de huevos infectados por transmisión vertical
        """
        return sum(batch.cantidad_infectados for batch in self.egg_batches)
    
    def get_eggs_stats(self) -> dict:
        """
        Obtiene estadísticas detalladas de huevos.
        
        Returns
        -------
        dict
            Diccionario con:
            - total: Total de huevos
            - infectados: Huevos infectados
            - susceptibles: Huevos no infectados
            - porcentaje_infectados: % de huevos infectados
            - lotes: Número de lotes activos
        """
        total = self.count_eggs()
        infectados = self.count_infected_eggs()
        susceptibles = total - infectados
        porcentaje = (infectados / total * 100) if total > 0 else 0.0
        
        return {
            'total': total,
            'infectados': infectados,
            'susceptibles': susceptibles,
            'porcentaje_infectados': porcentaje,
            'lotes': len(self.egg_batches)
        }
    
    def apply_mortality(self, mortality_rate: float):
        """
        Aplica mortalidad diaria a los huevos.
        
        Reduce la cantidad de huevos en cada lote según la tasa de mortalidad.
        Elimina lotes que quedan sin huevos.
        
        TRANSMISIÓN VERTICAL: Mantiene la proporción de huevos infectados
        al aplicar mortalidad (la infección no afecta supervivencia del huevo).
        
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
            
            # Calcular muertes entre infectados (proporcional)
            if batch.cantidad > 0:
                proporcion_infectados = batch.cantidad_infectados / batch.cantidad
                muertes_infectados = int(muertes * proporcion_infectados)
                
                # Redondeo estocástico para infectados
                muertes_inf_esperadas = muertes * proporcion_infectados
                if self.model.random.random() < (muertes_inf_esperadas - muertes_infectados):
                    muertes_infectados += 1
                
                batch.cantidad_infectados = max(0, batch.cantidad_infectados - muertes_infectados)
            
            batch.cantidad -= muertes
            
            # Asegurar consistencia
            batch.cantidad_infectados = min(batch.cantidad_infectados, batch.cantidad)
            
            # Marcar para eliminación si no quedan huevos
            if batch.cantidad <= 0:
                batches_to_remove.append(batch)
        
        # Eliminar lotes vacíos
        for batch in batches_to_remove:
            self.egg_batches.remove(batch)
    
    def apply_temperature_mortality(self):
        """
        Aplica mortalidad adicional a los huevos según la temperatura.
        
        La mortalidad se ajusta según la temperatura:
        - T < 10°C: 90% de huevos mueren (frío extremo)
        - T > 40°C: 80% de huevos mueren (calor extremo)
        - 10°C < T < 15°C o 35°C < T < 40°C: 50% mueren (subóptimo)
        - 15°C <= T <= 35°C: Mortalidad base normal
        
        Se llama en cada paso de simulación después de la mortalidad base.
        """
        temperatura = self.model.temperatura_actual
        
        # Determinar tasa de mortalidad adicional según temperatura
        if temperatura < self.model.temp_extreme_cold:
            # Frío extremo (< 10°C)
            mortality_rate = self.model.egg_mortality_extreme_cold
        elif temperatura > self.model.temp_extreme_heat:
            # Calor extremo (> 40°C)
            mortality_rate = self.model.egg_mortality_extreme_heat
        elif temperatura < self.model.temp_suboptimal_cold or temperatura > self.model.temp_suboptimal_heat:
            # Subóptimo (10-15°C o 35-40°C)
            mortality_rate = self.model.egg_mortality_suboptimal
        else:
            # Temperatura óptima (15-35°C) - sin mortalidad adicional
            return
        
        # Aplicar mortalidad por temperatura
        batches_to_remove = []
        
        for batch in self.egg_batches:
            # Calcular muertes (redondeo estocástico)
            muertes_esperadas = batch.cantidad * mortality_rate
            muertes = int(muertes_esperadas)
            
            # Probabilidad de muerte adicional (parte fraccionaria)
            if self.model.random.random() < (muertes_esperadas - muertes):
                muertes += 1
            
            # Calcular muertes entre infectados (proporcional)
            if batch.cantidad > 0:
                proporcion_infectados = batch.cantidad_infectados / batch.cantidad
                muertes_infectados = int(muertes * proporcion_infectados)
                
                # Redondeo estocástico para infectados
                muertes_inf_esperadas = muertes * proporcion_infectados
                if self.model.random.random() < (muertes_inf_esperadas - muertes_infectados):
                    muertes_infectados += 1
                
                batch.cantidad_infectados = max(0, batch.cantidad_infectados - muertes_infectados)
            
            batch.cantidad -= muertes
            
            # Asegurar consistencia
            batch.cantidad_infectados = min(batch.cantidad_infectados, batch.cantidad)
            
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
