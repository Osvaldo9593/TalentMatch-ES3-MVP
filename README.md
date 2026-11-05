# TalentMatch — Sistema de Clasificación y Preselección de CVs con IA

**Proyecto de Título para Ingeniería en Informática**  
**Estado:** MVP Final Integrado (Paso 6 — Integración Final, Seguridad, Pruebas y Preparación del MVP)

TalentMatch es una solución de software orientada a optimizar y transparentar el proceso de preselección de candidatos en reclutamiento laboral. Permite a un evaluador o reclutador crear convocatorias con criterios técnicos específicos, cargar currículums en formato PDF o DOCX, extraer su texto de forma automatizada, evaluar objetivamente la compatibilidad profesional mediante Inteligencia Artificial (OpenRouter) y visualizar los resultados consolidados en un panel interactivo.

> [!IMPORTANT]
> **Aviso Ético y de Alcance**: TalentMatch es un MVP académico de apoyo analítico a la preselección de candidatos. La Inteligencia Artificial **NO toma decisiones finales de contratación**. La decisión de selección corresponde siempre y en última instancia al evaluador o reclutador humano.

---

## 1. Arquitectura del Sistema

El sistema implementa una arquitectura desacoplada y orientada a servicios, donde el Frontend nunca se comunica directamente con proveedores externos de IA ni tiene acceso a secretos:

```text
                ┌──────────────────────────────────────┐
                │          React 18 + Vite             │
                │        Frontend SPA (TypeScript)     │
                │         http://localhost:5173        │
                └──────────────────┬───────────────────┘
                                   │ HTTP / JSON
                                   ▼
                ┌──────────────────────────────────────┐
                │             FastAPI                  │
                │          Backend REST API            │
                │         http://localhost:8000        │
                └──────────┬────────────────┬──────────┘
                           │                │
            SQLAlchemy /   │                │ HTTPS / JSON
             SQL (5432)    │                │ (Bearer Token)
                           ▼                ▼
                ┌────────────────────┐   ┌───────────────────────────┐
                │   PostgreSQL 16    │   │      OpenRouter API       │
                │  Docker Container  │   │     (openrouter/free)     │
                │ (talentmatch_db)   │   │ https://openrouter.ai/v1  │
                └────────────────────┘   └───────────────────────────┘
                           +
                ┌────────────────────┐
                │  Local File System │
                │ (backend/storage/) │
                │    UUID PDF Safe   │
                └────────────────────┘
```

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS. Interfaz limpia tipo editorial, componentes modulares, filtros multivariables y modales de inspección.
- **Backend**: Python 3, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic. Servicios independientes para almacenamiento físico de archivos PDF/DOCX, extracción de texto y clasificación con IA.
- **Base de Datos**: PostgreSQL 16 sobre Docker con volumen persistente (`postgres_data`).
- **IA**: OpenRouter API utilizando el modelo `openrouter/free`. Clave de API aislada exclusivamente en el backend.
- **Almacenamiento**: Almacenamiento local aislado en `backend/storage/cvs/` utilizando identificadores UUID v4 y validación anti path-traversal.

---

## 2. Requisitos Previos

Antes de ejecutar el proyecto, asegúrate de contar con las siguientes herramientas instaladas en tu sistema:

