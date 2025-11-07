FROM mcr.microsoft.com/devcontainers/python:3.11

# Install dependencies
WORKDIR /workspace/grazie-service
COPY grazie-service/requirements_webapp.txt ./
RUN pip install --no-cache-dir -r requirements_webapp.txt
