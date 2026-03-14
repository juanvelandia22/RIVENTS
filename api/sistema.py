from flask import Flask, render_template_string, request, redirect, session, send_file, url_for
import sqlite3
from datetime import datetime
import os
from fpdf import FPDF
import io

app = Flask(__name__)
app.secret_key = 'pollo_raul_secret_key'

# ==============================
# CONFIGURACIÓN DEL NEGOCIO
# ==============================
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
VALOR_IVA = 0.19

def get_db_connection():
    db_path = "pos.db"
    if os.environ.get("VERCEL"):
        db_path = "/tmp/pos.db"
        if not os.path.exists(db_path) and os.path.exists("pos.db"):
            import shutil
            shutil.copy("pos.db", db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Nueva estructura con CÓDIGO como llave primaria
        conn.execute("""CREATE TABLE IF NOT EXISTS inventario (
            codigo INTEGER PRIMARY KEY, 
            producto TEXT, 
            precio REAL, 
            stock REAL, 
            tipo TEXT,
            fecha_registro TEXT, 
            fecha_vencimiento TEXT)""")
        
        conn.execute("""CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            subtotal REAL, iva REAL, total REAL, 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre TEXT, 
            cliente_documento TEXT,
            detalles_json TEXT)""")
        conn.commit()

init_db()

# ==============================
# INTERFAZ MEJORADA (HTML/CSS)
# ==============================
HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ nombre }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1300px; margin: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
        .full-width { grid-column: 1 / -1; }
        h1, h2 { color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }
        th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
        th { background: #f8f9fa; }
        input, select, button { width: 100%; padding: 10px; margin: 4px 0; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #3498db; color: white; border: none; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { opacity: 0.8; }
        .btn-success { background: #2ecc71; }
        .btn-danger { background: #e74c3c; width: auto; padding: 5px 10px; }
        .btn-edit { background: #f1c40f; color: #333; width: auto; padding: 5px 10px; }
        .total-display { font-size: 24px; font-weight: bold; color: #27ae60; margin: 15px 0; border: 2px dashed #2ecc71; padding: 10px; text-align: center; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; background: #e8f4fd; color: #3498db; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card full-width">
            <h1 style="text-align:center;">🍗 {{ nombre }} - Inventario y POS</h1>
        </div>

        <div class="card">
            <h2>📦 Registro / Edición de Producto</h2>
            <form action="/inventario/guardar" method="POST">
                <div style="display:flex; gap:10px;">
                    <input type="number" name="codigo" placeholder="Cód (Ej: 101)" required>
                    <input type="text" name="producto" placeholder="Nombre del Producto" required>
                </div>
                <div style="display:flex; gap:10px;">
                    <input type="number" step="0.01" name="precio" placeholder="Precio" required>
                    <input type="number" step="0.01" name="stock" placeholder="Stock Inicial" required>
                </div>
                <div style="display:flex; gap:10px;">
                    <select name="tipo">
                        <option value="Kg">Kilogramos (Kg)</option>
                        <option value="Und">Unidades (Und)</option>
                    </select>
                    <input type="date" name="vencimiento" title="Fecha de Vencimiento">
                </div>
                <button type="submit" class="btn-success">Guardar o Actualizar</button>
            </form>
            
            <h3>Lista de Inventario</h3>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Cód</th>
                            <th>Producto</th>
                            <th>Precio</th>
                            <th>Stock</th>
                            <th>Registro</th>
                            <th>Acción</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in inventario %}
                        <tr>
                            <td><strong>{{ p.codigo }}</strong></td>
                            <td>{{ p.producto }}</td>
                            <td>${{ "{:,.0f}".format(p.precio) }}</td>
                            <td><span class="badge">{{ p.stock }} {{ p.tipo }}</span></td>
                            <td style="font-size: 10px;">{{ p.fecha_registro }}</td>
                            <td>
                                <div style="display:flex; gap:5px;">
                                    <a href="/inventario/eliminar/{{ p.codigo }}" onclick="return confirm('¿Eliminar producto?')">
                                        <button class="btn-danger">🗑️</button>
                                    </a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>🛒 Nueva Venta</h2>
            <form action="/carrito/agregar" method="POST">
                <input type="number" name="codigo_vta" placeholder="Escribe el código numérico..." required>
                <input type="number" step="0.01" name="cantidad" placeholder="Cantidad a vender" required>
                <button type="submit">Agregar al Carrito</button>
            </form>
            <hr>
            <div class="total-display">TOTAL: ${{ "{:,.0f}".format(total_venta) }}</div>
            {% if carrito %}
                {% for item in carrito %}
                <p>✅ ({{ item.codigo }}) {{ item.nombre }} x{{ item.cantidad }} = ${{ "{:,.0f}".format(item.total) }}</p>
                {% endfor %}
                <a href="/venta/finalizar"><button class="btn-success">FINALIZAR E IMPRIMIR</button></a>
                <a href="/carrito/limpiar"><button style="background:#e74c3c; margin-top:5px;">VACIAR CARRITO</button></a>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# ==============================
# RUTAS DE LÓGICA MEJORADA
# ==============================

@app.route("/")
def index():
    if 'carrito' not in session: session['carrito'] = []
    if 'cliente' not in session: session['cliente'] = {"nombre": "Consumidor Final", "documento": "222222222222"}
    
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM inventario ORDER BY codigo ASC").fetchall()
    his = conn.execute("SELECT * FROM facturas ORDER BY fecha DESC LIMIT 5").fetchall()
    conn.close()
    
    total = sum(item['total'] for item in session['carrito'])
    return render_template_string(HTML_SISTEMA, nombre=NOMBRE_LOCAL, inventario=inv, 
                                   carrito=session['carrito'], total_venta=total, 
                                   cliente=session['cliente'], historial=his)

@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    c = request.form
    conn = get_db_connection()
    # INSERT OR REPLACE permite actualizar si el código ya existe (Edición)
    conn.execute("""INSERT OR REPLACE INTO inventario (codigo, producto, precio, stock, tipo, fecha_registro, fecha_vencimiento) 
                 VALUES (?,?,?,?,?,?,?)""",
                 (c['codigo'], c['producto'].upper(), c['precio'], c['stock'], c['tipo'], 
                  datetime.now().strftime('%Y-%m-%d'), c['vencimiento']))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/inventario/eliminar/<int:codigo>")
def inv_eliminar(codigo):
    conn = get_db_connection()
    conn.execute("DELETE FROM inventario WHERE codigo = ?", (codigo,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    cod = request.form.get("codigo_vta")
    cant = float(request.form.get("cantidad", 0))

    conn = get_db_connection()
    p = conn.execute("SELECT producto, precio, stock FROM inventario WHERE codigo=?", (cod,)).fetchone()
    conn.close()

    if p and p['stock'] >= cant:
        carrito = session.get('carrito', [])
        carrito.append({
            "codigo": cod,
            "nombre": p['producto'], 
            "cantidad": cant, 
            "total": p['precio'] * cant
        })
        session['carrito'] = carrito

    return redirect("/")

@app.route("/venta/finalizar")
def finalizar():
    carrito = session.get('carrito', [])
    if not carrito: return redirect("/")
    
    total = sum(item['total'] for item in carrito)
    sub = total / (1 + VALOR_IVA)
    iva = total - sub
    cliente = session.get('cliente')
    
    detalles = "|".join([f"{i['nombre']},{i['cantidad']},{i['total']}" for i in carrito])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO facturas (subtotal, iva, total, cliente_nombre, cliente_documento, detalles_json) 
                      VALUES (?,?,?,?,?,?)""", 
                   (sub, iva, total, cliente['nombre'], cliente['documento'], detalles))
    factura_id = cursor.lastrowid
    
    for item in carrito:
        conn.execute("UPDATE inventario SET stock = stock - ? WHERE producto = ?", (item['cantidad'], item['nombre']))
    
    conn.commit()
    conn.close()
    session['carrito'] = []
    
    return redirect(url_for('generar_pdf', id_factura=factura_id))

@app.route("/factura/pdf/<int:id_factura>")
def generar_pdf(id_factura):
    conn = get_db_connection()
    f = conn.execute("SELECT * FROM facturas WHERE id = ?", (id_factura,)).fetchone()
    conn.close()
    if not f: return "No encontrada", 404

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, NOMBRE_LOCAL, ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 11)
    pdf.cell(100, 7, f"Factura: #{f['id']}")
    pdf.cell(90, 7, f"Fecha: {f['fecha'][:16]}", ln=True, align="R")
    pdf.ln(10)
    
    # Items
    items = f['detalles_json'].split("|")
    for item in items:
        nom, cant, tot = item.split(",")
        pdf.cell(100, 8, nom, 1)
        pdf.cell(40, 8, cant, 1, 0, "C")
        pdf.cell(50, 8, f"${float(tot):,.0f}", 1, 1, "R")

    pdf.ln(10)
    pdf.cell(190, 10, f"TOTAL PAGADO: ${f['total']:,.0f}", 1, 1, "C")

    output = io.BytesIO()
    pdf_out = pdf.output(dest='S')
    output.write(pdf_out)
    output.seek(0)
    return send_file(output, mimetype='application/pdf', download_name=f"Factura_{id_factura}.pdf")

@app.route("/carrito/limpiar")
def car_limpiar():
    session['carrito'] = []
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)