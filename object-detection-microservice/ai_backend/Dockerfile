FROM python:3.8-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
  build-essential \
  libopenblas-dev \
  liblapack-dev \
  libx11-dev \
  libgl1-mesa-glx \
  libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

# Install the application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --timeout=520

COPY . .


EXPOSE 5001
CMD ["python", "ai_app.py"]