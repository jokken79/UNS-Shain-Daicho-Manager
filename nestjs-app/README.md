# UNS Shain Daicho Manager - NestJS API

API REST y aplicación web para la gestión del registro de empleados de Universal Kikaku (UNS).

## Inicio Rápido

```bash
# Instalar dependencias
npm install

# Modo desarrollo
npm run start:dev

# Modo producción
npm run build
npm run start:prod
```

La aplicación estará disponible en:
- **Web UI:** http://localhost:3000
- **API Docs (Swagger):** http://localhost:3000/api/docs
- **Health Check:** http://localhost:3000/api/health

## Estructura del Proyecto

```
nestjs-app/
├── src/
│   ├── main.ts                 # Entry point
│   ├── app.module.ts           # Main module
│   ├── app.controller.ts       # View routes
│   │
│   ├── common/
│   │   ├── constants.ts        # Configuration constants
│   │   └── interfaces/         # TypeScript interfaces
│   │
│   ├── excel/                  # Excel file handling
│   │   ├── excel.module.ts
│   │   ├── excel.service.ts    # Core data loading logic
│   │   └── excel.controller.ts # File upload endpoint
│   │
│   ├── employees/              # Employee management
│   │   ├── employees.module.ts
│   │   ├── employees.service.ts
│   │   ├── employees.controller.ts
│   │   └── dto/
│   │
│   ├── visas/                  # Visa alerts
│   │   ├── visas.module.ts
│   │   ├── visas.service.ts
│   │   └── visas.controller.ts
│   │
│   ├── salaries/               # Salary analysis
│   │   ├── salaries.module.ts
│   │   ├── salaries.service.ts
│   │   └── salaries.controller.ts
│   │
│   └── reports/                # Reports & export
│       ├── reports.module.ts
│       ├── reports.service.ts
│       └── reports.controller.ts
│
├── views/                      # Handlebars templates
│   ├── index.hbs
│   ├── search.hbs
│   ├── visas.hbs
│   ├── salaries.hbs
│   └── reports.hbs
│
├── public/                     # Static files
│   ├── css/style.css
│   └── js/app.js
│
├── package.json
├── tsconfig.json
└── nest-cli.json
```

## API Endpoints

### Excel (Carga de datos)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/excel/upload` | Subir archivo Excel |
| GET | `/api/excel/status` | Verificar estado de datos |

### Employees (Empleados)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/employees` | Listar todos los empleados |
| GET | `/api/employees/search?name=X` | Buscar por nombre |
| GET | `/api/employees/stats` | Estadísticas generales |
| GET | `/api/employees/stats/nationality` | Por nacionalidad |
| GET | `/api/employees/stats/age` | Por edad |
| GET | `/api/employees/stats/dispatch-companies` | Por empresa |
| GET | `/api/employees/:id` | Obtener por ID |

### Visas (Alertas)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/visas/alerts?days=90` | Alertas de visa |
| GET | `/api/visas/alerts/critical` | Alertas críticas (≤30 días) |
| GET | `/api/visas/alerts/warning` | Advertencias (31-60 días) |
| GET | `/api/visas/alerts/upcoming` | Próximas (61-90 días) |
| GET | `/api/visas/expired` | Visas expiradas |

### Salaries (Salarios)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/salaries/stats` | Estadísticas de salarios |
| GET | `/api/salaries/distribution` | Distribución (histograma) |
| GET | `/api/salaries/profit` | Análisis de ganancias |
| GET | `/api/salaries/top-earners?top=10` | Top salarios |
| GET | `/api/salaries/by-category` | Por categoría |

### Reports (Reportes)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reports/summary` | Reporte resumen |
| GET | `/api/reports/tenure` | Análisis de antigüedad |
| GET | `/api/reports/export/json` | Exportar a JSON |
| GET | `/api/reports/export/csv` | Exportar a CSV |
| GET | `/api/reports/export/excel` | Exportar a Excel |

## Interfaz Web

La aplicación incluye una interfaz web con las siguientes páginas:

1. **Dashboard** (`/`) - Métricas principales y gráficos
2. **Búsqueda** (`/search`) - Buscar empleados por nombre
3. **Alertas Visa** (`/visas`) - Alertas de vencimiento de visa
4. **Salarios** (`/salaries`) - Análisis de salarios
5. **Reportes** (`/reports`) - Reportes y exportación

## Tecnologías

- **NestJS** - Framework backend
- **TypeScript** - Lenguaje de programación
- **ExcelJS** - Lectura/escritura de Excel
- **Swagger** - Documentación de API
- **Handlebars** - Motor de plantillas
- **Plotly.js** - Gráficos interactivos

## Uso con API

```typescript
// Ejemplo: Buscar empleados
const response = await fetch('/api/employees/search?name=NGUYEN&activeOnly=true');
const employees = await response.json();

// Ejemplo: Obtener alertas de visa
const response = await fetch('/api/visas/alerts?days=90');
const alerts = await response.json();

// Ejemplo: Exportar a Excel
window.location.href = '/api/reports/export/excel?activeOnly=true';
```

## Licencia

MIT License - Universal Kikaku (UNS)
