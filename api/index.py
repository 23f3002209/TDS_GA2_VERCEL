import json
import os
import numpy as np
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)

# Basic CORS setup
CORS(app, resources={r"/*": {"origins": "*"}})

# The "Safety Net": Ensures every response (even errors) has CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route("/", methods=["GET"])
def read_root():
    return jsonify({"message": "Hello, World!"})

@app.route("/", methods=["POST", "OPTIONS"])
def process_request():
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return make_response("", 200)

    # Get JSON body
    body = request.get_json()
    if not body:
        return jsonify({"error": "Missing request body"}), 400
    
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    # File path logic (Vercel looks from the root)
    # If the file is in your 'api/' folder, use 'api/q-vercel-latency.json'
    file_path = './q-vercel-latency.json' 
    
    try:
        with open(file_path) as file:
            data = json.load(file)
            
        output = {}
        for region in regions:
            latency = []
            uptime = []
            breaches = 0

            for entry in data:
                if entry.get('region') == region:
                    latency.append(entry.get('latency_ms', 0))
                    uptime.append(entry.get('uptime_pct', 0))
                    if entry.get('latency_ms', 0) > threshold_ms:
                        breaches += 1

            if latency:
                # Ensure values are native Python floats for JSON serialization
                avg_latency = float(np.mean(latency))
                p95_latency = float(np.percentile(latency, 95))
                avg_uptime = float(np.mean(uptime))
            else:
                avg_latency = 0.0
                p95_latency = 0.0
                avg_uptime = 0.0

            output[region] = {
                'avg_latency': avg_latency,
                'p95_latency': p95_latency,
                'avg_uptime': avg_uptime,
                'breaches': breaches
            }

        return jsonify(output)
    
    except FileNotFoundError:
        return jsonify({"error": f"Data file not found at {file_path}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Vercel
app = app