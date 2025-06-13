#!/bin/bash

echo "🔧 Installing packages with prebuilt binaries..."

# Установим всё необходимое, избегая сборки pydantic-core
pip install --upgrade pip setuptools wheel

# Установим Pydantic и его зависимости строго через бинарные колёса
pip install --only-binary :all: pydantic==2.5.3

# Затем ставим всё остальное
pip install -r requirements.txt
