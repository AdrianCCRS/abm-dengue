# -*- coding: utf-8 -*-
"""
Script principal para ejecutar la simulación ABM del Dengue.

Este script configura e inicia la simulación con parámetros configurables
desde línea de comandos o archivo YAML.

Uso:
    python main.py --config config/simulation_config.yaml
    python main.py --steps 365 --humanos 1000 --mosquitos 2000

Autor: Yeison Adrián Cáceres Torres, William Urrutia Torres, Jhon Anderson Vargas Gómez
Universidad Industrial de Santander - Simulación Digital F1
"""

import argparse
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel
from src.agents import EstadoSalud, EstadoMosquito


def cargar_configuracion(archivo_config: str) -> dict:
    """
    Carga configuración desde archivo YAML o JSON.
    
    Parameters
    ----------
    archivo_config : str
        Ruta al archivo de configuración
        
    Returns
    -------
    dict
        Diccionario con parámetros de configuración
    """
    import json
    from pathlib import Path
    ruta = Path(archivo_config)
    with ruta.open('r', encoding='utf-8') as f:
        if ruta.suffix.lower() in ('.yaml', '.yml'):
            config = yaml.safe_load(f)
        elif ruta.suffix.lower() == '.json':
            config = json.load(f)
        else:
            # Intentar YAML primero y luego JSON
            try:
                config = yaml.safe_load(f)
            except Exception:
                f.seek(0)
                config = json.load(f)
    return config


