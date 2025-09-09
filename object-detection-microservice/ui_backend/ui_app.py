from flask import Flask, request, jsonify, render_template_string
import requests
import base64
from PIL import Image
import io
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Configuration
AI_BACKEND_URL = 'http://ai_backend:5001'  # Docker service name
OUTPUT_DIR = 'output'

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Object Detection Service</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .upload-section { border: 2px dashed #4CAF50; padding: 30px; text-align: center; margin-bottom: 30px; border-radius: 8px; background-color: #f9f9f9; }
        .result-section { margin-top: 30px; padding: 20px; border-radius: 8px; background-color: #f0f8ff; }
        .image-container { margin: 20px 0; text-align: center; }
        img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        button { 
            background-color: #4CAF50; 
            color: white; 
            padding: 12px 25px; 
            border: none; 
            cursor: pointer; 
            border-radius: 5px; 
            font-size: 16px;
            transition: background-color 0.3s;
        }
        button:hover { background-color: #45a049; }
        button:disabled { background-color: #cccccc; cursor: not-allowed; }
        input[type="file"] { 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            margin: 10px 0;
        }
        .loading { display: none; color: #4CAF50; font-weight: bold; }
        .error { color: #f44336; background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .success { color: #4CAF50; background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }
        h1 { color: #333; text-align: center; }
        h2 { color: #4CAF50; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        pre { 
            background-color: #f8f8f8; 
            padding: 15px; 
            border-radius: 5px; 
            overflow-x: auto; 
            border: 1px solid #eee;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Object Detection Microservice</h1>
        
        <div class="upload-section">
            <h2>📤 Upload Image for Object Detection</h2>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="imageFile" name="image" accept="image/*" required>
                <br><br>
                <button type="submit" id="submitBtn">🔍 Detect Objects</button>
                <div class="loading" id="loading">⏳ Processing image... Please wait</div>
            </form>
        </div>
        
        <div class="result-section" id="results" style="display:none;">
            <h2>📊 Detection Results</h2>
            <div id="resultContent"></div>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('imageFile');
            const file = fileInput.files[0];
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            
            if (!file) {
                alert('Please select an image file');
                return;
            }
            
            // Show loading state
            submitBtn.disabled = true;
            loading.style.display = 'block';
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const imageData = e.target.result.split(',')[1]; // Remove data:image/jpeg;base64,
                
                fetch('/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({image: imageData})  // Send in body, not URL
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok: ' + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    displayResults(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    displayError('Error processing image: ' + error.message);
                })
                .finally(() => {
                    // Hide loading state
                    submitBtn.disabled = false;
                    loading.style.display = 'none';
                });
            };
            reader.readAsDataURL(file);
        });
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            const resultContent = document.getElementById('resultContent');
            
            if (data.error) {
                displayError(data.error);
                return;
            }
            
            const imageHtml = `
                <div class="success">
                    <h3>✅ Detection Complete!</h3>
                    <p><strong>Total objects detected:</strong> ${data.total_objects}</p>
                </div>
                
                <div class="image-container">
                    <h3>🖼️ Detected Objects Visualization</h3>
                    <img src="data:image/jpeg;base64,${data.annotated_image}" alt="Detected Objects">
                </div>
                
                <div>
                    <h3>📋 Detection Details</h3>
                    <pre>${JSON.stringify(data.detections, null, 2)}</pre>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 5px;">
                    <h4>💾 Files Saved:</h4>
                    <p>• Annotated image and JSON results saved to output directory</p>
                </div>
            `;
            
            resultContent.innerHTML = imageHtml;
            resultsDiv.style.display = 'block';
            
            // Scroll to results
            resultsDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        function displayError(errorMessage) {
            const resultsDiv = document.getElementById('results');
            const resultContent = document.getElementById('resultContent');
            
            resultContent.innerHTML = `
                <div class="error">
                    <h3>❌ Error Occurred</h3>
                    <p>${errorMessage}</p>
                </div>
            `;
            
            resultsDiv.style.display = 'block';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health_check():
    return jsonify({'status': 'UI backend is running', 'timestamp': datetime.now().isoformat()})

@app.route('/process', methods=['POST'])
def process_image():
    try:
        # Get image data from request body (not URL)
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Forward to AI backend using POST body
        ai_response = requests.post(
            f'{AI_BACKEND_URL}/detect',
            json={'image': image_data},
            timeout=60  # Increased timeout for large images
        )
        
        if ai_response.status_code != 200:
            error_msg = ai_response.json().get('error', 'AI backend error')
            return jsonify({'error': f'AI backend error: {error_msg}'}), ai_response.status_code
        
        result = ai_response.json()
        
        # Save results with unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        json_filename = f"{OUTPUT_DIR}/detections_{timestamp}_{unique_id}.json"
        image_filename = f"{OUTPUT_DIR}/annotated_{timestamp}_{unique_id}.jpg"
        
        # Save JSON
        with open(json_filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Save annotated image
        if 'annotated_image' in result and result['annotated_image']:
            try:
                image_bytes = base64.b64decode(result['annotated_image'])
                with open(image_filename, 'wb') as f:
                    f.write(image_bytes)
            except Exception as e:
                print(f"Warning: Could not save annotated image: {e}")
        
        return jsonify(result)
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'AI backend timeout - image processing took too long'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'AI backend connection failed: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)