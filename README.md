# Dev Storyteller

## Del Repositorio a tu Speech de Entrevista

"Dev Storyteller" es una aplicación web tipo micro-SaaS diseñada para transformar tus proyectos de GitHub en un "pack completo de defensa de proyecto" listo para entrevistas. Olvídate de los bullets genéricos del CV; esta herramienta te prepara para presentar tus proyectos de manera impactante y adaptada a diferentes audiencias.

### ¿Qué Ofrece?

Para cada repositorio de GitHub que elijas, "Dev Storyteller" genera:

*   **Resumen para Recruiter:** 2-3 líneas de texto no técnico, enfocado en el valor de negocio del proyecto.
*   **Resumen para Entrevista Técnica:** Un minuto de explicación sobre la arquitectura, el stack tecnológico y los problemas técnicos resueltos.
*   **Explicación "Para Tontos":** Una descripción simplificada del proyecto, ideal para practicar cómo comunicarlo a audiencias no técnicas.
*   **Versiones Multi-idioma:** Todo el contenido generado está disponible en inglés y español.
*   **Preguntas y Respuestas de Entrevista:** 10 posibles preguntas de entrevista sobre el proyecto, junto con respuestas propuestas.
*   **Esqueleto de Tests (Opcional):** Ideas y estructuras básicas para tests (p.ej., E2E con Playwright o tests de API) que podrías implementar.

Todo este contenido se guarda para que el usuario pueda imprimirlo, estudiarlo o copiarlo/pegarlo directamente en su portfolio o CV.

### Tecnologías Utilizadas

El proyecto "Dev Storyteller" está construido con una arquitectura full-stack:

*   **Backend:**
    *   **Lenguaje:** Python
    *   **Framework:** FastAPI
    *   **Base de Datos:** SQLAlchemy (ORM)
    *   **Tareas Asíncronas:** Celery con Redis
    *   **Servidor:** Uvicorn
    *   **Herramientas de Calidad:** Ruff (linter), Black (formateador)
*   **Frontend:**
    *   **Framework:** React
    *   **Build Tool:** Vite

### Configuración del Entorno de Desarrollo

Para levantar el proyecto localmente, sigue los siguientes pasos:

#### 1. Backend

1.  **Navega al directorio del backend:**
    ```bash
    cd workspace/dev_storyteller/backend
    ```
2.  **Crea y activa un entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Linux/macOS
    # venv\Scripts\activate   # En Windows
    ```
3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configura las variables de entorno:**
    Crea un archivo `.env` en el directorio `backend` con las configuraciones necesarias (ej. `DATABASE_URL`, `REDIS_URL`).
    *(Nota: Se necesitará un archivo `.env.example` o instrucciones más detalladas para esto en el futuro.)*
5.  **Inicia la base de datos (si es necesario):**
    Asegúrate de que tu base de datos (ej. PostgreSQL si usas `psycopg2-binary`) esté corriendo y accesible.
6.  **Ejecuta las migraciones de la base de datos (si aplica):**
    *(Nota: Se necesitarán comandos específicos para las migraciones de SQLAlchemy/Alembic.)*
7.  **Inicia el servidor FastAPI:**
    ```bash
    uvicorn src.main:app --reload
    ```
    El backend estará disponible en `http://localhost:8000` (o el puerto configurado).

#### 2. Frontend

1.  **Navega al directorio del frontend:**
    ```bash
    cd workspace/dev_storyteller/frontend
    ```
2.  **Instala las dependencias de Node.js:**
    ```bash
    npm install
    ```
3.  **Inicia la aplicación React:**
    ```bash
    npm run dev
    ```
    El frontend estará disponible en `http://localhost:5173` (o el puerto configurado por Vite).

### Ejecución de Pruebas

#### Backend

1.  **Asegúrate de estar en el entorno virtual del backend:**
    ```bash
    cd workspace/dev_storyteller/backend
    source venv/bin/activate
    ```
2.  **Ejecuta Pytest:**
    ```bash
    pytest
    ```

#### Frontend

*(Nota: Se necesitarán instrucciones específicas para ejecutar pruebas de frontend, si las hay, como Jest o React Testing Library.)*

### Contribución

¡Agradecemos cualquier contribución! Por favor, consulta las guías de contribución (cuando estén disponibles) para más detalles.

### Licencia

[Pendiente: Añadir información de licencia]