def ejecutar_simulacion(
    steps: int = 365,
    width: int = 50,
    height: int = 50,
    num_humanos: int = 100,
    num_mosquitos: int = 200,
    num_huevos: int = 50,
    infectados_iniciales: int = 5,
    mosquitos_infectados_iniciales: int = 2,
    usar_lsm: bool = False,
    usar_itn_irs: bool = False,
    seed: int = None,
    verbose: bool = True,
    config: Optional[dict] = None,
    climate_data_path: Optional[str] = None
) -> DengueModel:
    """
    Ejecuta la simulación del modelo ABM del Dengue.
    
    Parameters
    ----------
    steps : int, default=365
        Número de días a simular (1 año)
    width : int, default=50
        Ancho del grid
    height : int, default=50
        Alto del grid
    num_humanos : int, default=1000
        Número de humanos
    num_mosquitos : int, default=2000
        Número de mosquitos adultos iniciales
    num_huevos : int, default=500
        Número de huevos iniciales
    infectados_iniciales : int, default=10
        Humanos infectados al inicio
    mosquitos_infectados_iniciales : int, default=5
        Mosquitos infectados al inicio
    usar_lsm : bool, default=False
        Activar control larvario (LSM)
    usar_itn_irs : bool, default=False
        Activar protección con redes/insecticidas (ITN/IRS)
    seed : int, optional
        Semilla para reproducibilidad
    verbose : bool, default=True
        Mostrar progreso en consola
    config : dict, optional
        Diccionario de configuración completo del modelo
    climate_data_path : str, optional
        Ruta al archivo CSV con datos climáticos históricos
        
    Returns
    -------
    DengueModel
        Modelo ejecutado con datos recolectados
    """
    # Validar duración de la simulación con datos climáticos
    if climate_data_path:
        max_days = 365  # Limitado por los datos climáticos del CSV (2022)
        if steps > max_days:
            if verbose:
                print(f"⚠️  ADVERTENCIA: La simulación solicitada ({steps} días) excede el rango")
                print(f"   de datos climáticos disponibles ({max_days} días).")
                print(f"   Se limitará a {max_days} días.\n")
            steps = max_days
    
    # Crear modelo
    if verbose:
        print("=" * 70)
        print("SIMULACIÓN ABM DEL DENGUE - BUCARAMANGA")
        print("=" * 70)
        print(f"\n Configuración:")
        print(f"   • Días a simular: {steps}")
        print(f"   • Grid: {width}×{height}")
        print(f"   • Población humana: {num_humanos}")
        print(f"   • Mosquitos adultos: {num_mosquitos}")
        print(f"   • Huevos iniciales: {num_huevos}")
        print(f"   • Infectados iniciales: {infectados_iniciales} humanos, {mosquitos_infectados_iniciales} mosquitos")
        print(f"   • Control LSM: {'✓' if usar_lsm else '✗'}")
        print(f"   • Control ITN/IRS: {'✓' if usar_itn_irs else '✗'}")
        print(f"   • Semilla: {seed if seed else 'Aleatoria'}")
        print("\n Iniciando simulación...\n")
    
    modelo = DengueModel(
        width=width,
        height=height,
        num_humanos=num_humanos,
        num_mosquitos=num_mosquitos,
        num_huevos=num_huevos,
        infectados_iniciales=infectados_iniciales,
        mosquitos_infectados_iniciales=mosquitos_infectados_iniciales,
        usar_lsm=usar_lsm,
        usar_itn_irs=usar_itn_irs,
        fecha_inicio=datetime(2022, 1, 1),  # Usar fecha dentro del rango de datos del CSV
        seed=seed,
        config=config,
        climate_data_path=climate_data_path
    )
    
    # Ejecutar simulación
    for i in range(steps):
        modelo.step()
        
        # Mostrar progreso cada 10 días para seguimiento detallado
        if verbose and (i % 10 == 9 or i == 0 or i == steps - 1):
            infectados = modelo._contar_humanos_estado(EstadoSalud.INFECTADO)
            expuestos = modelo._contar_humanos_estado(EstadoSalud.EXPUESTO)
            recuperados = modelo._contar_humanos_estado(EstadoSalud.RECUPERADO)
            mosquitos_adultos = modelo._contar_mosquitos_adultos()
            mosquitos_inf = modelo._contar_mosquitos_estado(EstadoMosquito.INFECTADO)
            huevos = modelo._contar_huevos()
            susceptibles = modelo._contar_humanos_estado(EstadoSalud.SUSCEPTIBLE)
            
            # Obtener estadísticas de huevos (incluye infectados)
            eggs_stats = modelo.egg_manager.get_eggs_stats()
            huevos_infectados = eggs_stats['infectados']
            pct_huevos_inf = eggs_stats['porcentaje_infectados']
            
            # Obtener número de charcos temporales
            charcos = len(modelo.sitios_cria_temporales)
            
            # Imprimir reporte detallado
            print(f"Día {i+1:3d}/{steps}: "
                  f"H S:{susceptibles:4d} E:{expuestos:2d} I:{infectados:3d} R:{recuperados:4d} | "
                  f"M A:{mosquitos_adultos:5d} (I:{mosquitos_inf:4d}) H:{huevos:8d} | "
                  f"T:{modelo.temperatura_actual:4.1f}°C P:{modelo.precipitacion_actual:4.1f}mm", 
                  end='')
            
            # Mostrar huevos infectados si hay
            if huevos_infectados > 0:
                print(f" | H_inf:{huevos_infectados:5d} ({pct_huevos_inf:4.1f}%)", end='')
            
            # Mostrar charcos si hay
            if charcos > 0:
                print(f" | Charcos:{charcos:2d}", end='')
            
            print()  # Nueva línea
    
    if verbose:
        print("\n" + "="*70)
        print("Simulación completada!")
        
        # Estadísticas finales de huevos
        eggs_stats = modelo.egg_manager.get_eggs_stats()
        
        print(f"Resumen final:")
        print(f"   • Total infectados: {modelo._contar_humanos_estado(EstadoSalud.INFECTADO)}")
        print(f"   • Total recuperados: {modelo._contar_humanos_estado(EstadoSalud.RECUPERADO)}")
        print(f"   • Mosquitos adultos: {modelo._contar_mosquitos_adultos()}")
        print(f"   • Mosquitos infectados: {modelo._contar_mosquitos_estado(EstadoMosquito.INFECTADO)}")
        print(f"   • Huevos totales: {eggs_stats['total']}")
        print(f"   • Huevos infectados: {eggs_stats['infectados']} ({eggs_stats['porcentaje_infectados']:.2f}%)")
        print(f"   • Charcos activos: {len(modelo.sitios_cria_temporales)}")
        print(f"   • Tasa de ataque: {modelo._contar_humanos_estado(EstadoSalud.RECUPERADO)/num_humanos*100:.1f}%")
        print("="*70)
    
    return modelo


