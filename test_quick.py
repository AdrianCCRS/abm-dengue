"""
Script de prueba rápida del modelo ABM del Dengue.

Ejecuta una simulación corta (30 días) para verificar funcionamiento.

Uso:
    python test_quick.py
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.dengue_model import DengueModel
from src.agents import EstadoSalud, EstadoMosquito


def prueba_rapida():
    """Ejecuta una simulación de prueba de 30 días."""
    print("=" * 70)
    print("🧪 PRUEBA RÁPIDA DEL MODELO ABM DEL DENGUE")
    print("=" * 70)
    print("\n⚙️  Configuración de prueba:")
    print("   • Días: 30")
    print("   • Grid: 50×50")
    print("   • Humanos: 100")
    print("   • Mosquitos: 200")
    print("   • Infectados iniciales: 5 humanos, 2 mosquitos")
    print("\n🚀 Creando modelo...\n")
    
    # Crear modelo con parámetros reducidos
    modelo = DengueModel(
        width=50,
        height=50,
        num_humanos=100,
        num_mosquitos=200,
        num_huevos=50,
        infectados_iniciales=5,
        mosquitos_infectados_iniciales=2,
        usar_lsm=False,
        usar_itn_irs=False,
        seed=42  # Para reproducibilidad
    )
    
    print("✅ Modelo creado exitosamente!")
    print(f"   • Agentes totales: {len(modelo.schedule.agents)}")
    print(f"   • Humanos: {modelo.num_humanos}")
    print(f"   • Mosquitos adultos: {modelo._contar_mosquitos_adultos()}")
    print(f"   • Huevos: {modelo._contar_huevos()}")
    
    print("\n🔄 Ejecutando 30 días de simulación...\n")
    
    # Ejecutar 30 pasos
    for i in range(30):
        modelo.step()
        
        if (i + 1) % 10 == 0:
            s = modelo._contar_humanos_estado(EstadoSalud.SUSCEPTIBLE)
            e = modelo._contar_humanos_estado(EstadoSalud.EXPUESTO)
            inf = modelo._contar_humanos_estado(EstadoSalud.INFECTADO)
            r = modelo._contar_humanos_estado(EstadoSalud.RECUPERADO)
            mosq = modelo._contar_mosquitos_adultos()
            mosq_i = modelo._contar_mosquitos_estado(EstadoMosquito.INFECTADO)
            
            print(f"📅 Día {i+1:2d}: S={s:3d} E={e:3d} I={inf:3d} R={r:3d} | "
                  f"Mosquitos: {mosq:3d} (infectados: {mosq_i:2d}) | "
                  f"Temp: {modelo.temperatura_actual:.1f}°C")
    
    print("\n✅ Simulación completada!")
    
    # Resumen final
    print("\n📊 RESUMEN FINAL:")
    print("=" * 70)
    datos = modelo.datacollector.get_model_vars_dataframe()
    
    print(f"Susceptibles: {datos['Susceptibles'].iloc[-1]}")
    print(f"Expuestos: {datos['Expuestos'].iloc[-1]}")
    print(f"Infectados: {datos['Infectados'].iloc[-1]}")
    print(f"Recuperados: {datos['Recuperados'].iloc[-1]}")
    print(f"Pico de infectados: {datos['Infectados'].max()} (día {datos['Infectados'].idxmax()})")
    print(f"Mosquitos totales: {datos['Mosquitos_Total'].iloc[-1]}")
    print(f"Mosquitos infectados: {datos['Mosquitos_I'].iloc[-1]}")
    print(f"Huevos: {datos['Huevos'].iloc[-1]}")
    print(f"Temperatura promedio: {datos['Temperatura'].mean():.2f}°C")
    print(f"Precipitación total: {datos['Precipitacion'].sum():.1f}mm")
    print("=" * 70)
    
    print("\n✨ Prueba completada exitosamente!")
    print("   Puedes ejecutar la simulación completa con:")
    print("   python main.py --steps 365 --humanos 1000 --mosquitos 2000")


if __name__ == "__main__":
    try:
        prueba_rapida()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
