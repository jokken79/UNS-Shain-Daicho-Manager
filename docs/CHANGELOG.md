# Changelog

Todos los cambios notables se documentan en este archivo.

## [2.0.1] - 2026-02-24

### Added
- ✅ AGENTS.md con reglas operativas para agentes (build/lint/test/style y verificacion Context7)
- ✅ Suite de pruebas `unittest` en `tests/test_shain_daicho.py` con casos de carga, busqueda y exportacion
- ✅ Seccion de verificacion rapida en `docs/README.md`

### Changed
- ✅ `main.py` ahora implementa CLI completo (`summary`, `active`, `visa-alerts`, `search`, `export`) con codigos de salida
- ✅ `src/app_shain_daicho.py` usa rutas temporales cross-platform y cache por hash del archivo subido
- ✅ `src/shain_utils.py` mejora validacion de export y normalizacion de formatos/sufijos
- ✅ `requirements.txt` corrige `openpyxl` a una version instalable (`>=3.1.5,<4.0.0`)

### Fixed
- ✅ Export en Windows al eliminar dependencias de `/tmp`
- ✅ `calculate_profit_margin` ahora maneja correctamente valores numericos `0`
- ✅ Mensajes de error para argumentos faltantes o formatos no soportados en comandos CLI

## [2.0.0] - 2026-01-30

### Added
- ✅ Módulo Python limpio y optimizado (shain_utils.py)
- ✅ Aplicación web interactiva (Streamlit)
- ✅ 6 tabs principales en interfaz web
- ✅ Análisis de edad y antigüedad
- ✅ Alertas mejoradas de visa
- ✅ Exportación múltiple (Excel, JSON, CSV)
- ✅ Logging completo
- ✅ Type hints en todo el código
- ✅ Validación de datos
- ✅ Documentación completa

### Changed
- ✅ Corregidas sintaxis incorrecta
- ✅ Eliminado código duplicado
- ✅ Mejorado manejo de errores
- ✅ Optimizado para datasets grandes

### Fixed
- ✅ Staff status detection
- ✅ Error handling en todas funciones
- ✅ Validación de columnas faltantes

## [1.0.0] - 2026-01-15

### Initial Release
- Código base con errores de sintaxis
- Funcionalidades básicas
- Sin documentación completa