def guardar_resultados(modelo: DengueModel, directorio_salida: str = "results"):
    """
    Guarda los resultados de la simulación.
    
    Genera:
    - CSV con datos temporales
    - Gráficas de series de tiempo
    - Resumen estadístico
    
    Parameters
    ----------
    modelo : DengueModel
        Modelo ejecutado
    directorio_salida : str, default="results"
        Directorio donde guardar resultados
    """
    # Crear directorio si no existe
    output_dir = Path(directorio_salida)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Obtener datos del modelo
    datos = modelo.datacollector.get_model_vars_dataframe()
    
    # Timestamp para archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Guardar CSV
    csv_path = output_dir / f"simulacion_{timestamp}.csv"
    datos.to_csv(csv_path, index=True)
    print(f"\n💾 Datos guardados en: {csv_path}")
    
    # Crear gráficas
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle('Simulación ABM del Dengue - Bucaramanga', fontsize=16, fontweight='bold')
    
    # 1. Estados SEIR de humanos
    axes[0, 0].plot(datos.index, datos['Susceptibles'], label='Susceptibles', color='blue', linewidth=2)
    axes[0, 0].plot(datos.index, datos['Expuestos'], label='Expuestos', color='orange', linewidth=2)
    axes[0, 0].plot(datos.index, datos['Infectados'], label='Infectados', color='red', linewidth=2)
    axes[0, 0].plot(datos.index, datos['Recuperados'], label='Recuperados', color='green', linewidth=2)
    axes[0, 0].set_xlabel('Días')
    axes[0, 0].set_ylabel('Número de humanos')
    axes[0, 0].set_title('Estados SEIR - Población Humana')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Estados SI de mosquitos
    axes[0, 1].plot(datos.index, datos['Mosquitos_S'], label='Susceptibles', color='blue', linewidth=2)
    axes[0, 1].plot(datos.index, datos['Mosquitos_I'], label='Infectados', color='red', linewidth=2)
    axes[0, 1].plot(datos.index, datos['Mosquitos_Total'], label='Total', color='black', linewidth=2, linestyle='--')
    axes[0, 1].set_xlabel('Días')
    axes[0, 1].set_ylabel('Número de mosquitos')
    axes[0, 1].set_title('Estados SI - Población de Mosquitos')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Infectados humanos (detalle)
    axes[1, 0].plot(datos.index, datos['Infectados'], color='red', linewidth=2)
    axes[1, 0].fill_between(datos.index, datos['Infectados'], alpha=0.3, color='red')
    axes[1, 0].set_xlabel('Días')
    axes[1, 0].set_ylabel('Infectados')
    axes[1, 0].set_title('Infectados Humanos (Curva Epidémica)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Temperatura y precipitación
    ax_temp = axes[1, 1]
    ax_precip = ax_temp.twinx()
    
    line1 = ax_temp.plot(datos.index, datos['Temperatura'], color='orange', linewidth=2, label='Temperatura')
    ax_temp.set_xlabel('Días')
    ax_temp.set_ylabel('Temperatura (°C)', color='orange')
    ax_temp.tick_params(axis='y', labelcolor='orange')
    
    line2 = ax_precip.plot(datos.index, datos['Precipitacion'], color='blue', linewidth=1, alpha=0.6, label='Precipitación')
    ax_precip.set_ylabel('Precipitación (mm)', color='blue')
    ax_precip.tick_params(axis='y', labelcolor='blue')
    
    ax_temp.set_title('Variables Climáticas')
    ax_temp.grid(True, alpha=0.3)
    
    # Leyenda combinada
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax_temp.legend(lines, labels, loc='upper left')
    
    # 5. Huevos y mosquitos adultos
    axes[2, 0].plot(datos.index, datos['Huevos'], label='Huevos', color='purple', linewidth=2)
    axes[2, 0].plot(datos.index, datos['Mosquitos_Total'], label='Adultos', color='brown', linewidth=2)
    axes[2, 0].set_xlabel('Días')
    axes[2, 0].set_ylabel('Cantidad')
    axes[2, 0].set_title('Dinámica de Mosquitos (Ciclo de Vida)')
    axes[2, 0].legend()
    axes[2, 0].grid(True, alpha=0.3)
    
    # 6. Estrategias de control
    axes[2, 1].plot(datos.index, datos['LSM_Activo'].astype(int), label='LSM', color='green', linewidth=2, drawstyle='steps-post')
    axes[2, 1].plot(datos.index, datos['ITN_IRS_Activo'].astype(int), label='ITN/IRS', color='blue', linewidth=2, drawstyle='steps-post')
    axes[2, 1].set_xlabel('Días')
    axes[2, 1].set_ylabel('Activo (1) / Inactivo (0)')
    axes[2, 1].set_title('Estrategias de Control')
    axes[2, 1].set_ylim([-0.1, 1.1])
    axes[2, 1].legend()
    axes[2, 1].grid(True, alpha=0.3)
    
    # Ajustar layout y guardar
    plt.tight_layout()
    plot_path = output_dir / f"graficas_{timestamp}.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Gráficas guardadas en: {plot_path}")
    
    # Mostrar gráficas
    plt.show()
    
    # Resumen estadístico
    print("\n📈 RESUMEN ESTADÍSTICO:")
    print("=" * 70)
    print(f"Pico de infectados: {datos['Infectados'].max()} (día {datos['Infectados'].idxmax()})")
    print(f"Total de recuperados al final: {datos['Recuperados'].iloc[-1]}")
    print(f"Ataque rate: {datos['Recuperados'].iloc[-1] / (datos['Susceptibles'].iloc[0] + datos['Infectados'].iloc[0]) * 100:.2f}%")
    print(f"Mosquitos al inicio: {datos['Mosquitos_Total'].iloc[0]}")
    print(f"Mosquitos al final: {datos['Mosquitos_Total'].iloc[-1]}")
    print(f"Temperatura promedio: {datos['Temperatura'].mean():.2f}°C (±{datos['Temperatura'].std():.2f})")
    print(f"Precipitación total: {datos['Precipitacion'].sum():.2f}mm")
    print("=" * 70)


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Simulación ABM del Dengue en Bucaramanga',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Argumentos de línea de comandos
    parser.add_argument('--config', type=str, help='Archivo de configuración YAML/JSON')
    # Default=None para detectar si el usuario lo pasó explícitamente
    parser.add_argument('--steps', type=int, default=None, help='Días a simular (CLI tiene prioridad sobre archivo)')
    parser.add_argument('--humanos', type=int, default=100, help='Número de humanos')
    parser.add_argument('--mosquitos', type=int, default=200, help='Número de mosquitos')
    parser.add_argument('--huevos', type=int, default=50, help='Número de huevos iniciales')
    parser.add_argument('--infectados', type=int, default=5, help='Infectados iniciales')
    parser.add_argument('--lsm', action='store_true', help='Activar control LSM')
    parser.add_argument('--itn-irs', action='store_true', help='Activar control ITN/IRS')
    parser.add_argument('--seed', type=int, help='Semilla para reproducibilidad')
    parser.add_argument('--output', type=str, default='results', help='Directorio de salida')
    parser.add_argument('--no-plots', action='store_true', help='No mostrar gráficas')
    
    args = parser.parse_args()
    
    # Ruta absoluta al archivo CSV de datos climáticos
    project_dir = Path(__file__).parent
    climate_csv_path = str(project_dir / 'data' / 'raw' / 'datos_climaticos_2022.csv')
    
    # Cargar configuración si se especifica
    if args.config:
        cfg = cargar_configuracion(args.config)
        # Determinar parámetros de simulación desde config nueva (simulation) o legacy (simulacion/poblacion/control)
        if 'simulation' in cfg:
            sim = cfg['simulation']
            # Prioridad: CLI (--steps) > archivo > default 365
            steps = args.steps if args.steps is not None else sim.get('steps', 365)
            width = sim.get('width', 150)
            height = sim.get('height', 150)
            num_humanos = sim.get('num_humanos', args.humanos)
            num_mosquitos = sim.get('num_mosquitos', args.mosquitos)
            num_huevos = sim.get('num_huevos', args.huevos)
            infectados_iniciales = sim.get('infectados_iniciales', args.infectados)
            mosquitos_infectados_iniciales = sim.get('mosquitos_infectados_iniciales', 2)
            usar_lsm = sim.get('usar_lsm', args.lsm)
            usar_itn_irs = sim.get('usar_itn_irs', args.itn_irs)
            seed = sim.get('seed', args.seed)
            parametros = {
                'steps': steps,
                'width': width,
                'height': height,
                'num_humanos': num_humanos,
                'num_mosquitos': num_mosquitos,
                'num_huevos': num_huevos,
                'infectados_iniciales': infectados_iniciales,
                'mosquitos_infectados_iniciales': mosquitos_infectados_iniciales,
                'usar_lsm': usar_lsm,
                'usar_itn_irs': usar_itn_irs,
                'seed': seed,
                'config': cfg,
                'climate_data_path': climate_csv_path
            }
        else:
            # Compatibilidad con esquema legacy
            simulacion = cfg.get('simulacion', {})
            poblacion = cfg.get('poblacion', {})
            control = cfg.get('control', {})
            # Prioridad: CLI (--steps) > archivo > default 365
            steps = args.steps if args.steps is not None else simulacion.get('duracion_dias', 365)
            parametros = {
                'steps': steps,
                'width': simulacion.get('width', 150),
                'height': simulacion.get('height', 150),
                'num_humanos': poblacion.get('humanos', args.humanos),
                'num_mosquitos': poblacion.get('mosquitos_adultos', args.mosquitos),
                'num_huevos': poblacion.get('huevos', args.huevos),
                'infectados_iniciales': args.infectados,
                'mosquitos_infectados_iniciales': 2,
                'usar_lsm': control.get('lsm', {}).get('activado', args.lsm),
                'usar_itn_irs': control.get('itn_irs', {}).get('activado', args.itn_irs),
                'seed': args.seed,
                'config': cfg,
                'climate_data_path': climate_csv_path
            }
    else:
        # Sin archivo: usar CLI o default 365
        parametros = {
            'steps': args.steps if args.steps is not None else 365,
            'width': 150,
            'height': 150,
            'num_humanos': args.humanos,
            'num_mosquitos': args.mosquitos,
            'num_huevos': args.huevos,
            'infectados_iniciales': args.infectados,
            'mosquitos_infectados_iniciales': 2,
            'usar_lsm': args.lsm,
            'usar_itn_irs': args.itn_irs,
            'seed': args.seed,
            'config': None,
            'climate_data_path': climate_csv_path
        }
    
    # Ejecutar simulación
    modelo = ejecutar_simulacion(**parametros)
    
    # Guardar resultados
    if not args.no_plots:
        guardar_resultados(modelo, args.output)


if __name__ == "__main__":
    main()
