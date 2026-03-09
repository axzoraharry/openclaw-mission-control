---
name: saas-mvp-launcher
description: Quickly launch SaaS MVP applications with pre-configured templates for Next.js, FastAPI, and full-stack deployments. Automates project setup, database configuration, and deployment pipelines.
---

# SaaS MVP Launcher

Quickly scaffold and deploy SaaS MVP applications with best practices built-in.

## Quick Start

```bash
# Launch a full-stack SaaS MVP
saas-mvp-launcher create my-saas --template fullstack

# Launch Next.js frontend only
saas-mvp-launcher create my-app --template nextjs

# Launch FastAPI backend only
saas-mvp-launcher create my-api --template fastapi
```

## Templates

### fullstack
- Next.js 14+ with App Router
- FastAPI backend
- PostgreSQL database
- Docker Compose setup
- Authentication (Clerk/Local)
- Tailwind CSS + shadcn/ui
- TypeScript throughout

### nextjs
- Next.js 14+ with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- ESLint + Prettier configured

### fastapi
- FastAPI with Python 3.11+
- SQLAlchemy + Alembic
- PostgreSQL
- JWT authentication
- Docker setup
- pytest testing

## Commands

```bash
saas-mvp-launcher create <name> [options]
  --template <name>     Template to use (fullstack|nextjs|fastapi)
  --database <type>     Database (postgres|sqlite|mysql)
  --auth <provider>     Auth provider (clerk|local|none)
  --deploy <target>     Deployment target (docker|vercel|aws)
  --git                 Initialize git repository
  --install             Install dependencies after creation

saas-mvp-launcher list-templates
  Show available templates

saas-mvp-launcher deploy <path> [options]
  --target <target>     Deployment target
  --env <file>          Environment file
```

## Examples

```bash
# Create full-stack SaaS with auth
saas-mvp-launcher create my-saas --template fullstack --auth clerk --git --install

# Create API-only backend
saas-mvp-launcher create my-api --template fastapi --database postgres

# Deploy existing project
saas-mvp-launcher deploy ./my-saas --target docker
```

## Best Practices

- All templates include TypeScript
- Pre-configured linting and formatting
- Docker support for local development
- Environment variable management
- Health check endpoints
- API documentation (OpenAPI/Swagger)

## References

- [templates/fullstack/](templates/fullstack/)
- [templates/nextjs/](templates/nextjs/)
- [templates/fastapi/](templates/fastapi/)
