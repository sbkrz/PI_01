#Imagen base oficial de Python
FROM python:3.9

#Establecemos el directorio de trabajo
WORKDIR /app

#Dependencias 
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#Copiamos el código de la aplicación al contenedor
COPY . .

#Ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
