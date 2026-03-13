from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ==============================
# CONFIGURACIÓN DEL NEGOCIO
# ==============================
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
VALOR_IVA = 0.19
carrito_de_compras = []
cliente_actual = {"nombre": "Consumidor Final", "documento": "222222222222"}

def get_db_connection():
    conn = sqlite3.connect("pos.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea y actualiza la base de datos automáticamente"""
    with get_db_connection() as conn:
        # Tabla Inventario
        conn.execute("""CREATE TABLE IF NOT EXISTS inventario (
            producto TEXT PRIMARY KEY, precio REAL, stock REAL, tipo TEXT,
            fecha_expedicion TEXT, fecha_vencimiento TEXT)""")
        
        # Tabla Facturas (Historial)
        conn.execute("""CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            subtotal REAL, iva REAL, total REAL, 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre TEXT, 
            cliente_documento TEXT)""")
        
        # REPARACIÓN: Si la tabla ya existía pero le faltaban columnas de cliente
        try:
            conn.execute("ALTER TABLE facturas ADD COLUMN cliente_nombre TEXT")
        except sqlite3.OperationalError: pass
        try:
            conn.execute("ALTER TABLE facturas ADD COLUMN cliente_documento TEXT")
        except sqlite3.OperationalError: pass
        
        conn.commit()

# ==============================
# INTERFAZ PROFESIONAL (HTML/CSS)
# ==============================
HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ nombre }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
        .full-width { grid-column: 1 / -1; }
        h1, h2 { color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; border-bottom: 1px solid #eee; text-align: left; }
        th { background: #f8f9fa; color: #7f8c8d; }
        input, select, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; font-size: 14px; }
        button { background: #3498db; color: white; border: none; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #2980b9; transform: translateY(-1px); }
        .btn-success { background: #2ecc71; }
        .btn-success:hover { background: #27ae60; }
        .total-display { font-size: 24px; font-weight: bold; color: #27ae60; margin: 15px 0; border: 2px dashed #2ecc71; padding: 10px; text-align: center; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background: #e8f4fd; color: #3498db; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card full-width">
            <h1 style="border:none; margin:0; text-align:center;">🍗 {{ nombre }} - Punto de Venta</h1>
        </div>

        <div class="card">
            <h2>📦 Gestión de Inventario</h2>
            <form action="/inventario/agregar" method="POST">
                <input type="text" name="producto" placeholder="Nombre del Producto (ej: Muslos)" required>
                <div style="display:flex; gap:10px;">
                    <input type="number" step="0.01" name="precio" placeholder="Precio de Venta" required>
                    <input type="number" step="0.01" name="stock" placeholder="Cantidad / Peso" required>
                </div>
                <select name="tipo">
                    <option value="Kg">Kilogramos (Kg)</option>
                    <option value="Und">Unidades (Und)</option>
                </select>
                <label style="font-size:12px; color:#666;">Fecha de Vencimiento:</label>
                <input type="date" name="vencimiento" required>
                <button type="submit" class="btn-success">Guardar en Inventario</button>
            </form>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead><tr><th>Producto</th><th>Precio</th><th>Stock</th></tr></thead>
                    <tbody>
                        {% for p in inventario %}
                        <tr>
                            <td>{{ p.producto }}</td>
                            <td>${{ "{:,.0f}".format(p.precio) }}</td>
                            <td><span class="badge">{{ p.stock }} {{ p.tipo }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>🛒 Nueva Venta</h2>
            <form action="/carrito/agregar" method="POST">
                <input type="text" list="prods" name="producto" placeholder="Escriba para buscar producto..." required>
                <datalist id="prods">
                    {% for p in inventario %}<option value="{{ p.producto }}">{% endfor %}
                </datalist>
                <input type="number" step="0.01" name="cantidad" placeholder="Cantidad / Peso a vender" required>
                <button type="submit">Agregar al Carrito</button>
            </form>
            <hr>
            <h3>👤 Cliente: {{ cliente.nombre }}</h3>
            <form action="/cliente/actualizar" method="POST">
                <div style="display:flex; gap:10px;">
                    <input type="text" name="nombre" placeholder="Nombre">
                    <input type="text" name="documento" placeholder="Cédula / NIT">
                </div>
                <button type="submit" style="background:#95a5a6">Vincular Cliente</button>
            </form>
            <hr>
            <div class="total-display">TOTAL: ${{ "{:,.0f}".format(total_venta) }}</div>
            {% if carrito %}
            <div style="max-height: 150px; overflow-y: auto; margin-bottom: 10px; font-size: 13px;">
                {% for item in carrito %}
                <p>✅ {{ item.cantidad }} x {{ item.nombre }} = ${{ "{:,.0f}".format(item.total) }}</p>
                {% endfor %}
            </div>
            <a href="/venta/finalizar"><button class="btn-success">✅ FINALIZAR Y GUARDAR FACTURA</button></a>
            {% endif %}
        </div>

        <div class="card full-width">
            <h2>📊 Historial de Facturas Recientes</h2>
            <table>
                <thead>
                    <tr><th>ID</th><th>Fecha</th><th>Cliente</th><th>Subtotal</th><th>IVA (19%)</th><th>Total</th></tr>
                </thead>
                <tbody>
                    {% for f in historial %}
                    <tr>
                        <td>#{{ f.id }}</td>
                        <td>{{ f.fecha[:16] }}</td>
                        <td>{{ f.cliente_nombre }}</td>
                        <td>${{ "{:,.0f}".format(f.subtotal) }}</td>
                        <td>${{ "{:,.0f}".format(f.iva) }}</td>
                        <td><strong>${{ "{:,.0f}".format(f.total) }}</strong></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# ==============================
# LÓGICA DE CONTROL (RUTAS)
# ==============================
@app.route("/")
def index():
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM inventario ORDER BY producto ASC").fetchall()
    his = conn.execute("SELECT * FROM facturas ORDER BY fecha DESC LIMIT 15").fetchall()
    conn.close()
    total = sum(item['total'] for item in carrito_de_compras)
    return render_template_string(HTML_SISTEMA, nombre=NOMBRE_LOCAL, inventario=inv, 
                                 carrito=carrito_de_compras, total_venta=total, 
                                 cliente=cliente_actual, historial=his)

@app.route("/inventario/agregar", methods=["POST"])
def inv_agregar():
    p = request.form
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO inventario VALUES (?,?,?,?,?,?)",
                 (p['producto'].upper(), p['precio'], p['stock'], p['tipo'], 
                  datetime.now().strftime('%Y-%m-%d'), p['vencimiento']))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    nombre = request.form.get("producto").upper()
    cant = float(request.form.get("cantidad", 0))
    conn = get_db_connection()
    p = conn.execute("SELECT precio FROM inventario WHERE producto=?", (nombre,)).fetchone()
    conn.close()
    if p:
        carrito_de_compras.append({"nombre": nombre, "cantidad": cant, "total": p['precio'] * cant})
    return redirect("/")

@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    cliente_actual['nombre'] = request.form.get("nombre") or "Consumidor Final"
    cliente_actual['documento'] = request.form.get("documento") or "222222222222"
    return redirect("/")

@app.route("/venta/finalizar")
def finalizar():
    if not carrito_de_compras: return redirect("/")
    
    total = sum(item['total'] for item in carrito_de_compras)
    sub = total / (1 + VALOR_IVA)
    iva = total - sub
    
    conn = get_db_connection()
    # Guardar Factura
    conn.execute("""INSERT INTO facturas (subtotal, iva, total, cliente_nombre, cliente_documento) 
                 VALUES (?,?,?,?,?)""", 
                 (sub, iva, total, cliente_actual['nombre'], cliente_actual['documento']))
    
    # Descontar del Inventario
    for item in carrito_de_compras:
        conn.execute("UPDATE inventario SET stock = stock - ? WHERE producto = ?", 
                    (item['cantidad'], item['nombre']))
    
    conn.commit()
    conn.close()
    carrito_de_compras.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)