# Object Detection Microservice

A microservice architecture for object detection using YOLOv8 with two backend services:
1. UI Backend - Handles user interface and request routing
2. AI Backend - Performs object detection using YOLOv8

## Prerequisites

- Docker and Docker Compose
- At least 4GB RAM (for model loading)
- Internet connection (for initial model download)

## Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd object-detection-microservice