## app.py
from flask import Flask, render_template, request, jsonify

from simulation import main as run_sumo

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_simulation_route():
    data = request.json
    perc = float(data.get('perc', 0.8))
    price = float(data.get('price', 1.0))
    scale_traffic = float(data.get('scale_traffic', 2.0))
    
    try:
        results = run_sumo(perc, price, scale_traffic)
        return jsonify({"status": "success", "message": "Simulation Complete", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)