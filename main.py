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
import pandas as pd
import matplotlib.pyplot as plt

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel
from src.agents import EstadoSalud, EstadoMosquito


def cargar_configuracion(archivo_config: str) -> dict:
    """
    Carga configuración desde archivo YAML.
    
    Parameters
    ----------
    archivo_config : str
        Ruta al archivo de configuración
        
    Returns
    -------
    dict
        Diccionario con parámetros de configuración
    """
    with open(archivo_config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
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
    verbose: bool = True
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
        
    Returns
    -------
    DengueModel
        Modelo ejecutado con datos recolectados
    """
    # Crear modelo
    if verbose:
        print("=" * 70)
        print("SIMULACIÓN ABM DEL DENGUE - BUCARAMANGA")
        print("=" * 70)
        print(f"\n⚙️  Configuración:")
        print(f"   • Días a simular: {steps}")
        print(f"   • Grid: {width}×{height}")
        print(f"   • Población humana: {num_humanos}")
        print(f"   • Mosquitos adultos: {num_mosquitos}")
        print(f"   • Huevos iniciales: {num_huevos}")
        print(f"   • Infectados iniciales: {infectados_iniciales} humanos, {mosquitos_infectados_iniciales} mosquitos")
        print(f"   • Control LSM: {'✓' if usar_lsm else '✗'}")
        print(f"   • Control ITN/IRS: {'✓' if usar_itn_irs else '✗'}")
        print(f"   • Semilla: {seed if seed else 'Aleatoria'}")
        print("\n🚀 Iniciando simulación...\n")
    
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
        fecha_inicio=datetime.now(),
        seed=seed
    )
    
    # Ejecutar simulación
    for i in range(steps):
        modelo.step()
        
        # Mostrar progreso cada 5 días para seguimiento más detallado
        if verbose and (i + 1) % 5 == 0:
            infectados = modelo._contar_humanos_estado(EstadoSalud.INFECTADO)
            expuestos = modelo._contar_humanos_estado(EstadoSalud.EXPUESTO)
            recuperados = modelo._contar_humanos_estado(EstadoSalud.RECUPERADO)
            mosquitos_adultos = modelo._contar_mosquitos_adultos()
            mosquitos_inf = modelo._contar_mosquitos_estado(EstadoMosquito.INFECTADO)
            huevos = modelo._contar_huevos()
            susceptibles = modelo._contar_humanos_estado(EstadoSalud.SUSCEPTIBLE)
            
            print(f"📅 Día {i+1:3d}: "
                  f"👥 S:{susceptibles:3d} E:{expuestos:2d} I:{infectados:2d} R:{recuperados:3d} "
                  f"| 🦟 A:{mosquitos_adultos:3d} (I:{mosquitos_inf:2d}) H:{huevos:3d} "
                  f"| 🌡️{modelo.temperatura_actual:4.1f}°C 🌧️{modelo.precipitacion_actual:4.1f}mm")
    
    if verbose:
        print("\n" + "="*70)
        print("✅ Simulación completada!")
        print(f"📊 Resumen final:")
        print(f"   • Total infectados: {modelo._contar_humanos_estado(EstadoSalud.INFECTADO)}")
        print(f"   • Total recuperados: {modelo._contar_humanos_estado(EstadoSalud.RECUPERADO)}")
        print(f"   • Mosquitos adultos: {modelo._contar_mosquitos_adultos()}")
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
    parser.add_argument('--config', type=str, help='Archivo de configuración YAML')
    parser.add_argument('--steps', type=int, default=365, help='Días a simular')
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
    
    # Cargar configuración si se especifica
    if args.config:
        config = cargar_configuracion(args.config)
        # Sobrescribir con argumentos CLI si se proporcionan
        parametros = {
            'steps': args.steps if args.steps != 365 else config.get('simulacion', {}).get('duracion_dias', 365),
            'num_humanos': args.humanos if args.humanos != 100 else config.get('poblacion', {}).get('humanos', 100),
            'num_mosquitos': args.mosquitos if args.mosquitos != 200 else config.get('poblacion', {}).get('mosquitos_adultos', 200),
            'num_huevos': args.huevos if args.huevos != 50 else config.get('poblacion', {}).get('huevos', 50),
            'infectados_iniciales': args.infectados,
            'usar_lsm': args.lsm or config.get('control', {}).get('lsm', {}).get('activado', False),
            'usar_itn_irs': args.itn_irs or config.get('control', {}).get('itn_irs', {}).get('activado', False),
            'seed': args.seed
        }
    else:
        parametros = {
            'steps': args.steps,
            'num_humanos': args.humanos,
            'num_mosquitos': args.mosquitos,
            'num_huevos': args.huevos,
            'infectados_iniciales': args.infectados,
            'usar_lsm': args.lsm,
            'usar_itn_irs': args.itn_irs,
            'seed': args.seed
        }
    
    # Ejecutar simulación
    modelo = ejecutar_simulacion(**parametros)
    
    # Guardar resultados
    if not args.no_plots:
        guardar_resultados(modelo, args.output)


if __name__ == "__main__":
    main()
