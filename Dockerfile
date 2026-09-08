# Imagen opcional: sirve para Cloud Run o para probar en local con Docker.
# En Render no hace falta, porque detecta el proyecto de Python solo.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY calculos.py server.py ./

# Los servicios de nube inyectan PORT; 8080 es el valor por defecto.
ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
