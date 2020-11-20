# Use python3.8-slim.
FROM python:3.8-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR ${APP_HOME}
COPY . ./

# Install production dependencies.
RUN pip install Flask google-cloud-secret-manager Pillow mysqlclient gunicorn
RUN pip install --upgrade azure-cognitiveservices-vision-face

# Run the web service on container startup.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app