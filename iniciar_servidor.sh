#!/bin/bash

echo "========================================"
echo "   🚀 Iniciando Servidor Alia IA"
echo "========================================"
echo ""

echo "Instalando dependencias..."
pip install -r requirements_registro.txt

echo ""
echo "Iniciando servidor..."
python registro_backend.py 