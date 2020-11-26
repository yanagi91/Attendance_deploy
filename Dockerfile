# Use python3.7-slim.
FROM python:3.7-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR ${APP_HOME}
COPY . ./
COPY requirements.txt /

# Install production dependencies.
RUN pip install -r requirements.txt 
RUN pip install --upgrade azure-cognitiveservices-vision-face

# Run the web service on container startup.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app