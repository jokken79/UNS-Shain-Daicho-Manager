# 🚀 UNS 社員台帳 Manager - Quick Start Guide

## ⚡ 30 segundos - Empezar

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar aplicación web
streamlit run app_shain_daicho.py

# 3. Abre en navegador
# http://localhost:8501
```

---

## 📱 Interfaz Web (Recomendado)

### Paso 1: Cargar archivo
1. Haz clic en "Upload 社員台帳 Excel file" en el sidebar izquierdo
2. Selecciona tu archivo `.xlsm`
3. Espera 2 segundos para que cargue

### Paso 2: Explorar pestañas
```
📊 Dashboard    → Resumen visual + gráficos
👤 Search       → Buscar empleados por nombre
🔔 Visa Alerts  → Alertas de vencimiento de visa
💰 Salary      → Análisis de salarios
📈 Reports     → Reportes avanzados
⚙️ Export      → Descargar datos
```

---

## 💻 Línea de Comandos (Rápido)

### Ver resumen
```bash
python shain_utils.py "archivo.xlsm" summary
```
**Output:** JSON con estadísticas completas

### Ver alertas de visa
```bash
python shain_utils.py "archivo.xlsm" visa-alerts
```
**Output:** Lista de empleados con visa próxima a vencer

### Buscar empleado
```bash
python shain_utils.py "archivo.xlsm" search NGUYEN
```
**Output:** Lista de empleados con "NGUYEN" en el nombre

### Exportar datos
```bash
python shain_utils.py "archivo.xlsm" export excel
```
**Output:** Archivo `export_YYYYMMDD_HHMMSS.xlsx`

---

## 🐍 Usar en Python

### Instalación como módulo
```python
from shain_utils import ShainDaicho

# Cargar datos
sd = ShainDaicho('archivo.xlsm')
sd.load()

# Resumen
stats = sd.get_summary_stats()
print(f"Total: {stats['total']['total']}")

# Buscar
results = sd.search_employee('NGUYEN')
for emp in results:
    print(f"{emp['name']} ({emp['category']})")

# Visa alerts
alerts = sd.get_visa_alerts(days=90)
for alert in alerts[:5]:
    print(f"{alert['alert_level']} {alert['name']}")

# Exportar
sd.export_active_employees('output.xlsx', format='excel')
```

---

## 📊 Ejemplos Prácticos

### Ejemplo 1: Contar empleados por nacionalidad
```python
sd = ShainDaicho('archivo.xlsm')
sd.load()
nat = sd.get_nationality_breakdown()
print(nat['派遣'])  # {'ベトナム': 976, 'ブラジル': 43, ...}
```

### Ejemplo 2: Ver empleados activos
```python
active = sd.get_active_employees('派遣')
print(f"Activos: {len(active)}")
print(active[['社員№', '氏名', '時給']])
```

### Ejemplo 3: Calcular margen de ganancia
```python
profit = sd.calculate_profit_margin(employee_id=1001)
print(f"Margen: {profit['margin_rate_percent']}%")
```

### Ejemplo 4: Filtrar por edad
```python
active = sd.get_active_employees('派遣')
young = active[active['年齢'] < 30]
print(f"Empleados <30 años: {len(young)}")
```

### Ejemplo 5: Análisis de salarios
```python
salary = sd.get_salary_stats()
print(f"Salario promedio: ¥{salary['時給']['avg']:.0f}")
print(f"Rango: ¥{salary['時給']['min']:.0f} - ¥{salary['時給']['max']:.0f}")
```

---

## 🎯 Casos de Uso Comunes

### 1. "Necesito ver quiénes tienen visa próxima a vencer"
```bash
python shain_utils.py "archivo.xlsm" visa-alerts
```
Ve los empleados con 🔴 (URGENT) - vencimiento ≤30 días

### 2. "Quiero exportar lista de empleados activos"
Usa la web → Tab "Export" → Elige formato (Excel/CSV/JSON) → Descarga

### 3. "Necesito buscar a un empleado específico"
```bash
python shain_utils.py "archivo.xlsm" search "NOMBRE"
```

### 4. "Quiero ver gráficos de distribución"
Inicia la web y ve el Tab "Dashboard"

### 5. "Necesito análisis de salarios"
Web → Tab "Salary Analysis" → Ve gráficos y estadísticas

---

## 📈 Datos Actuales

```
派遣社員   (Dispatch):      1,066 empleados    398 activos
請負社員   (Contract):        141 empleados     62 activos
スタッフ  (Staff):            15 empleados     15 activos
──────────────────────────────────────────────────────
TOTAL:                      1,222 empleados    475 activos (39%)
```

### Top nacionalidades
- Vietnam: 1,028 (84%)
- Indonesia: 71 (6%)
- Japan: 59 (5%)

### Top empresas (派遣先)
- 高雄工業 岡山: 185 empleados
- 高雄工業 静岡: 141 empleados
- 高雄工業 海南第一: 72 empleados

### Salarios (派遣社員 activos)
- Mínimo: ¥1,100/hora
- Máximo: ¥1,655/hora
- Promedio: ¥1,349/hora
- Margen promedio: ¥463/hora

---

## ❓ FAQ - Preguntas Frecuentes

### P: ¿Qué Python necesito?
R: Python 3.8 o superior

### P: ¿Puedo usar con otros archivos Excel?
R: Sí, solo asegúrate que tengan las columnas requeridas (社員№, 氏名, etc.)

### P: ¿Es gratis?
R: Sí, código abierto para uso interno de UNS

### P: ¿Puedo modificar el código?
R: Sí, toda la documentación está incluida

### P: ¿Se pueden automatizar alertas?
R: Sí, ver GUIA_COMPLETA.md → "Automatización"

### P: ¿Funciona offline?
R: Sí, no requiere internet (excepto Streamlit online)

### P: ¿Qué hago si hay error?
R: Ver GUIA_COMPLETA.md → "Troubleshooting"

### P: ¿Puedo integrar con otros sistemas?
R: Sí, ver GUIA_COMPLETA.md → "Integración con APIs"

---

## 🔧 Troubleshooting Rápido

### Error: "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### Error: "File not found"
Usa ruta completa:
```bash
python shain_utils.py "/ruta/completa/archivo.xlsm" summary
```

### La web es lenta
```bash
rm -rf .streamlit/cache
streamlit run app_shain_daicho.py --logger.level=warning
```

### No se cargan datos
1. Verifica que el archivo sea .xlsx o .xlsm
2. Verifica que tenga las hojas: DBGenzaiX, DBUkeoiX, DBStaffX
3. Ver GUIA_COMPLETA.md para más detalles

---

## 📁 Estructura de Archivos

```
outputs/
├── shain_utils.py              # ⭐ Módulo principal
├── app_shain_daicho.py        # ⭐ Aplicación web
├── requirements.txt            # Dependencias
├── config.yaml                 # Configuración
├── README.md                   # Guía completa
├── GUIA_COMPLETA.md           # Documentación (3000+ palabras)
├── RESUMEN_EJECUTIVO.md       # Proyecto completo
└── QUICK_START.md             # Este archivo
```

---

## 🎓 Recursos

- **Documentación:** GUIA_COMPLETA.md
- **Ejemplos:** Ejemplos en este archivo
- **Configuración:** config.yaml
- **Código:** shain_utils.py (bien comentado)

---

## 📞 Soporte

- **Email:** tech@uns.jp
- **Documentación:** Ver archivos .md incluidos
- **Código:** Todos los archivos están documentados

---

**Versión:** 2.0.0  
**Última actualización:** 30 Enero 2026  
**Estado:** ✅ Listo para producción
