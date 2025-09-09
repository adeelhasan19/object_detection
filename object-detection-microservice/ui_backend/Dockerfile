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
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "ui_app.py"]