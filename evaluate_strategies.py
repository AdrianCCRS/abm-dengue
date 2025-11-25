import argparse
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from tqdm import tqdm
import numpy as np

from src.model.dengue_model import DengueModel

def cargar_configuracion(ruta_config):
    with open(ruta_config, 'r') as f:
        return yaml.safe_load(f)

def ejecutar_escenario(nombre, config_base, overrides, steps, seed, climate_csv):
    print(f"\n--- Ejecutando Escenario: {nombre} ---")
    
    # Copiar configuración base y aplicar overrides
    config = config_base.copy()
    
    # Asegurar que la sección control existe
    if 'control' not in config:
        config['control'] = {}
        
    # Aplicar overrides
    for key, value in overrides.items():
        if key.startswith('control.'):
            # Manejar claves anidadas tipo 'control.usar_lsm' (aunque en el modelo son atributos directos)
            # En el modelo, los flags son atributos directos pasados al constructor o leídos del config
            # Ajustamos según cómo DengueModel lee la configuración
            pass
        config[key] = value
        
    # Instanciar modelo
    # DengueModel acepta un argumento 'config' con el diccionario completo
    # También pasamos    # Ensure climate data path is provided for the model
    # Ensure climate_data_path is set below
    # Asegurar ruta de datos climáticos
    config['climate_data_path'] = climate_csv

    # Instanciar modelo
    modelo = DengueModel(seed=seed, config=config, climate_data_path=climate_csv)

    
    datos_diarios = []
    
    # Ejecutar simulación
    for step in tqdm(range(steps), desc=f"Simulando {nombre}"):
        modelo.step()
        
        # Recolectar métricas
        # Obtener métricas del DataCollector
        df_metrics = modelo.datacollector.get_model_vars_dataframe()
        ultimo = df_metrics.iloc[-1]
        infectados = ultimo['Infectados']
        mosquitos = ultimo['Mosquitos_Total']
        mosquitos_inf = ultimo['Mosquitos_I']
        
        datos_diarios.append({
            'Dia': step,
            'Escenario': nombre,
            'Infectados': infectados,
            'Mosquitos_Total': mosquitos,
            'Mosquitos_Infectados': mosquitos_inf,
            'Lluvia': modelo.precipitacion_actual,
            'Temperatura': modelo.temperatura_actual
        })
        
    return pd.DataFrame(datos_diarios)

def main():
    parser = argparse.ArgumentParser(description="Evaluar estrategias de control de dengue")
    parser.add_argument("--config", default="config/default_config.yaml", help="Ruta al archivo de configuración base")
    parser.add_argument("--steps", type=int, default=364, help="Número de pasos (días) a simular")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad")
    parser.add_argument("--climate_csv", default="data/raw/datos_climaticos_2022.csv", help="Ruta al archivo CSV de datos climáticos")
    parser.add_argument("--output_dir", default="results/evaluation", help="Directorio de salida")
    
    args = parser.parse_args()
    
    # Crear directorio de salida con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # Cargar configuración base
    config_base = cargar_configuracion(args.config)
    # Añadir ruta de datos climáticos al config base
    config_base['climate_data_path'] = args.climate_csv
    
    # Definir escenarios
    # Modificamos los flags directamente en el diccionario de configuración
    escenarios = [
        {
            "nombre": "1. Baseline (Sin Control)",
            "overrides": {
                "usar_lsm": False,
                "usar_itn_irs": False
            }
        },
        {
            "nombre": "2. Solo LSM",
            "overrides": {
                "usar_lsm": True,
                "usar_itn_irs": False
            }
        },
        {
            "nombre": "3. Solo ITN/IRS",
            "overrides": {
                "usar_lsm": False,
                "usar_itn_irs": True
            }
        },
        {
            "nombre": "4. Combinado (LSM + ITN/IRS)",
            "overrides": {
                "usar_lsm": True,
                "usar_itn_irs": True
            }
        }
    ]
    
    # Ejecutar todos los escenarios
    resultados_totales = []
    metricas_resumen = []
    
    for escenario in escenarios:
        df_escenario = ejecutar_escenario(
            escenario["nombre"], 
            config_base, 
            escenario["overrides"], 
            args.steps, 
            args.seed,
            args.climate_csv
        )
        resultados_totales.append(df_escenario)
        
        # Calcular métricas resumen
        total_infectados_acum = df_escenario['Infectados'].sum() # Aproximación (esto es prevalencia diaria sumada, no incidencia)
        # Mejor métrica: Pico máximo
        pico_infectados = df_escenario['Infectados'].max()
        dia_pico = df_escenario['Infectados'].idxmax() # Ojo, esto es índice relativo al df
        dia_pico_real = df_escenario.loc[dia_pico, 'Dia']
        
        mosquitos_final = df_escenario['Mosquitos_Total'].iloc[-1]
        
        metricas_resumen.append({
            'Escenario': escenario["nombre"],
            'Pico_Infectados': pico_infectados,
            'Dia_Pico': dia_pico_real,
            'Mosquitos_Final': mosquitos_final,
            'Mosquitos_Infectados_Final': df_escenario['Mosquitos_Infectados'].iloc[-1]
        })
    
    df_resultados = pd.concat(resultados_totales)
    df_resumen = pd.DataFrame(metricas_resumen)
    
    # Calcular reducción respecto al baseline
    baseline_pico = df_resumen.loc[0, 'Pico_Infectados']
    df_resumen['Reduccion_Pico_%'] = ((baseline_pico - df_resumen['Pico_Infectados']) / baseline_pico * 100).round(2)
    
    print("\n--- Resumen de Resultados ---")
    print(df_resumen)
    
    # Guardar datos
    df_resultados.to_csv(os.path.join(output_dir, "series_temporales.csv"), index=False)
    df_resumen.to_csv(os.path.join(output_dir, "resumen_metricas.csv"), index=False)
    
    # Generar Gráficas
    plt.figure(figsize=(12, 10))
    
    # 1. Curvas de Infectados
    plt.subplot(2, 1, 1)
    for nombre in df_resultados['Escenario'].unique():
        datos = df_resultados[df_resultados['Escenario'] == nombre]
        plt.plot(datos['Dia'], datos['Infectados'], label=nombre, linewidth=2)
    
    plt.title('Dinámica de Infección Humana por Escenario')
    plt.ylabel('Número de Infectados')
    plt.xlabel('Día')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. Curvas de Mosquitos
    plt.subplot(2, 1, 2)
    for nombre in df_resultados['Escenario'].unique():
        datos = df_resultados[df_resultados['Escenario'] == nombre]
        plt.plot(datos['Dia'], datos['Mosquitos_Total'], label=nombre, linewidth=2)
        
    plt.title('Población de Mosquitos por Escenario')
    plt.ylabel('Total Mosquitos')
    plt.xlabel('Día')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "comparativa_estrategias.png"), dpi=300)
    print(f"\nResultados guardados en: {output_dir}")

if __name__ == "__main__":
    main()
