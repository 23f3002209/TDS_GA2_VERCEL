from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json
import os

app = FastAPI()

# 1. Standard Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Manual Middleware for Headers (The "Safety Net")
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# 3. Explicit OPTIONS handler
@app.options("/{rest_of_path:path}")
async def preflight():
    return Response(status_code=200)


class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: int


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.post("/")
async def process_request(body: RequestBody):
    # Use relative path according to your project structure on Vercel
    with open('./q-vercel-latency.json') as file:
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
