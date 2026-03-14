from flask import Flask, render_template_string, request, redirect, session, send_file, url_for
import sqlite3
from datetime import datetime
import os
from fpdf import FPDF
import io

app = Flask(__name__)
app.secret_key = 'pollo_raul_secret_key'

# === CONFIGURACIÓN LEGAL (DIAN) ===
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_NEGOCIO = "123.456.789-0" 
DIRECCION = "Cúcuta, Norte de Santander"
TELEFONO = "300 000 0000"
VALOR_IVA = 0.19

def get_db_connection():
    db_path = "pos.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Aseguramos que la tabla tenga la columna 'codigo' como llave primaria
        conn.execute("""CREATE TABLE IF NOT EXISTS inventario (
            codigo INTEGER PRIMARY KEY, 
            producto TEXT, 
            precio REAL, 
            stock REAL, 
            tipo TEXT, 
            fecha_registro TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            subtotal REAL, iva REAL, total REAL, 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            cliente_nombre TEXT, 
            cliente_documento TEXT, 
            detalles_json TEXT)""")
        conn.commit()

init_db()

HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ nombre }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 1300px; margin: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
        .full-width { grid-column: 1 / -1; }
        h1, h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
        input, button { width: 100%; padding: 10px; margin: 5px 0; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #3498db; color: white; border: none; font-weight: bold; cursor: pointer; }
        .btn-success { background: #2ecc71; }
        .btn-danger { background: #e74c3c; width: auto; }
        .total-display { font-size: 24px; font-weight: bold; color: #27ae60; text-align: center; padding: 15px; background: #f9fffb; border: 2px dashed #2ecc71; }
        .search-box { background: #e8f4fd; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card full-width" style="text-align:center;">
            <h1>🍗 {{ nombre }}</h1>
            <p>NIT: {{ nit }} | {{ direccion }}</p>
        </div>

        <div class="card">
            <h2>📦 Inventario (Códigos Cortos)</h2>
            <form action="/inventario/guardar" method="POST">
                <input type="number" name="codigo" placeholder="Código (Ej: 1)" required>
                <input type="text" name="producto" placeholder="Producto" required>
                <input type="number" step="0.01" name="precio" placeholder="Precio" required>
                <input type="number" step="0.01" name="stock" placeholder="Stock" required>
                <button type="submit" class="btn-success">Guardar / Actualizar</button>
            </form>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead><tr><th>Cód</th><th>Producto</th><th>Precio</th><th>Stock</th><th>Acción</th></tr></thead>
                    <tbody>
                        {% for p in inventario %}
                        <tr>
                            <td><b>{{ p.codigo }}</b></td>
                            <td>{{ p.producto }}</td>
                            <td>${{ "{:,.0f}".format(p.precio) }}</td>
                            <td>{{ p.stock }}</td>
                            <td><a href="/inventario/eliminar/{{ p.codigo }}"><button class="btn-danger">🗑️</button></a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>🛒 Venta Rápida</h2>
            <form action="/carrito/agregar" method="POST">
                <div style="display:flex; gap:10px;">
                    <input type="number" name="codigo_vta" placeholder="Código..." required autofocus>
                    <input type="number" step="0.01" name="cantidad" placeholder="Cant." required style="width:100px;">
                    <button type="submit" style="width:120px;">Añadir</button>
                </div>
            </form>
            <hr>
            <h3>👤 Datos del Cliente</h3>
            <form action="/cliente/actualizar" method="POST">
                <input type="text" name="nombre" placeholder="Nombre" value="{{ cliente.nombre }}">
                <input type="text" name="documento" placeholder="Cédula/NIT" value="{{ cliente.documento }}">
                <button type="submit" style="background:#95a5a6">Cargar Datos</button>
            </form>
            <div class="total-display">TOTAL: ${{ "{:,.0f}".format(total_venta) }}</div>
            {% if carrito %}
                <a href="/venta/finalizar"><button class="btn-success">GENERAR FACTURA E IMPRIMIR PDF</button></a>
                <a href="/carrito/limpiar"><button style="background:#e74c3c; margin-top:5px;">VACIAR</button></a>
            {% endif %}
        </div>

        <div class="card full-width">
            <h2>📊 Historial y Buscador de Facturas</h2>
            <div class="search-box">
                <form action="/" method="GET" style="display:flex; gap:10px;">
                    <input type="text" name="buscar" placeholder="Buscar por Cédula o Nombre..." value="{{ busqueda }}">
                    <button type="submit" style="width:150px;">🔍 Buscar</button>
                    <a href="/" style="width:150px;"><button type="button" style="background:#95a5a6">Ver Todas</button></a>
                </form>
            </div>
            <table>
                <thead><tr><th>No.</th><th>Fecha</th><th>Cliente</th><th>Cédula</th><th>Total</th><th>Acción</th></tr></thead>
                <tbody>
                    {% for f in historial %}
                    <tr>
                        <td>#{{ f.id }}</td>
                        <td>{{ f.fecha[:16] }}</td>
                        <td>{{ f.cliente_nombre }}</td>
                        <td>{{ f.cliente_documento }}</td>
                        <td><b>${{ "{:,.0f}".format(f.total) }}</b></td>
                        <td><a href="/factura/pdf/{{ f.id }}" target="_blank">📄 Imprimir PDF</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    if 'carrito' not in session: session['carrito'] = []
    if 'cliente' not in session: session['cliente'] = {"nombre": "Consumidor Final", "documento": "222222222222"}
    buscar = request.args.get('buscar', '')
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM inventario ORDER BY codigo ASC").fetchall()
    if buscar:
        query = "SELECT * FROM facturas WHERE cliente_documento LIKE ? OR cliente_nombre LIKE ? ORDER BY fecha DESC"
        his = conn.execute(query, ('%'+buscar+'%', '%'+buscar+'%')).fetchall()
    else:
        his = conn.execute("SELECT * FROM facturas ORDER BY fecha DESC LIMIT 10").fetchall()
    conn.close()
    total = sum(item['total'] for item in session['carrito'])
    return render_template_string(HTML_SISTEMA, nombre=NOMBRE_LOCAL, nit=NIT_NEGOCIO, direccion=DIRECCION, 
                                   inventario=inv, carrito=session['carrito'], total_venta=total, 
                                   cliente=session['cliente'], historial=his, busqueda=buscar)

@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    c = request.form
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO inventario VALUES (?,?,?,?,?,?)",
                 (c['codigo'], c['producto'].upper(), c['precio'], c['stock'], 'Und', datetime.now().strftime('%Y-%m-%d')))
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
        carrito.append({"codigo": cod, "nombre": p['producto'], "cantidad": cant, "total": p['precio'] * cant})
        session['carrito'] = carrito
    return redirect("/")

@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    session['cliente'] = {"nombre": request.form.get("nombre"), "documento": request.form.get("documento")}
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
    cursor.execute("INSERT INTO facturas (subtotal, iva, total, cliente_nombre, cliente_documento, detalles_json) VALUES (?,?,?,?,?,?)", 
                   (sub, iva, total, cliente['nombre'], cliente['documento'], detalles))
    factura_id = cursor.lastrowid
    for item in carrito:
        conn.execute("UPDATE inventario SET stock = stock - ? WHERE codigo = ?", (item['cantidad'], item['codigo']))
    conn.commit()
    conn.close()
    session['carrito'] = []
    return redirect(url_for('generar_pdf', id_factura=factura_id))

@app.route("/factura/pdf/<int:id_factura>")
def generar_pdf(id_factura):
    conn = get_db_connection()
    f = conn.execute("SELECT * FROM facturas WHERE id = ?", (id_factura,)).fetchone()
    conn.close()
    
    pdf = FPDF(format='letter')
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, NOMBRE_LOCAL, ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 7, f"NIT: {NIT_NEGOCIO} | Tel: {TELEFONO}", ln=True, align="C")
    pdf.cell(190, 7, DIRECCION, ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, f"FACTURA DE VENTA No. {f['id']}", border="TB", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 7, f"Fecha: {f['fecha'][:16]}", ln=True)
    pdf.cell(190, 7, f"Cliente: {f['cliente_nombre']}", ln=True)
    pdf.cell(190, 7, f"Cédula/NIT: {f['cliente_documento']}", ln=True)
    pdf.ln(5)
    
    # Encabezado tabla
    pdf.set_font("Arial", "B", 10)
    pdf.cell(100, 8, "Descripción", 1); pdf.cell(30, 8, "Cant.", 1, 0, "C"); pdf.cell(60, 8, "Total", 1, 1, "C")
    
    pdf.set_font("Arial", "", 10)
    items = f['detalles_json'].split("|")
    for item in items:
        nom, cant, tot = item.split(",")
        pdf.cell(100, 7, nom, 1); pdf.cell(30, 7, cant, 1, 0, "C"); pdf.cell(60, 7, f"${float(tot):,.0f}", 1, 1, "R")
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(130, 8, "SUBTOTAL:", 0, 0, "R"); pdf.cell(60, 8, f"${f['subtotal']:,.0f}", 0, 1, "R")
    pdf.cell(130, 8, f"IVA ({VALOR_IVA*100:.0f}%):", 0, 0, "R"); pdf.cell(60, 8, f"${f['iva']:,.0f}", 0, 1, "R")
    pdf.cell(130, 10, "TOTAL NETO:", 0, 0, "R"); pdf.cell(60, 10, f"${f['total']:,.0f}", 1, 1, "R")

    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(190, 5, "Esta factura se asimila en todos sus efectos a una letra de cambio. Gracias por su compra.", align="C")

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