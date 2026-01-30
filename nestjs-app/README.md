# UNS Shain Daicho Manager - NestJS API

API REST y aplicación web para la gestión del registro de empleados de Universal Kikaku (UNS).

## Características

- **Autenticación JWT** - Sistema de login seguro con roles (admin/viewer)
- **Base de datos PostgreSQL** - Persistencia de datos con TypeORM
- **Notificaciones automáticas** - Alertas de visa por email (diarias y semanales)
- **Docker** - Containerización para deploy fácil
- **API REST documentada** - Swagger UI integrado

## Inicio Rápido

### Opción 1: Docker (Recomendado)

```bash
# Iniciar con Docker Compose
npm run docker:up

# Ver logs
npm run docker:logs

# Detener
npm run docker:down
```

### Opción 2: Desarrollo Local

```bash
# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env

# Modo desarrollo
npm run start:dev

# Modo producción
npm run build
npm run start:prod
```

## URLs Disponibles

| URL | Descripción |
|-----|-------------|
| http://localhost:3000 | Dashboard principal |
| http://localhost:3000/login | Página de login |
| http://localhost:3000/api/docs | Documentación Swagger |
| http://localhost:3000/api/health | Health check |
| http://localhost:8080 | Adminer (gestión DB) |

## Credenciales por Defecto

- **Usuario:** `Jpkken`
- **Contraseña:** `57UD10R@`
- **Rol:** admin

## Estructura del Proyecto

```
nestjs-app/
├── src/
│   ├── main.ts                 # Entry point
│   ├── app.module.ts           # Main module
│   │
│   ├── auth/                   # 🔐 Autenticación JWT
│   │   ├── auth.module.ts
│   │   ├── auth.service.ts
│   │   ├── auth.controller.ts
│   │   ├── strategies/         # Passport JWT strategy
│   │   ├── guards/             # JWT & Roles guards
│   │   └── decorators/         # @Public(), @Roles()
│   │
│   ├── users/                  # 👤 Gestión de usuarios
│   │   ├── users.module.ts
│   │   └── users.service.ts
│   │
│   ├── database/               # 🗄️ PostgreSQL + TypeORM
│   │   ├── database.module.ts
│   │   └── entities/
│   │       ├── user.entity.ts
│   │       └── employee.entity.ts
│   │
│   ├── notifications/          # 📧 Alertas por email
│   │   ├── notifications.module.ts
│   │   ├── notifications.service.ts
│   │   └── notifications.controller.ts
│   │
│   ├── excel/                  # 📊 Carga de Excel
│   ├── employees/              # 👥 Gestión de empleados
│   ├── visas/                  # 🛂 Alertas de visa
│   ├── salaries/               # 💰 Análisis de salarios
│   └── reports/                # 📈 Reportes y exportación
│
├── views/                      # Plantillas Handlebars
├── public/                     # CSS y JavaScript
├── Dockerfile                  # 🐳 Imagen Docker
├── docker-compose.yml          # 🐳 Orquestación
└── .env.example                # Variables de entorno
```

## API Endpoints

### Auth (Autenticación)
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/login` | Iniciar sesión | No |
| GET | `/api/auth/profile` | Obtener perfil | Sí |
| POST | `/api/auth/logout` | Cerrar sesión | Sí |

### Employees (Empleados)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/employees` | Listar todos |
| GET | `/api/employees/search?name=X` | Buscar por nombre |
| GET | `/api/employees/stats` | Estadísticas |
| GET | `/api/employees/:id` | Obtener por ID |

### Visas (Alertas)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/visas/alerts?days=90` | Todas las alertas |
| GET | `/api/visas/alerts/critical` | Críticas (≤30 días) |
| GET | `/api/visas/alerts/warning` | Advertencia (31-60) |
| GET | `/api/visas/alerts/upcoming` | Próximas (61-90) |

### Salaries (Salarios)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/salaries/stats` | Estadísticas |
| GET | `/api/salaries/distribution` | Distribución |
| GET | `/api/salaries/top-earners` | Top salarios |

### Reports (Reportes)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reports/summary` | Reporte resumen |
| GET | `/api/reports/export/json` | Exportar JSON |
| GET | `/api/reports/export/csv` | Exportar CSV |
| GET | `/api/reports/export/excel` | Exportar Excel |

### Notifications (Solo Admin)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/notifications/test` | Enviar email de prueba |
| POST | `/api/notifications/trigger` | Disparar alertas manual |

## Configuración de Email

Para habilitar notificaciones automáticas, configura las variables SMTP en `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASS=tu-app-password
ADMIN_EMAIL=admin@uns.co.jp
```

### Alertas Automáticas

- **Diarias (9:00 AM):** Alertas críticas de visa (≤30 días)
- **Semanales (Lunes 8:00 AM):** Reporte completo de visas

## Uso con API

```typescript
// 1. Iniciar sesión
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'Jpkken', password: '57UD10R@' })
});
const { access_token } = await loginResponse.json();

// 2. Usar token en peticiones
const employees = await fetch('/api/employees', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

## Tecnologías

| Tecnología | Propósito |
|------------|-----------|
| NestJS | Framework backend |
| TypeScript | Lenguaje tipado |
| PostgreSQL | Base de datos |
| TypeORM | ORM |
| Passport + JWT | Autenticación |
| Nodemailer | Envío de emails |
| ExcelJS | Procesamiento Excel |
| Swagger | Documentación API |
| Docker | Containerización |

## Comandos Docker

```bash
npm run docker:build   # Construir imagen
npm run docker:up      # Iniciar servicios
npm run docker:down    # Detener servicios
npm run docker:logs    # Ver logs
```

## Licencia

MIT License - Universal Kikaku (UNS)
