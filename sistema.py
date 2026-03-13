from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ==============================
# CONFIGURACIÓN DEL NEGOCIO
# ==============================
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_LOCAL = "900.555.222-1"
VALOR_IVA = 0.19

# Variables temporales para la sesión actual
carrito_de_compras = []
cliente_actual = {"nombre": "Consumidor Final", "documento": "222222222222"}

def get_db_connection():
    conn = sqlite3.connect("pos.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea las tablas y repara la base de datos si le faltan columnas"""
    with get_db_connection() as conn:
        # 1. Tabla Inventario
        conn.execute("""CREATE TABLE IF NOT EXISTS inventario (
            producto TEXT PRIMARY KEY, 
            precio REAL, 
            stock REAL, 
            tipo TEXT,
            fecha_expedicion TEXT, 
            fecha_vencimiento TEXT)""")
        
        # 2. Tabla Facturas (Historial)
        conn.execute("""CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            subtotal REAL, 
            iva REAL, 
            total REAL, 
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre TEXT, 
            cliente_documento TEXT)""")
        
        # 3. Tabla Clientes (Directorio)
        conn.execute("""CREATE TABLE IF NOT EXISTS clientes (
            documento TEXT PRIMARY KEY, 
            nombre TEXT)""")
        
        # REPARACIÓN: Si la tabla facturas ya existía pero no tenía estas columnas, las agregamos
        try:
            conn.execute("ALTER TABLE facturas ADD COLUMN cliente_nombre TEXT")
        except sqlite3.OperationalError: pass
        
        try:
            conn.execute("ALTER TABLE facturas ADD COLUMN cliente_documento TEXT")
        except sqlite3.OperationalError: pass

        conn.commit()

# ==============================
# INTERFAZ VISUAL (HTML/CSS)
# ==============================
HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ nombre }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 1100px; margin: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .full-width { grid-column: 1 / -1; }
        h1, h2 { color: #2c3e50; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; border-bottom: 1px solid #eee; text-align: left; }
        input, select, button { width: 100%; padding: 10px; margin: 8px 0; border-radius: 5px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #3498db; color: white; border: none; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #2980b9; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219150; }
        .badge-red { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card full-width">
            <h1>🍗 {{ nombre }} - Panel de Gestión</h1>
        </div>

        <div class="card">
            <h2>📦 Agregar al Inventario</h2>
            <form action="/inventario/agregar" method="POST">
                <input type="text" name="producto" placeholder="Nombre del Producto (ej: Muslos)" required>
                <input type="number" step="0.01" name="precio" placeholder="Precio de Venta" required>
                <input type="number" step="0.01" name="stock" placeholder="Cantidad / Peso Inicial" required>
                <select name="tipo">
                    <option value="Kg">Kilogramos (Kg)</option>
                    <option value="Und">Unidades (Und)</option>
                </select>
                <label>Fecha de Vencimiento:</label>
                <input type="date" name="vencimiento" required>
                <button type="submit" class="btn-success">Guardar Producto</button>
            </form>
            <hr>
            <h3>Stock Actual</h3>
            <table>
                <tr><th>Producto</th><th>Precio</th><th>Stock</th></tr>
                {% for p in inventario %}
                <tr>
                    <td>{{ p.producto }}</td>
                    <td>${{ "{:,.0f}".format(p.precio) }}</td>
                    <td class="{{ 'badge-red' if p.stock <= 3 else '' }}">{{ p.stock }} {{ p.tipo }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h2>🛒 Realizar Venta</h2>
            <form action="/carrito/agregar" method="POST">
                <select name="producto">
                    {% for p in inventario %}
                    <option value="{{ p.producto }}">{{ p.producto }} (${{ p.precio }})</option>
                    {% endfor %}
                </select>
                <input type="number" step="0.01" name="cantidad" placeholder="Cantidad a vender" required>
                <button type="submit">Añadir al Carrito</button>
            </form>
            <hr>
            <h3>👤 Cliente</h3>
            <form action="/cliente/actualizar" methods=["POST"]> <input type="text" name="nombre" placeholder="Nombre" value="{{ cliente.nombre }}">
                <input type="text" name="documento" placeholder="CC / NIT" value="{{ cliente.documento }}">
                <button type="submit" style="background:#95a5a6">Vincular Cliente</button>
            </form>
            <hr>
            <h3>🧾 Detalle:</h3>
            <ul>
                {% for item in carrito %}
                <li>{{ item.cantidad }} x {{ item.nombre }} = ${{ "{:,.0f}".format(item.total) }}</li>
                {% endfor %}
            </ul>
            <h2 style="color: #27ae60;">Total: ${{ "{:,.0f}".format(total_venta) }}</h2>
            {% if carrito %}
            <a href="/venta/finalizar"><button class="btn-success">✅ CERRAR VENTA Y GUARDAR</button></a>
            {% endif %}
        </div>

        <div class="card full-width">
            <h2>📊 Historial de Ventas Recientes</h2>
            <table>
                <tr><th>ID</th><th>Fecha</th><th>Cliente</th><th>Total</th></tr>
                {% for f in historial %}
                <tr>
                    <td>#{{ f.id }}</td>
                    <td>{{ f.fecha[:16] }}</td>
                    <td>{{ f.cliente_nombre }}</td>
                    <td>${{ "{:,.0f}".format(f.total) }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""

# ==============================
# LOGICA Y RUTAS (FLASK)
# ==============================
@app.route("/")
def index():
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM inventario").fetchall()
    his = conn.execute("SELECT * FROM facturas ORDER BY fecha DESC LIMIT 10").fetchall()
    conn.close()
    
    total_c = sum(item['total'] for item in carrito_de_compras)
    return render_template_string(HTML_SISTEMA, 
                                 nombre=NOMBRE_LOCAL, 
                                 inventario=inv, 
                                 carrito=carrito_de_compras, 
                                 total_venta=total_c, 
                                 cliente=cliente_actual,
                                 historial=his)

@app.route("/inventario/agregar", methods=["POST"])
def inv_agregar():
    p = request.form
    conn = get_db_connection()
    conn.execute("""INSERT OR REPLACE INTO inventario 
                 (producto, precio, stock, tipo, fecha_expedicion, fecha_vencimiento) 
                 VALUES (?, ?, ?, ?, ?, ?)""",
                 (p['producto'].upper(), p['precio'], p['stock'], p['tipo'], 
                  datetime.now().strftime('%Y-%m-%d'), p['vencimiento']))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    nombre = request.form.get("producto")
    cantidad = float(request.form.get("cantidad", 0))
    conn = get_db_connection()
    prod = conn.execute("SELECT precio FROM inventario WHERE producto=?", (nombre,)).fetchone()
    conn.close()
    if prod:
        carrito_de_compras.append({"nombre": nombre, "cantidad": cantidad, "total": prod['precio'] * cantidad})
    return redirect("/")

@app.route("/cliente/actualizar", methods=["POST"])
def cli_actualizar():
    cliente_actual['nombre'] = request.form.get("nombre")
    cliente_actual['documento'] = request.form.get("documento")
    return redirect("/")

@app.route("/venta/finalizar")
def venta_finalizar():
    if not carrito_de_compras: return redirect("/")
    
    total = sum(item['total'] for item in carrito_de_compras)
    sub = total / (1 + VALOR_IVA)
    iva = total - sub

    conn = get_db_connection()
    # 1. Guardar en Historial
    conn.execute("""INSERT INTO facturas (subtotal, iva, total, cliente_nombre, cliente_documento) 
                 VALUES (?,?,?,?,?)""", 
                 (sub, iva, total, cliente_actual['nombre'], cliente_actual['documento']))
    
    # 2. Guardar Cliente en el directorio
    conn.execute("INSERT OR REPLACE INTO clientes (documento, nombre) VALUES (?,?)",
                 (cliente_actual['documento'], cliente_actual['nombre']))
    
    # 3. Descontar del Inventario
    for item in carrito_de_compras:
        conn.execute("UPDATE inventario SET stock = stock - ? WHERE producto = ?", 
                    (item['cantidad'], item['nombre']))
    
    conn.commit()
    conn.close()
    carrito_de_compras.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db() # Ejecuta la creación y reparación al encender
    app.run(debug=True)