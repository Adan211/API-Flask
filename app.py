from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pytds

load_dotenv()  # Carga las variables desde .env

app = Flask(__name__)
CORS(app)

# Conexión usando variables de entorno
conn_str = {
    "server": os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", 1433))  # Default: 1433
}

@app.route('/reporte_ventas', methods=['GET'])
def reporte_ventas():
    fecha_str = request.args.get('fecha')  # formato: '2024-03-28'
    try:
        fecha_inicio = datetime.strptime(fecha_str, '%Y-%m-%d')
        fecha_fin = fecha_inicio + timedelta(days=1)

        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            query = """
                SELECT
                    ROUND(SUM(totalbebidas), 2) AS Bebidas,
                    ROUND(SUM(totalalimentos), 2) AS Alimentos,
                    ROUND(SUM(otros), 2) AS Otros,
                    ROUND(SUM(totalbebidas + totalalimentos + otros + totalimpuesto1), 2) AS VentaTotal,
                    ROUND(SUM(totalimpuesto1), 2) AS Impuestos,
                    ROUND(SUM(totaldescuentoycortesia), 2) AS [DescCortesias],

                    CASE WHEN SUM(totalbebidas + totalalimentos + otros) > 0
                        THEN ROUND(SUM(totalbebidas) * 100.0 / SUM(totalbebidas + totalalimentos + otros), 2)
                        ELSE 0 END AS PorcentajeBebidas,

                    CASE WHEN SUM(totalbebidas + totalalimentos + otros) > 0
                        THEN ROUND(SUM(totalalimentos) * 100.0 / SUM(totalbebidas + totalalimentos + otros), 2)
                        ELSE 0 END AS PorcentajeAlimentos,

                    CASE WHEN SUM(totalbebidas + totalalimentos + otros) > 0
                        THEN ROUND(SUM(otros) * 100.0 / SUM(totalbebidas + totalalimentos + otros), 2)
                        ELSE 0 END AS PorcentajeOtros

                FROM cheques
                WHERE fecha >= ? AND cierre < ?
            """
            cursor.execute(query, fecha_inicio, fecha_fin)
            row = cursor.fetchone()

            if row:
                # Adaptamos al modelo que espera Android
                return jsonify({
    "bebidas": row.Bebidas,
    "alimentos": row.Alimentos,
    "otros": row.Otros,
    "venta_total": row.VentaTotal,
    "impuestos": row.Impuestos,
    "desc_cortesias": row.DescCortesias,
    "porcentaje_bebidas": row.PorcentajeBebidas,
    "porcentaje_alimentos": row.PorcentajeAlimentos,
    "porcentaje_otros": row.PorcentajeOtros
            })

            else:
                return jsonify({"error": "No se encontraron datos"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render define PORT, si no, usa 5000 por defecto
    app.run(debug=True, host="0.0.0.0", port=port, threaded=True)
