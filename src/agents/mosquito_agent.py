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
    Agente mosquito hembra con estados SI y reproducción dependiente de temperatura.
    
    OPTIMIZACIÓN: Solo se modelan hembras. Los machos son implícitos ya que:
    - No pican ni transmiten enfermedades
    - No ponen huevos
    - Solo sirven para apareamiento (modelado con mating_probability)
    - Reducen la población de agentes en ~50% sin pérdida de información
    
    Representa un mosquito Aedes aegypti hembra en la simulación con:
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
    sitio_cria : Optional[Tuple[int, int]], default=None
        Posición del sitio de cría (para huevos)
        
    Attributes
    ----------
    estado : EstadoMosquito
        Estado epidemiológico (S o I)
    etapa : EtapaVida
        Etapa de vida actual
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
        sitio_cria: Optional[Tuple[int, int]] = None
    ):
        super().__init__(unique_id, model)
        
        # Estado epidemiológico
        self.estado = EstadoMosquito.SUSCEPTIBLE
        
        # Ciclo de vida
        self.etapa = etapa
        self.dias_como_huevo = 0
        self.edad = 0
        
        # Comportamiento
        self.ha_picado_hoy = False
        self.esta_apareado = False  # Solo hembras existen en el modelo (machos implícitos)
        self.sitio_cria = sitio_cria
        self.dias_desde_ultima_puesta = 0  # Control de cooldown de reproducción
        
        # Ciclo gonotrófico: días entre puestas (cargado desde configuración)
        # Rango biológico: 2-4 días según Scott et al. (1993), Maciel-de-Freitas et al. (2006)
        self.dias_cooldown_reproduccion = model.gonotrophic_cycle_days
        
        # Parámetros desde configuración del modelo (cacheados para rendimiento)
        self.mortality_rate = model.mortality_rate
        self.sensory_range = model.sensory_range
        self.mating_probability = model.mating_probability
        self.eggs_per_female = model.eggs_per_female
        
        # Parámetros del modelo de grados-día acumulados (GDD) para desarrollo inmaduro
        # Basado en Tun-Lin et al. (1999) para Aedes aegypti [15]
        self.immature_development_threshold = model.immature_development_threshold  # T_base_inmaduro (°C)
        self.immature_thermal_constant = model.immature_thermal_constant  # K_inmaduro (°C·día)
        
        # Acumulador de grados-día para desarrollo inmaduro (huevo → adulto)
        self.grados_acumulados = 0.0
        
        # Parámetros de transmisión (cacheados)
        self.mosquito_to_human_prob = model.mosquito_to_human_prob  # α
        self.human_to_mosquito_prob = model.human_to_mosquito_prob  # β
        
        # Parámetros de reproducción (cacheados)
        self.rainfall_threshold = model.rainfall_threshold
        self.female_ratio = model.female_ratio
        
        # Parámetros de movimiento (cacheados)
        self.max_range = model.max_range
    
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
        Procesa el desarrollo inmaduro usando el modelo de grados-día acumulados (GDD).
        
        Basado en Tun-Lin et al. (1999) para Aedes aegypti [15].
        El desarrollo desde huevo hasta adulto se completa cuando se acumula
        la constante térmica K_inmaduro = 181.2 ± 36.1 °C·día.
        
        Fórmula de grados-día diarios:
        GD_dia = max(T_dia - T_base_inmaduro, 0)
        
        Donde:
        - T_dia: temperatura media diaria (tavg en °C)
        - T_base_inmaduro: umbral térmico mínimo = 8.3 ± 3.6 °C
        - El desarrollo solo progresa cuando T_dia > T_base_inmaduro
        
        Referencias:
        [15] Tun-Lin et al. (1999) - Aedes aegypti development thresholds
        [16] [17] Modelos entomológicos estándar de grados-día
        """
        # Obtener temperatura media diaria del modelo
        temperatura = self.model.temperatura_actual  # T_dia (tavg)
        
        # Calcular contribución diaria de grados-día
        # GD_dia = max(T_dia - T_base_inmaduro, 0)
        grados_dia = max(temperatura - self.immature_development_threshold, 0.0)
        
        # Acumular grados-día
        self.grados_acumulados += grados_dia
        
        # Incrementar contador de días (para métricas)
        self.dias_como_huevo += 1
        
        # Verificar si se alcanzó la constante térmica total
        if self.grados_acumulados >= self.immature_thermal_constant:
            self.eclosionar()
    
    def eclosionar(self):
        """
        Transición de HUEVO a ADULTO.
        
        El mosquito emerge como adulto y se coloca en el sitio de cría.
        
        NOTA: Se asume que self.sitio_cria contiene coordenadas válidas dentro del grid.
        Los sitios de cría provienen de fuentes validadas:
        - self.model.sitios_cria (validados durante inicialización del grid)
        - self.model.sitios_cria_temporales (creados por _actualizar_sitios_cria_temporales)
        - self.random.randrange() en _inicializar_mosquitos (garantizado dentro de bounds)
        
        Si se modifican estas fuentes, asegurar que las coordenadas cumplan:
        0 <= x < grid.width y 0 <= y < grid.height
        """
        self.etapa = EtapaVida.ADULTO
        self.dias_como_huevo = 0
        self.edad = 0
        self.grados_acumulados = 0.0        
        
        # Colocar en el sitio de cría
        if self.sitio_cria and not self.pos:
            self.model.grid.place_agent(self, self.sitio_cria)
    
    def procesar_comportamiento_adulto(self):
        """
        Ejecuta el comportamiento del mosquito adulto (hembra).
        
        Secuencia diaria:
        1. Verificar mortalidad
        2. Moverse (caminata aleatoria o dirigida a humano)
        3. Intentar picar
        4. Aparearse (apareamiento implícito)
        5. Reproducir si está apareada y ha picado
        """
        self.edad += 1
        self.ha_picado_hoy = False
        
        # Incrementar cooldown de reproducción
        if self.dias_desde_ultima_puesta < self.dias_cooldown_reproduccion:
            self.dias_desde_ultima_puesta += 1
        
        # 1. Mortalidad diaria (usar parámetro del modelo)
        if self.random.random() < self.mortality_rate:
            # Solo remover del grid si tiene posición
            if self.pos is not None:
                self.model.grid.remove_agent(self)
            self.model.agents.remove(self)
            return
        
        # 2. Movimiento
        self.mover()
        
        # 3. Picar humano
        self.intentar_picar()
        
        # 4. Apareamiento (implícito: probabilidad de encontrar macho)
        if not self.esta_apareado:
            self.intentar_apareamiento()
        
        # 5. Reproducción
        if self.esta_apareado and self.ha_picado_hoy:
            self.intentar_reproduccion()
    
    def mover(self):
        """
        Movimiento del mosquito: caminata aleatoria o dirigida.
        
        Lógica:
        - Buscar humanos dentro del rango sensorial (Sr = 3)
        - Si detecta humano: moverse hacia él
        - Si no: caminata aleatoria (Moore neighborhood)
        
        Nota: Todos los mosquitos en el modelo son hembras (los machos son implícitos).
        """
        # Verificar que el mosquito tenga posición (huevos no tienen posición)
        if self.pos is None:
            return
        
        # Buscar humano cercano
        humano_cercano = self.buscar_humano_cercano()
        if humano_cercano:
            # Moverse hacia el humano detectado
            self.mover_hacia(humano_cercano.pos)
            return
        
        # Caminata aleatoria si no detecta humano
        self.mover_aleatorio()
    
    def mover_aleatorio(self):
        """Movimiento aleatorio dentro del rango de vuelo diario (Fr)."""
        vecindad = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False,
            radius=self.max_range  # Rango de vuelo del mosquito (por defecto 5 celdas ~190m)
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
            radius=self.sensory_range
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
        
        Puede resultar en:
        - Transmisión mosquito → humano (si mosquito infectado, humano susceptible)
        - Transmisión humano → mosquito (si mosquito susceptible, humano infectado)
        
        Probabilidades desde configuración del modelo:
        - α (mosquito → humano): mosquito_to_human_prob (por defecto 0.6)
        - β (humano → mosquito): human_to_mosquito_prob (por defecto 0.275)
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
        alpha = self.mosquito_to_human_prob  # α
        beta = self.human_to_mosquito_prob  # β
        
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
        Intenta aparearse (apareamiento implícito con población de machos).
        
        En lugar de buscar machos físicos en el modelo (que no aportan nada),
        asumimos que hay suficientes machos en el ambiente y aplicamos
        directamente la probabilidad de apareamiento.
        
        Probabilidad de éxito: mating_probability (por defecto 0.6)
        
        Justificación biológica:
        - Machos no pican ni transmiten enfermedades
        - Machos no ponen huevos
        - Su única función es aparearse
        - Modelar machos consume ~50% de recursos sin aportar información
        - Esta simplificación mantiene la misma dinámica poblacional
        """
        if self.random.random() < self.mating_probability:
            self.esta_apareado = True
    
    def intentar_reproduccion(self):
        """
        Intenta poner huevos en un sitio de cría cercano.
        
        Requisitos:
        - Estar apareada (probabilidad aplicada en intentar_apareamiento)
        - Haber picado (ingesta de sangre)
        - Encontrar sitio de cría activo
        - Condiciones climáticas favorables (precipitación >= umbral)
        - Haber pasado el período de cooldown (ciclo gonotrófico ~3 días)
        
        Resultado: eggs_per_female huevos (por defecto 100)
        Sexo de huevos: female_ratio determina proporción de hembras
        
        Nota: Solo los huevos hembra se convertirán en adultos. Los huevos
        macho son descartados (nunca eclosionan) ya que los machos no
        aportan información al modelo epidemiológico.
        """
        # Verificar cooldown (ciclo gonotrófico: tiempo entre puestas)
        if self.dias_desde_ultima_puesta < self.dias_cooldown_reproduccion:
            return
        
        # Verificar precipitación (necesaria para sitios de cría activos)
        precipitacion = self.model.precipitacion_actual if hasattr(self.model, 'precipitacion_actual') else 0
        
        if precipitacion < self.rainfall_threshold:
            return
        
        # Buscar sitio de cría cercano
        sitio = self._buscar_sitio_cria()
        if not sitio:
            return
        
        # Poner solo huevos hembra (optimización: los machos no aportan al modelo)
        # female_ratio determina cuántos huevos son hembras
        num_huevos_hembra = int(self.eggs_per_female * self.female_ratio)
        
        # Crear solo huevos hembra
        for _ in range(num_huevos_hembra):
            unique_id = self.model.next_id()
            huevo = MosquitoAgent(
                unique_id=unique_id,
                model=self.model,
                etapa=EtapaVida.HUEVO,
                sitio_cria=sitio
            )
            
            # No agregar al grid (huevos no ocupan espacio hasta eclosionar)
            self.model.agents.add(huevo)
        
        # Resetear estado reproductivo
        self.ha_picado_hoy = False
        self.dias_desde_ultima_puesta = 0  # Reiniciar cooldown
    
    def _buscar_sitio_cria(self) -> Optional[Tuple[int, int]]:
        """
        Busca sitio de cría activo cercano (celdas tipo AGUA).
        
        Busca dentro del rango máximo de vuelo del mosquito (Fr).
        
        OPTIMIZACIÓN: Usa índice espacial del modelo para búsqueda O(1) en lugar de O(n).
        
        Returns
        -------
        Optional[Tuple[int, int]]
            Coordenadas del sitio de cría más cercano o None
        """
        if self.pos is None:
            return None
        
        # Log para debugging
        import time
        start = time.time()
        
        # Obtener sitios cercanos usando el índice espacial del modelo
        # Esto solo busca en sectores relevantes (mucho más rápido)
        sitios_candidatos = self.model.obtener_sitios_cercanos(self.pos, self.max_range)
        
        elapsed_query = time.time() - start
        if elapsed_query > 0.01:  # Si tarda más de 10ms
            print(f"\n⚠️  Mosquito {self.unique_id}: Consulta índice espacial tardó {elapsed_query*1000:.1f}ms", flush=True)
        
        if not sitios_candidatos:
            return None
        
        # Log si hay muchos candidatos (indica problema con índice)
        if len(sitios_candidatos) > 500:
            print(f"\n⚠️  Mosquito {self.unique_id}: Índice retornó {len(sitios_candidatos)} candidatos (demasiados!)", flush=True)
        
        # Buscar el sitio más cercano dentro del rango
        x, y = self.pos
        max_range_sq = self.max_range ** 2  # Comparar distancias al cuadrado (evita sqrt)
        
        mejor_sitio = None
        mejor_dist_sq = float('inf')
        
        for sitio in sitios_candidatos:
            sx, sy = sitio
            
            # Calcular distancia euclidiana al cuadrado
            dist_sq = (sx - x) ** 2 + (sy - y) ** 2
            
            # Verificar si está dentro del rango y es más cercano
            if dist_sq <= max_range_sq and dist_sq < mejor_dist_sq:
                mejor_dist_sq = dist_sq
                mejor_sitio = sitio
        
        elapsed_total = time.time() - start
        if elapsed_total > 0.1:  # Si tarda más de 100ms
            print(f"\n🐌 Búsqueda lenta: {elapsed_total*1000:.1f}ms ({len(sitios_candidatos)} candidatos)", flush=True)
        
        return mejor_sitio
    
    def _distancia(self, pos: Tuple[int, int]) -> float:
        """
        Calcula distancia euclidiana a una posición.
        
        NOTA: Este método asume que self.pos no es None (solo adultos llaman).
        Los huevos/larvas/pupas tienen self.pos=None, pero están protegidos por
        validaciones en mover(), buscar_humano_cercano() y _buscar_sitio_cria()
        que verifican self.pos antes de llamar este método.
        
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
                f"etapa={self.etapa.value}, pos={self.pos})")
