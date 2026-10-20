#!/bin/bash
set -e

echo "=== 1. Verificando entorno virtual ==="
if [ ! -d "venv"]; then
    echo "No existe el entorno virtual(venv). Creando..."
    python3 -m venv venv
else
    echo "Ya existe el entorno virtual(venv)"
fi

echo "=== 2. Activando entorno virtual ==="
source venv/bin/activate

echo "=== 3. Actualizando pip ==="
pip install --upgrade pip

echo "=== 4. Instalando dependencias de requirement.txt ==="
pip install -r requirements.txt

echo "=== 5. Verificando archivo de variables de entorno virtual(.env) ==="
if [! -f ".env"]; then
    echo "No existe archivo '.env'. Creando a partir de '.env.example'"
    cp .env.example .env
else
    echo "Ya existe el archivo '.env', no se modifica ninguna configuracion"
fi

echo "=== ¡Inicializacion completada con exito! ==="