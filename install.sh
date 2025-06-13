#!/bin/bash

# Установить зависимости вручную с колесами
pip install --upgrade pip setuptools wheel
pip install --only-binary pydantic-core pydantic==2.5.3
pip install -r requirements.txt