- **Docker Desktop** o **Docker Engine + Docker Compose** (en ejecución).
- **Python 3.10 o superior** (probado en Python 3.12 y 3.14).
- **Node.js 18 o superior** y gestor de paquetes **npm**.
- **Clave de API de OpenRouter** (gratuita, obtenible en [openrouter.ai/keys](https://openrouter.ai/keys)).

---

## 3. Variables de Entorno

El proyecto incluye plantillas `.env.example` tanto para el Backend como para el Frontend.

### Backend (`backend/.env`)

Copia la plantilla de ejemplo y configura tu clave de OpenRouter:

```bash
cp backend/.env.example backend/.env
```

Parámetros disponibles en `backend/.env`:

| Variable | Descripción | Valor por Defecto / Ejemplo |
| :--- | :--- | :--- |
| `PROJECT_NAME` | Nombre de la aplicación | `"TalentMatch API"` |
| `API_V1_STR` | Prefijo de rutas v1 | `"/api/v1"` |
| `ENVIRONMENT` | Entorno de ejecución (`development` / `production`) | `"development"` |
| `BACKEND_CORS_ORIGINS` | Orígenes permitidos para CORS | `["http://localhost:5173","http://localhost:3000"]` |
| `FRONTEND_URL` | Origen alternativo individual | `"http://localhost:5173"` |
| `POSTGRES_USER` | Usuario de la base de datos | `postgres` |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos | `postgres` |
| `POSTGRES_HOST` | Host de PostgreSQL | `localhost` |
| `POSTGRES_PORT` | Puerto de conexión | `5432` |
| `POSTGRES_DB` | Nombre de la base de datos | `talentmatch_db` |
| `DATABASE_URL` | String de conexión SQLAlchemy (opcional) | `postgresql://postgres:postgres@localhost:5432/talentmatch_db` |
| `CV_STORAGE_PATH` | Carpeta relativa de almacenamiento de PDFs | `storage/cvs` |
| `MAX_CV_FILE_SIZE_MB` | Tamaño máximo por PDF en Megabytes | `10` |
| `OPENROUTER_API_KEY` | Clave de autenticación OpenRouter (**Obligatoria**) | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | Modelo de lenguaje utilizado | `openrouter/free` |
| `OPENROUTER_BASE_URL` | URL base de la API de OpenRouter | `https://openrouter.ai/api/v1` |
| `MAX_CV_TEXT_LENGTH` | Longitud máxima de texto de CV enviada a IA | `8000` |

> [!CAUTION]
> **Seguridad**: `OPENROUTER_API_KEY` nunca debe subirse al repositorio ni configurarse en el frontend.

### Frontend (`frontend/.env`)

Copia la plantilla de ejemplo en la carpeta frontend:

```bash
cp frontend/.env.example frontend/.env
```

Contenido de `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

---

## 4. Instalación y Ejecución Paso a Paso

Sigue esta guía secuencial para levantar el sistema completo desde cero:

### Autenticación y migraciones

Después de instalar `backend/requirements.txt`, copia `backend/.env.example` a
`backend/.env` y reemplaza `JWT_SECRET_KEY` y las contraseñas de seed por valores
seguros. Ejecuta las migraciones y crea los usuarios iniciales:

```bash
cd backend
alembic upgrade head
python scripts/seed_users.py
```

El usuario `admin` puede actualizar estados y eliminar definitivamente CVs. El
usuario `recruiter` puede operar el flujo normal y actualizar estados, pero no
puede ejecutar purgas definitivas.

### Pruebas

```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npm run test
```

### Paso 1: Levantar la Base de Datos con Docker

Desde la raíz del proyecto (`TalentMatch/`):

```bash
docker compose up -d
```

Verifica que el contenedor `talentmatch-postgres` esté activo y saludable:
```bash
docker compose ps
```

### Paso 2: Configurar y Levantar el Backend (FastAPI)

1. Ingresa a la carpeta `backend`:
   ```bash
   cd backend
   ```

2. Crea y activa el entorno virtual de Python:
   - **En Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **En Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Instala las dependencias del backend:
   ```bash
   pip install -r requirements.txt
   ```

4. Asegúrate de haber creado el archivo `.env` con tu `OPENROUTER_API_KEY`:
   ```bash
   # Configura OPENROUTER_API_KEY en backend/.env
   ```

5. Aplica las migraciones de Alembic sobre PostgreSQL:
   ```bash
   alembic upgrade head
   ```

6. Inicia el servidor de desarrollo FastAPI:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

El backend quedará escuchando en `http://localhost:8000`.

### Paso 3: Configurar y Levantar el Frontend (React + Vite)

1. En una nueva terminal, ingresa a la carpeta `frontend`:
   ```bash
   cd frontend
   ```

2. Instala las dependencias de Node:
   ```bash
   npm install
   ```

3. Inicia el servidor de desarrollo de Vite:
   ```bash
   npm run dev
   ```

El frontend estará disponible en `http://localhost:5173`.

---

## 5. Verificación y Pruebas Automatizadas

El proyecto cuenta con suites de pruebas unitarias, de integración y end-to-end:

### Pruebas del Backend (pytest)
Desde la carpeta `backend/`:
```bash
pytest -v
```
*(52 pruebas unitarias y de integración que verifican endpoints, esquemas, reglas de validación, DOCX y modelos).*

### Pruebas del Frontend (vitest)
Desde la carpeta `frontend/`:
```bash
npm test
```
*(18 pruebas que validan autenticación, carga PDF/DOCX, componentes del dashboard, listado, ordenamiento y clientes API).*

### Verificación del Flujo End-to-End en Vivo
Ejecuta la prueba de integración completa con PostgreSQL y OpenRouter en vivo:
```bash
python scripts/verify_step6_e2e.py
```

---

## 6. URLs y Endpoints Principales

| Servicio / Recurso | Método / URL | Descripción |
| :--- | :--- | :--- |
| **Frontend Web** | [http://localhost:5173/dashboard](http://localhost:5173/dashboard) | Vista consolidada de métricas y convocatorias |
| **Gestión de Ofertas** | [http://localhost:5173/job-offers](http://localhost:5173/job-offers) | Listado y administración de convocatorias laborales |
| **Monitoreo del Sistema** | [http://localhost:5173/system-status](http://localhost:5173/system-status) | Estado de salud de API, PostgreSQL y OpenRouter |
| **Swagger UI (Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Documentación interactiva OpenAPI de endpoints |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Documentación alternativa de la API |
| **Health Check Raíz** | `GET /health` | Estado del backend y conectividad a base de datos |
| **Health Check API** | `GET /api/v1/health` | Estado del servicio FastAPI |
| **Health Check DB** | `GET /api/v1/health/database` | Verificación de conexión con PostgreSQL |
| **Health Check OpenRouter** | `GET /api/v1/health/openrouter` | Verificación en vivo de OpenRouter (`openrouter/free`) |
| **Métricas Dashboard** | `GET /api/v1/dashboard/stats` | Conteo de ofertas activas, CVs totales, evaluados y pendientes |
| **Listar Ofertas** | `GET /api/v1/job-offers/` | Obtiene ofertas laborales con métricas agregadas de CVs |
| **Crear Oferta** | `POST /api/v1/job-offers/` | Registra una oferta con habilidades requeridas y deseables |
| **Obtener Oferta** | `GET /api/v1/job-offers/{id}` | Obtiene detalle completo de una oferta |
| **Actualizar Oferta** | `PUT /api/v1/job-offers/{id}` | Modifica datos y criterios de selección |
| **Eliminar Oferta** | `DELETE /api/v1/job-offers/{id}` | Eliminación física (bloqueada si posee CVs asociados) |
| **Cargar CV (PDF/DOCX)** | `POST /api/v1/job-offers/{id}/cvs/` | Valida, almacena con UUID y extrae texto de PDF o DOCX |
| **Listar CVs de Oferta** | `GET /api/v1/job-offers/{id}/cvs/` | Retorna los CVs de la convocatoria con resumen de evaluación |
| **Detalle de CV** | `GET /api/v1/job-offers/{id}/cvs/{cv_id}` | Obtiene metadatos, texto extraído y conteo de palabras |
| **Descargar documento** | `GET /api/v1/job-offers/{id}/cvs/{cv_id}/file` | Entrega segura del archivo PDF o DOCX original |
| **Eliminar CV** | `DELETE /api/v1/job-offers/{id}/cvs/{cv_id}` | Elimina registro en BD, archivo en disco y evaluación en cascada |
| **Evaluación automática** | `POST /api/v1/job-offers/{id}/cvs/` | Programa la evaluación del CV cargado en segundo plano |
| **Obtener Evaluación** | `GET /api/v1/job-offers/{id}/cvs/{cv_id}/evaluation` | Consulta evaluación almacenada en PostgreSQL sin re-evaluar |
| **Evaluar en Lote** | `POST /api/v1/job-offers/{id}/evaluate` | Programa en segundo plano todos los CVs procesados pendientes |
| **Login** | `POST /api/v1/auth/login` | Obtiene un token JWT para usuarios admin o recruiter |
| **Perfil actual** | `GET /api/v1/auth/me` | Consulta el usuario autenticado |

---

## 7. Flujo de Uso del Sistema

1. **Crear Convocatoria Laboral**:
   - El reclutador define el cargo, modalidad, descripción y criterios clave: habilidades obligatorias (*must-have*), habilidades deseadas (*nice-to-have*) y requisitos generales.
2. **Carga de Currículums**:
   - Se suben los documentos en formato PDF o DOCX mediante arrastrar y soltar o selector de archivos.
   - El backend valida el archivo, tamaño `<= 10 MB`, genera un nombre único mediante UUID v4, almacena el archivo en disco y extrae el texto normalizado desde párrafos, viñetas y tablas DOCX.
3. **Evaluación Asistida por IA**:
   - Se envía a OpenRouter (`openrouter/free`) el conjunto de criterios del cargo junto con el texto extraído del currículum.
   - El prompt del sistema fuerza estricta objetividad, prohibiendo el uso de datos personales (edad, género, nacionalidad, fotografía, etc.) para el puntaje.
4. **Validación Estructurada y Persistencia**:
   - La respuesta del LLM es decodificada y validada estrictamente mediante esquemas Pydantic.
   - El puntaje (0–100) y la recomendación (`recommended`, `review`, `not_recommended`) se normalizan y almacenan en la tabla `candidate_evaluations` de PostgreSQL.
5. **Revisión en el Dashboard**:
   - El reclutador visualiza a los candidatos ordenados por compatibilidad, filtra por estado y examina el desglose cualitativo (habilidades encontradas, faltantes, análisis de experiencia y resumen).
   - El reclutador puede abrir el PDF original y toma la decisión final de preselección.

---

## 8. Criterios de Preselección Asistida

El sistema aplica umbrales objetivos y estandarizados para la recomendación:

- **80 – 100 puntos** (`recommended`): Alta compatibilidad con las competencias indispensables y experiencia requerida.
- **60 – 79 puntos** (`review`): Cumplimiento parcial de requisitos o habilidades transferibles que ameritan revisión humana detallada.
- **0 – 59 puntos** (`not_recommended`): Brecha significativa respecto a las habilidades o experiencia indispensables del cargo.

---

## 9. Almacenamiento Local de Documentos

- Los archivos PDF y DOCX se almacenan localmente en la ruta `backend/storage/cvs/`.
- Cada archivo recibe un nombre seguro basado en UUID y conserva su extensión.
- El nombre original proporcionado por el usuario (`original_filename`) se preserva únicamente como metadato en la base de datos.
- Se implementan guardas anti *path-traversal* para asegurar que ningún archivo pueda ser leído ni escrito fuera del directorio designado.
- El directorio de almacenamiento físico se encuentra explícitamente excluido del control de versiones en `.gitignore`.

---

## 10. Limitaciones del MVP

Como prototipo académico (MVP), el sistema contempla explícitamente las siguientes limitaciones de alcance:

- **Sin OCR**: La extracción de texto requiere PDFs de texto seleccionable o DOCX legibles. No procesa imágenes escaneadas ni aplica reconocimiento óptico de caracteres.
- **Sin RAG ni Bases de Datos Vectoriales**: La evaluación se basa en el contexto directo enviado al modelo de lenguaje (`openrouter/free`), sin embeddings ni bases vectoriales externas.
- **Autenticación acotada al MVP**: JWT y roles `admin`/`recruiter` están integrados. No se incluye OAuth ni gestión multi-inquilino (*multi-tenant*).
- **Almacenamiento Local**: Los archivos se guardan en el sistema de archivos del servidor backend (no en buckets en la nube como S3 o GCS).
- **Sin Decisión Contractual**: La IA actúa exclusivamente como asistente consultivo; la decisión final de selección o contratación depende siempre de la evaluación humana.
