import json
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List


app = FastAPI()


# Enable CORS for POST requests from any origin and allow all methods/headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins; adjust for security in production
    allow_credentials=True,    # Allow cookies and credentials if needed
    allow_methods=["*"],       # Allow all HTTP methods including OPTIONS
    allow_headers=["*"]        # Allow all headers in requests
    # 'expose_headers' is optional and usually not set to '*' (omit here)
)


class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: int


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.post("/")
async def process_request(body: RequestBody):
    # Use relative path according to your project structure on Vercel
    with open('vercel/q-vercel-latency.json') as file:
        data = json.load(file)
    output = {}

    for region in body.regions:
        latency = []
        uptime = []
        breaches = 0

        for entry in data:
            if entry['region'] == region:
                latency.append(entry['latency_ms'])
                uptime.append(entry['uptime_pct'])
                if entry['latency_ms'] > body.threshold_ms:
                    breaches += 1

        if latency:
            avg_latency = sum(latency) / len(latency)
            p95_latency = float(np.percentile(latency, 95))
            avg_uptime = sum(uptime) / len(uptime)
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

    return output
