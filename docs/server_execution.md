# Guía de Ejecución en Servidores - ABM Dengue Paralelo

## Servidores Disponibles

### felix.uis.edu.co
- **CPUs**: 64 lógicos (4 sockets × 8 cores × 2 threads)
- **Arquitectura**: Nehalem
- **Recomendación**: 36 procesos (6×6 sectores)

### thor.uis.edu.co
- **CPUs**: 128 lógicos (4 sockets × 16 cores × 2 threads)
- **Arquitectura**: Haswell-EP
- **Recomendación**: 64 procesos (8×8 sectores)

## Comandos de Ejecución

### 1. Ejecución Básica (Automática)

El script detecta automáticamente los CPUs disponibles:

```bash
# En felix (usará 64 CPUs automáticamente)
python run_parallel.py --config config/default_config.yaml --steps 365

# En thor (usará 128 CPUs automáticamente)
python run_parallel.py --config config/default_config.yaml --steps 365
```

### 2. Especificar Número de Procesos

```bash
# Usar 36 procesos (recomendado para felix)
python run_parallel.py --config config/default_config.yaml --steps 365 --processes 36

# Usar 64 procesos (recomendado para thor)
python run_parallel.py --config config/default_config.yaml --steps 365 --processes 64
```

### 3. Especificar Número de Sectores

```bash
# 6×6 = 36 sectores (óptimo para felix)
python run_parallel.py --config config/default_config.yaml --steps 365 --sectors 6 6

# 8×8 = 64 sectores (óptimo para thor)
python run_parallel.py --config config/default_config.yaml --steps 365 --sectors 8 8
```

### 4. Con Validación de Conservación

```bash
# Activar validación (detecta race conditions)
python run_parallel.py --config config/default_config.yaml --steps 365 --validate
```

### 5. Modo Verbose (Debugging)

```bash
# Logging detallado
python run_parallel.py --config config/default_config.yaml --steps 365 --verbose
```

## Ejecución en Background

### Usando nohup

```bash
# Ejecutar en background y guardar log
nohup python run_parallel.py --config config/default_config.yaml --steps 365 > simulation.log 2>&1 &

# Ver progreso
tail -f simulation.log

# Ver proceso
ps aux | grep run_parallel
```

### Usando screen

```bash
# Crear sesión
screen -S dengue_sim

# Ejecutar simulación
python run_parallel.py --config config/default_config.yaml --steps 365

# Desconectar: Ctrl+A, D
# Reconectar: screen -r dengue_sim
```

### Usando tmux

```bash
# Crear sesión
tmux new -s dengue_sim

# Ejecutar simulación
python run_parallel.py --config config/default_config.yaml --steps 365

# Desconectar: Ctrl+B, D
# Reconectar: tmux attach -t dengue_sim
```

## Monitoreo de Recursos

### Ver uso de CPU

```bash
# Tiempo real
htop

# Por proceso
top -u $USER

# Resumen
mpstat -P ALL 1
```

### Ver uso de memoria

```bash
# Memoria total
free -h

# Por proceso
ps aux --sort=-%mem | head -20
```

## Optimización por Servidor

### felix.uis.edu.co (64 CPUs)

**Configuración recomendada**:
```bash
python run_parallel.py \
    --config config/default_config.yaml \
    --steps 365 \
    --processes 36 \
    --sectors 6 6 \
    --output results/felix_run
```

**Speedup esperado**: 25-30×  
**Tiempo estimado**: 365 días en ~15-20 minutos

### thor.uis.edu.co (128 CPUs)

**Configuración recomendada**:
```bash
python run_parallel.py \
    --config config/default_config.yaml \
    --steps 365 \
    --processes 64 \
    --sectors 8 8 \
    --output results/thor_run
```

**Speedup esperado**: 40-50×  
**Tiempo estimado**: 365 días en ~10-12 minutos

## Troubleshooting

### Error: "Too many open files"

```bash
# Aumentar límite de archivos abiertos
ulimit -n 4096
```

### Error: "Cannot allocate memory"

```bash
# Verificar memoria disponible
free -h

# Reducir número de procesos
python run_parallel.py --processes 24 ...
```

### Simulación muy lenta

```bash
# Verificar que está usando múltiples cores
htop  # Debe mostrar uso distribuido en CPUs

# Reducir sectores si hay mucho overhead
python run_parallel.py --sectors 4 4 ...
```

## Ejemplo Completo

```bash
# 1. Conectar al servidor
ssh usuario@felix.uis.edu.co

# 2. Activar entorno virtual
cd ~/abm-dengue
source .venv/bin/activate

# 3. Verificar CPUs
python -c "import multiprocessing; print(f'CPUs: {multiprocessing.cpu_count()}')"

# 4. Ejecutar simulación en background
nohup python run_parallel.py \
    --config config/default_config.yaml \
    --steps 365 \
    --processes 36 \
    --sectors 6 6 \
    --validate \
    --output results/felix_365days \
    > simulation.log 2>&1 &

# 5. Monitorear
tail -f simulation.log

# 6. Ver uso de recursos
htop
```

## Notas Importantes

⚠️ **Estado Actual**: La infraestructura de paralelización está implementada pero aún no integrada con DengueModel.

**Para usar ahora** (versión secuencial):
```bash
python main.py --config config/default_config.yaml --steps 365
```

**Próximamente** (versión paralela):
- Fase 2: Integración con DengueModel
- Fase 3: Testing y validación
- Estimado: 1-2 semanas
