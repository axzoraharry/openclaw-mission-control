FROM python:3.12-slim

WORKDIR /app

# Install uv for fast Python package management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY app/ ./app/

# Install dependencies
RUN uv sync

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
