import cv2
import numpy as np
import json
import base64
from flask import Flask, request, jsonify
import torch
from ultralytics import YOLO
import io
from PIL import Image
import os

app = Flask(__name__)

# Load YOLOv8 model (lightweight version)
model = YOLO('yolov8n.pt')  # nano version for CPU efficiency

def process_image(image_data):
    # Decode base64 image
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Perform object detection
    results = model(image_cv)
    
    detections = []
    annotated_image = results[0].plot()  # Get image with bounding boxes
    
    # Extract detection data
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = model.names[class_id]
            
            detections.append({
                'class': class_name,
                'confidence': confidence,
                'bbox': {
                    'x1': int(x1),
                    'y1': int(y1),
                    'x2': int(x2),
                    'y2': int(y2)
                }
            })
    
    # Convert annotated image to base64 for return
    _, buffer = cv2.imencode('.jpg', annotated_image)
    annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        'detections': detections,
        'annotated_image': annotated_image_base64,
        'total_objects': len(detections)
    }

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'AI backend is running'})

@app.route('/detect', methods=['POST'])
def detect_objects():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        result = process_image(image_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)