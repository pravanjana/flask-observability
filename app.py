from flask import Flask, request, jsonify
import logging
import json
import time
import random
import os

app = Flask(__name__)

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

@app.after_request
def log_request(response):
    duration = round((time.time() - request.start_time) * 1000, 2)
    logger.info(
        "request completed",
        extra={
            "path": request.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": duration
        }
    )
    return response

@app.route('/')
def home():
    return jsonify({
        "message": "Flask Observability Demo",
        "status": "healthy"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/data')
def data():
    time.sleep(random.uniform(0.01, 0.1))
    return jsonify({"data": "some data", "count": random.randint(1, 100)})

@app.route('/api/error')
def error():
    logger.error(
        "simulated error occurred",
        extra={"path": "/api/error", "method": "GET", "status": 500, "duration_ms": 0}
    )
    return jsonify({"error": "something went wrong"}), 500

@app.route('/api/slow')
def slow():
    time.sleep(random.uniform(0.5, 2.0))
    return jsonify({"message": "slow response", "note": "this endpoint is intentionally slow"})

if __name__ == '__main__':
    logger.info("Flask app starting", extra={"path": "", "method": "", "status": "", "duration_ms": ""})
    app.run(host='0.0.0.0', port=5000, debug=False)
