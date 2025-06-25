import os
from dotenv import load_dotenv
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import logging

class FarmDatabase:
    def __init__(self):
        load_dotenv()
        self.config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'database': os.getenv('DB_NAME'),
        }
        
    def get_connection(self):
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as err:
            logging.error(f"Database connection error: {err}")
            return None
    
    def get_sensor_data(self, hours_back=24):
        """Recupera dati sensori storici dalle ultime X ore"""
        try:
            conn = self.get_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT parametro, asset, valore, data
            FROM Storico 
            WHERE data >= %s 
            AND parametro IN ('Umidità', 'Temperatura', 'Silos', 'Serbatoio')
            ORDER BY data DESC
            """
            
            start_time = datetime.now() - timedelta(hours=hours_back)
            df = pd.read_sql(query, conn, params=[start_time])
            conn.close()
            
            # Converti la colonna data
            df['data'] = pd.to_datetime(df['data'])
            
            # Converti valore in numerico dove possibile
            df['valore'] = pd.to_numeric(df['valore'], errors='coerce')
            
            # Rimuovi righe con valori NaN (come OFF)
            df = df.dropna(subset=['valore'])
            
            return df
            
        except Exception as e:
            logging.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def get_latest_values(self):
        """Recupera i valori più recenti dalla tabella Stato"""
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            query = """
            SELECT parametro, asset, valore, data
            FROM Stato
            WHERE parametro IN ('Umidità', 'Temperatura', 'Silos', 'Serbatoio')
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            # Organizza i dati per asset
            latest_data = {}
            for _, row in df.iterrows():
                # Gestisci valori numerici e stringhe
                try:
                    value = float(row['valore'])
                except (ValueError, TypeError):
                    value = row['valore']  # Mantieni come stringa se non numerico
                
                key = f"{row['parametro']}_{row['asset']}"
                latest_data[key] = {
                    'value': value,
                    'timestamp': row['data']
                }
            
            return latest_data
            
        except Exception as e:
            logging.error(f"Error fetching latest data: {e}")
            return {}
    
    def get_system_status(self):
        """Recupera lo stato attuale dei sistemi"""
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            query = """
            SELECT parametro, asset, valore, data
            FROM Stato
            WHERE parametro = 'Stato'
            AND asset IN ('Pompa', 'Servo')
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            status_data = {}
            for _, row in df.iterrows():
                key = f"{row['parametro']}_{row['asset']}"
                status_data[key] = {
                    'value': row['valore'],
                    'timestamp': row['data'],
                    'status': 'active' if row['valore'] == 'ON' else 'inactive'
                }
            
            return status_data
            
        except Exception as e:
            logging.error(f"Error fetching system status: {e}")
            return {}

    def get_system_statistics(self):
        """Recupera statistiche avanzate dei sistemi"""
        try:
            conn = self.get_connection()
            if not conn:
                return {
                    'servo': {'aperture_oggi': 0},
                    'pompa': {'ml_oggi': 0, 'litri_oggi': 0}
                }
            
            cursor = conn.cursor(dictionary=True)
            
            # Query servo - conta transizioni OFF -> ON (semplificata)
            servo_query = """
            SELECT 
                SUM(CASE 
                    WHEN valore = 'ON' AND 
                        LAG(valore) OVER (ORDER BY data) = 'OFF' 
                    THEN 1 ELSE 0 
                END) as aperture_oggi
            FROM Storico 
            WHERE parametro = 'Stato' 
            AND asset = 'Servo'
            AND DATE(data) = CURDATE()
            ORDER BY data
            """
            
            # Query pompa - conta tutti i record ON oggi
            pump_query = """
            SELECT COUNT(*) as records_on
            FROM Storico 
            WHERE parametro = 'Stato' 
            AND asset = 'Pompa'
            AND valore = 'ON'
            AND DATE(data) = CURDATE()
            """
            
            # Esegui query servo
            try:
                cursor.execute(servo_query)
                servo_result = cursor.fetchone()
                aperture_oggi = int(servo_result['aperture_oggi'] or 0)
            except Exception as e:
                logging.warning(f"Servo query error: {e}")
                aperture_oggi = 0
            
            # Esegui query pompa  
            try:
                cursor.execute(pump_query)
                pump_result = cursor.fetchone()
                records_on = int(pump_result['records_on'] or 0)
            except Exception as e:
                logging.warning(f"Pump query error: {e}")
                records_on = 0
            
            conn.close()
            
            # Calcola millilitri (ogni record ON = ~100ml approssimato)
            ml_totali = records_on * 100
            litri_totali = ml_totali // 1000
            ml_rimanenti = ml_totali % 1000
            
            return {
                'servo': {
                    'aperture_oggi': aperture_oggi
                },
                'pompa': {
                    'ml_oggi': ml_totali,
                    'litri_oggi': litri_totali,
                    'ml_rimanenti': ml_rimanenti,
                    'records_debug': records_on  # Per debug
                }
            }
            
        except Exception as e:
            logging.error(f"Error fetching system statistics: {e}")
            return {
                'servo': {'aperture_oggi': 0},
                'pompa': {'ml_oggi': 0, 'litri_oggi': 0, 'ml_rimanenti': 0}
            }

    def test_connection(self):
        """Testa la connessione al database"""
        try:
            conn = self.get_connection()
            if conn:
                conn.close()
                return True
            return False
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False

    def get_database_info(self):
        """Recupera informazioni sul database per debug"""
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Conta record per tabella
            queries = {
                'storico_count': "SELECT COUNT(*) as count FROM Storico",
                'stato_count': "SELECT COUNT(*) as count FROM Stato",
                'latest_storico': "SELECT MAX(data) as latest FROM Storico",
                'latest_stato': "SELECT MAX(data) as latest FROM Stato"
            }
            
            info = {}
            for key, query in queries.items():
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    info[key] = result
                except Exception as e:
                    logging.warning(f"Error in query {key}: {e}")
                    info[key] = None
            
            conn.close()
            return info
            
        except Exception as e:
            logging.error(f"Error fetching database info: {e}")
            return {}