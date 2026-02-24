# UNS 社員台帳 Manager

> 🎯 Sistema de gestión completo para la nómina de empleados de UNS

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2️⃣ Opción A: Usar por Línea de Comandos
```bash
# Ver resumen
python src/shain_utils.py "tu_archivo.xlsm" summary

# Ver alertas de visa
python src/shain_utils.py "tu_archivo.xlsm" visa-alerts

# Buscar empleado
python src/shain_utils.py "tu_archivo.xlsm" search NGUYEN
```

### 2️⃣ Opción B: Usar Aplicación Web (Recomendado)
```bash
streamlit run src/app_shain_daicho.py
```

Abre `http://localhost:8501` en tu navegador.

### ✅ Verificación rápida recomendada
```bash
python -m compileall src main.py examples tests
python -m unittest discover -s tests -p "test_*.py"
python -m unittest tests.test_shain_daicho.TestShainDaicho.test_search_employee_case_insensitive
python src/shain_utils.py "tu_archivo.xlsm" summary
```

---

## 📦 Archivos Incluidos

| Archivo | Descripción |
|---------|------------|
| `shain_utils.py` | Módulo principal con toda la lógica |
| `app_shain_daicho.py` | Aplicación web Streamlit |
| `requirements.txt` | Dependencias Python |
| `config.yaml` | Configuración personalizable |
| `GUIA_COMPLETA.md` | Documentación completa |
| `README.md` | Este archivo |

---

## 🎨 Características Principales

### 📊 Dashboard
- Resumen ejecutivo de empleados
- Gráficos interactivos
- Estadísticas por categoría

### 👤 Búsqueda
- Buscar por nombre
- Ver datos completos del empleado
- Búsqueda parcial (case-insensitive)

### 🔔 Alertas de Visa
- Identificar visas próximas a vencer
- Clasificación por urgencia (🔴 🟠 🟡)
- Exportar reportes

### 💰 Análisis de Salarios
- Estadísticas de salarios (時給)
- Análisis de precio de facturación (請求単価)
- Análisis de ganancias (差額利益)

### 📈 Reportes Avanzados
- Análisis de edad
- Análisis de antigüedad
- Reportes personalizados

### 💾 Exportación
- Excel, JSON, CSV
- Descarga directa desde la interfaz

---

## 🔧 Uso Avanzado

### Integración en Python

```python
from shain_utils import ShainDaicho

# Cargar datos
sd = ShainDaicho('ruta/a/archivo.xlsm')
sd.load()

# Obtener estadísticas
stats = sd.get_summary_stats()
print(f"Total de empleados: {stats['total']['total']}")

# Buscar empleados
resultados = sd.search_employee('NGUYEN')
for emp in resultados:
    print(f"{emp['name']} - {emp['nationality']}")

# Ver alertas de visa
alertas = sd.get_visa_alerts(days=90)
for alerta in alertas[:5]:
    print(f"{alerta['alert_level']} {alerta['name']} - {alerta['expiry_date']}")

# Exportar datos
sd.export_active_employees('output.xlsx', format='excel')
```

### API REST (Futuro)

```bash
# Iniciar servidor API
python api_server.py

# Hacer consultas
curl http://localhost:5000/api/employees/1001
curl http://localhost:5000/api/visa-alerts
```

---

## 📊 Estadísticas de Datos

Basado en tu archivo actual:

| Categoría | Total | Activos | Inactivos |
|-----------|-------|---------|-----------|
| 派遣社員 | 1,066 | 398 | 668 |
| 請負社員 | 141 | 62 | 79 |
| スタッフ | 15 | 15 | 0 |
| **Total** | **1,222** | **475** | **747** |

---

## 🌍 Nacionalidad

| Nacionalidad | Cantidad |
|------------|----------|
| ベトナム | 1,028 |
| ブラジル | 46 |
| イントネシア | 71 |
| 日本 | 59 |
| ペルー | 3 |
| フィリピン | 1 |

---

## 💼 Empresas (派遣先) Principales

| Empresa | Empleados |
|---------|-----------|
| 高雄工業 岡山 | 185 |
| 高雄工業 静岡 | 141 |
| 高雄工業 海南第一 | 72 |
| 瑞陵精機 | 57 |
| 加藤木材工業 本社 | 57 |

---

## 🚀 Performance

| Métrica | Valor |
|---------|-------|
| Tiempo de carga | < 2 segundos |
| Tiempo de búsqueda | < 100 ms |
| Memoria utilizada | ~50 MB |
| Compatibilidad | Python 3.8+ |

---

## ⚠️ Requisitos Mínimos

- **Python:** 3.8 o superior
- **RAM:** 512 MB
- **Disco:** 100 MB (depende del tamaño del Excel)
- **Sistema Operativo:** Windows, macOS, Linux

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "File not found"
Verifica que la ruta del archivo sea correcta:
```bash
python shain_utils.py "/ruta/completa/a/archivo.xlsm" summary
```

### La aplicación web es lenta
```bash
# Limpiar caché
rm -rf .streamlit/cache
streamlit run app_shain_daicho.py --logger.level=warning
```

---

## 📚 Documentación Completa

Para más información detallada, ver `GUIA_COMPLETA.md`

---

## 🤝 Contribuciones

¿Tienes sugerencias o mejoras? Contacta a:
- 📧 Email: tech@uns.jp
- 📞 Teléfono: +81-XXX-XXXX

---

## 📄 Licencia

Uso privado de UNS. Todos los derechos reservados.

---

## 📝 Changelog

### v2.0.0 (30 Enero 2026)
- ✅ Código limpio y corregido
- ✅ Aplicación web completa
- ✅ Análisis avanzado
- ✅ Manejo robusto de errores
- ✅ Documentación completa

### v1.0.0 (Anterior)
- Versión inicial

---

**Última actualización:** 30 Enero 2026
**Versión:** 2.0.0
**Autor:** UNS Technical Team
