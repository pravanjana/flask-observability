from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging
import json
import time
import random
import os

app = Flask(__name__)

REQUEST_COUNT = Counter(
    'flask_request_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'flask_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

ACTIVE_REQUESTS = Gauge(
    'flask_active_requests',
    'Number of active requests being processed'
)

ERROR_COUNT = Counter(
    'flask_error_total',
    'Total number of errors',
    ['endpoint']
)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": getattr(record, 'path', ''),
            "method": getattr(record, 'method', ''),
            "status": getattr(record, 'status', ''),
            "duration_ms": getattr(record, 'duration_ms', ''),
            "pod": os.environ.get('HOSTNAME', 'local')
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger('flask_app')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@app.before_request
def start_timer():
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()

@app.after_request
def log_and_record_metrics(response):
    duration = time.time() - request.start_time
    ACTIVE_REQUESTS.dec()
    if request.path != '/metrics':
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.path
        ).observe(duration)
        logger.info(
            "request completed",
            extra={
                "path": request.path,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }
        )
    return response

@app.route('/')
def home():
    return jsonify({"message": "Flask Observability Demo", "status": "healthy"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/api/data')
def data():
    time.sleep(random.uniform(0.01, 0.1))
    return jsonify({"data": "some data", "count": random.randint(1, 100)})

@app.route('/api/error')
def error():
    ERROR_COUNT.labels(endpoint='/api/error').inc()
    logger.error(
        "simulated error occurred",
        extra={"path": "/api/error", "method": "GET", "status": 500, "duration_ms": 0}
    )
    return jsonify({"error": "something went wrong"}), 500

@app.route('/api/slow')
def slow():
    time.sleep(random.uniform(0.5, 2.0))
    return jsonify({"message": "slow response"})

if __name__ == '__main__':
    logger.info("Flask app starting", extra={"path": "", "method": "", "status": "", "duration_ms": ""})
    app.run(host='0.0.0.0', port=5000, debug=False)
