from flask import Flask, render_template, jsonify, request
from database import FarmDatabase
from chart_generator import ChartGenerator
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/charts')
def get_charts():
    try:
        db = FarmDatabase()
        df = db.get_sensor_data(hours_back=24)
        
        if df.empty:
            return jsonify({'error': 'No data available'})
        
        chart_gen = ChartGenerator(df)
        
        charts = {
            'humidity': chart_gen.create_humidity_chart(),
            'resources': chart_gen.create_resources_chart(),
            'temperature': chart_gen.create_temperature_chart()
        }
        
        return jsonify(charts)
        
    except Exception as e:
        logging.error(f"Error generating charts: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/kpis')
def get_kpis():
    try:
        db = FarmDatabase()
        latest_data = db.get_latest_values()
        
        df = db.get_sensor_data(hours_back=1)
        chart_gen = ChartGenerator(df)
        
        kpis = chart_gen.create_dashboard_summary(latest_data)
        
        return jsonify(kpis)
        
    except Exception as e:
        logging.error(f"Error getting KPIs: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/system-status')
def get_system_status():
    """Endpoint per stato sistemi con statistiche avanzate"""
    try:
        db = FarmDatabase()
        system_status = db.get_system_status()
        system_stats = db.get_system_statistics()
        
        return jsonify({
            'status': system_status,
            'statistics': system_stats
        })
        
    except Exception as e:
        logging.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/latest-data')
def get_latest_data():
    """Endpoint per tutti i dati più recenti"""
    try:
        db = FarmDatabase()
        latest_data = db.get_latest_values()
        system_status = db.get_system_status()
        system_stats = db.get_system_statistics()
        
        return jsonify({
            'sensors': latest_data,
            'systems': {
                'status': system_status,
                'statistics': system_stats
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting latest data: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)