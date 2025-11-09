"""
Módulo para cargar y acceder a datos climáticos desde CSV.

Este módulo maneja la lectura de datos climáticos históricos
para su uso en la simulación del modelo de dengue.

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

import pandas as pd
from datetime import datetime
from typing import Tuple, Optional
import os


class ClimateDataLoader:
    """
    Cargador de datos climáticos desde archivo CSV.
    
    Lee datos climáticos históricos y proporciona acceso a ellos
    por fecha para usar en la simulación.
    
    Parameters
    ----------
    csv_path : str
        Ruta al archivo CSV con datos climáticos
        
    Attributes
    ----------
    data : pd.DataFrame
        DataFrame con los datos climáticos cargados
    """
    
    def __init__(self, csv_path: str):
        """
        Inicializa el cargador de datos climáticos.
        
        Parameters
        ----------
        csv_path : str
            Ruta al archivo CSV con columnas:
            - date: fecha en formato YYYY-MM-DD
            - tavg: temperatura promedio diaria (°C)
            - prcp: precipitación diaria (mm)
            
        Raises
        ------
        FileNotFoundError
            Si el archivo no existe
        ValueError
            Si el archivo no tiene las columnas requeridas
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Archivo de datos climáticos no encontrado: {csv_path}")
        
        # Cargar datos
        self.data = pd.read_csv(csv_path)
        
        # Validar columnas requeridas
        required_columns = ['date', 'tavg', 'prcp']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            raise ValueError(
                f"El archivo CSV debe contener las columnas: {required_columns}. "
                f"Faltan: {missing_columns}"
            )
        
        # Convertir columna de fecha a datetime
        self.data['date'] = pd.to_datetime(self.data['date'])
        
        # Establecer fecha como índice para búsqueda rápida
        self.data.set_index('date', inplace=True)
        
        # Manejar valores faltantes en tavg y prcp
        # Para tavg: interpolar linealmente
        if self.data['tavg'].isnull().any():
            self.data['tavg'] = self.data['tavg'].interpolate(method='linear')
        
        # Para prcp: rellenar con 0 (asumir sin lluvia)
        if self.data['prcp'].isnull().any():
            self.data['prcp'] = self.data['prcp'].fillna(0.0)
    
    def get_climate_data(self, date: datetime) -> Tuple[float, float]:
        """
        Obtiene datos climáticos para una fecha específica.
        
        Parameters
        ----------
        date : datetime
            Fecha para la cual obtener datos climáticos
            
        Returns
        -------
        Tuple[float, float]
            (temperatura en °C, precipitación en mm)
            
        Raises
        ------
        KeyError
            Si la fecha no está en los datos disponibles
        """
        # Normalizar la fecha (sin hora)
        date_normalized = pd.Timestamp(date.date())
        
        try:
            row = self.data.loc[date_normalized]
            temp = float(row['tavg'])
            precip = float(row['prcp'])
            return temp, precip
        except KeyError:
            raise KeyError(
                f"No hay datos climáticos disponibles para la fecha {date.date()}. "
                f"Rango de datos disponible: {self.data.index.min().date()} a {self.data.index.max().date()}"
            )
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Obtiene el rango de fechas disponible en los datos.
        
        Returns
        -------
        Tuple[datetime, datetime]
            (fecha_inicio, fecha_fin)
        """
        return self.data.index.min().to_pydatetime(), self.data.index.max().to_pydatetime()
    
    def has_date(self, date: datetime) -> bool:
        """
        Verifica si hay datos disponibles para una fecha.
        
        Parameters
        ----------
        date : datetime
            Fecha a verificar
            
        Returns
        -------
        bool
            True si hay datos para la fecha, False en caso contrario
        """
        date_normalized = pd.Timestamp(date.date())
        return date_normalized in self.data.index
