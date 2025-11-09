# Resumen de Cambios: Eliminación de API Meteostat y Uso de Datos CSV

## Fecha
9 de noviembre de 2025

## Descripción General
Se eliminaron todas las referencias a la API de Meteostat del proyecto y se implementó un sistema de carga de datos climáticos desde archivos CSV. Esto permite utilizar datos climáticos históricos almacenados localmente sin depender de servicios externos.

## Cambios Realizados

### 1. Nuevo Módulo de Datos Climáticos
**Archivo creado:** `src/utils/climate_data.py`

- Implementa la clase `ClimateDataLoader` que:
  - Carga datos climáticos desde archivos CSV
  - Valida la existencia de columnas requeridas (date, tavg, prcp)
  - Maneja valores faltantes (interpolación para temperatura, ceros para precipitación)
  - Proporciona acceso rápido a datos por fecha mediante indexación
  - Ofrece métodos para verificar disponibilidad de fechas y rangos de datos

### 2. Modificaciones en el Modelo Principal
**Archivo modificado:** `src/model/dengue_model.py`

#### Imports actualizados:
- Eliminado: `import requests` (ya no se necesita para API)
- Agregado: `from ..utils.climate_data import ClimateDataLoader`

#### Nuevos parámetros del constructor:
- `climate_data_path: Optional[str] = None` - Ruta al archivo CSV con datos climáticos

#### Nuevos atributos:
- `self.climate_loader: ClimateDataLoader` - Instancia del cargador de datos
- `self.use_csv_climate: bool` - Indica si se están usando datos desde CSV

#### Métodos modificados:
- **`_actualizar_clima()`**: Ahora intenta obtener datos desde CSV primero, con fallback a modelo sintético
- **Eliminado `_obtener_clima_meteostat()`**: Ya no se necesita este método
- **`_cargar_configuracion()`**: Ahora lee configuración de datos CSV desde el archivo YAML

#### Lógica de inicialización:
1. Inicializa `climate_loader` y `use_csv_climate` antes de cargar configuración
2. Si se proporciona `climate_data_path` directamente, lo carga
3. Si no, intenta cargar desde configuración YAML
4. Valida que las fechas de simulación estén en el rango de datos disponibles
5. Si hay errores, usa modelo sintético como fallback

### 3. Actualización de Configuración
**Archivo modificado:** `config/simulation_config.yaml`

Sección `climate` actualizada:
```yaml
climate:
  use_csv: true                      # Usar datos climáticos desde CSV
  csv_path: "data/raw/datos_climaticos_2022.csv"  # Ruta al archivo CSV
  default_temperature: 24.0          # °C (valor por defecto si no hay datos)
  default_precipitation: 3.0         # mm (valor por defecto si no hay datos)
  temperature_effect_on_breeding: true
  rain_effect_on_breeding: true
```

Eliminados:
- `use_api`
- `api_name`
- `location` (latitude, longitude)

### 4. Documentación Actualizada

#### README.md
- Cambió "API Meteostat" por "Datos históricos climáticos desde CSV"

#### docs/PARAMETROS_MODELO.md
- Actualizada referencia de datos climáticos

#### docs/CONFIGURACION_PARAMETROS.md
- Actualizada sección de configuración de clima
- Eliminadas referencias a API Meteostat

#### RESUMEN_PROYECTO.md
- Actualizada descripción de `climate_data.py`
- Cambiada fuente de datos de "Meteostat" a "CSV histórico"
- Actualizada lista de tecnologías

#### GUIA_DESARROLLO.md
- Marcada como completada la tarea de implementar cargador de datos climáticos
- Eliminada referencia a API Meteostat de recursos

#### INICIO_RAPIDO.md
- Actualizado estado de implementación de `climate_data.py`

#### .copilot-context.json
- Actualizada descripción de fuentes de datos

### 5. Datos Climáticos
**Archivo copiado:** `data/raw/datos_climaticos_2022.csv`

- Contiene datos climáticos de Bucaramanga para el año 2022
- Columnas: date, tavg, tmin, tmax, prcp, snow, wdir, wspd, wpgt, pres, tsun
- El sistema utiliza principalmente: date, tavg, prcp
- 365 días de datos (2022-01-01 a 2022-12-31)

### 6. Script de Prueba
**Archivo creado:** `test_climate_csv.py`

Implementa tres pruebas:
1. **Cargador de datos**: Verifica la carga correcta del CSV ✅
2. **Modelo con CSV**: Prueba el modelo usando datos CSV directamente
3. **Modelo con configuración**: Prueba el modelo usando configuración YAML

**Nota**: Las pruebas 2 y 3 fallan debido a un problema no relacionado con el sistema de clima (incompatibilidad con la versión de Mesa), pero la prueba 1 confirma que el cargador de datos funciona correctamente.

## Archivos Eliminados/No Necesarios

- No se eliminaron archivos físicamente, pero se removieron todas las referencias a Meteostat
- El archivo `requirements.txt` no requería cambios (no tenía dependencia de meteostat)

## Funcionalidad del Sistema de Datos CSV

### Ventajas:
1. **Sin dependencia externa**: No requiere conexión a internet
2. **Datos reales**: Usa datos históricos verificados
3. **Reproducibilidad**: Las simulaciones son completamente reproducibles
4. **Flexibilidad**: Fácil cambiar entre diferentes conjuntos de datos
5. **Rendimiento**: Acceso más rápido que llamadas a API
6. **Fallback robusto**: Si no hay datos, usa modelo sintético automáticamente

### Uso:
```python
# Opción 1: Pasar ruta directamente
model = DengueModel(
    fecha_inicio=datetime(2022, 1, 1),
    climate_data_path="data/raw/datos_climaticos_2022.csv"
)

# Opción 2: Usar configuración YAML
model = DengueModel(
    fecha_inicio=datetime(2022, 1, 1),
    config_file="config/simulation_config.yaml"
)

# Opción 3: Modelo sintético (sin CSV)
model = DengueModel(
    fecha_inicio=datetime(2024, 1, 1)
    # No se proporciona climate_data_path, usa modelo sintético
)
```

### Manejo de Errores:
- **Archivo no encontrado**: Imprime advertencia y usa modelo sintético
- **Fecha fuera de rango**: Imprime advertencia y usa modelo sintético
- **Columnas faltantes**: Lanza ValueError con mensaje claro
- **Valores nulos**: Interpola temperatura, asume 0mm para precipitación

## Impacto en Simulaciones

- Las simulaciones ahora usarán datos climáticos reales de 2022 por defecto
- La temperatura y precipitación varían según los datos históricos reales
- Esto afectará:
  - Reproducción de mosquitos (dependiente de temperatura y lluvia)
  - Maduración de huevos (dependiente de temperatura)
  - Ciclo de vida de mosquitos (afectado por clima)

## Próximos Pasos Sugeridos

1. Agregar más archivos CSV con datos de otros años
2. Implementar selección de año en la configuración
3. Crear visualizaciones de series temporales climáticas
4. Documentar cómo obtener datos climáticos de otras fuentes
5. Resolver el problema de compatibilidad con Mesa para ejecutar pruebas completas

## Verificación

✅ Cargador de datos climáticos funciona correctamente
✅ Todas las referencias a Meteostat eliminadas
✅ Documentación actualizada
✅ Configuración actualizada
✅ Datos CSV copiados y accesibles

## Contacto

**Equipo:**
- Yeison Adrián Cáceres Torres
- William Urrutia Torres
- Jhon Anderson Vargas Gómez

**Universidad Industrial de Santander**
**Simulación Digital F1**
