
from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# ==============================
# CONFIGURACIÓN Y DATOS DEL LOCAL
# ==============================
NIT_LOCAL = "900.555.222-1"
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
VALOR_IVA = 0.19

carrito_de_compras = []
cliente_actual = {"nombre": "Consumidor Final", "documento": "222222222222"}

# ==============================
# GESTIÓN DE BASE DE DATOS
# ==============================
def get_db_connection():
    conn = sqlite3.connect("pos.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Tabla Inventario
        conn.execute("""CREATE TABLE IF NOT EXISTS inventario (
            producto TEXT PRIMARY KEY, precio REAL, stock REAL, tipo TEXT,
            fecha_expedicion TEXT, fecha_vencimiento TEXT)""")
        
        # Tabla Facturas (CORREGIDA con cliente_nombre y cliente_documento)
        conn.execute("""CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, subtotal REAL, iva REAL,
            total REAL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre TEXT, cliente_documento TEXT)""")
        
        # Datos de prueba iniciales
        productos = [
            ("POLLO POR KILO", 18000, 40.0, "Kg", "2026-03-01", "2026-03-25"),
            ("CUBETA HUEVOS", 16000, 3.0, "Und", "2026-03-05", "2026-03-28"), # Alerta Stock
            ("QUESO CAMPESINO", 12000, 15.0, "Kg", "2026-03-02", "2026-03-14"), # Alerta Vence
            ("CHORIZO X UNID", 3500, 30.0, "Und", "2026-03-07", "2026-03-30")
        ]
        conn.executemany("INSERT OR IGNORE INTO inventario VALUES (?,?,?,?,?,?)", productos)
        conn.commit()

# ==============================
# DISEÑO Y ESTILOS (HTML/CSS)
# ==============================
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ negocio }}</title>
    <style>
        :root { --p: #2c3e50; --s: #3498db; --ok: #27ae60; --err: #e74c3c; --warn: #f39c12; }
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .full { grid-column: 1 / -1; }
        h1, h2 { color: var(--p); margin-top: 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }
        .alert-stock { background: #fff3cd; color: #856404; font-weight: bold; border-radius: 4px; padding: 2px; }
        .alert-vence { background: #f8d7da; color: #721c24; font-weight: bold; border-radius: 4px; padding: 2px; }
        input, select, button { width: 100%; padding: 10px; margin: 5px 0; border-radius: 5px; border: 1px solid #ddd; }
        button { background: var(--s); color: white; border: none; cursor: pointer; font-weight: bold; }
        .btn-vender { background: var(--ok); font-size: 1.2em; margin-top: 10px; }
        .total { font-size: 1.5em; color: var(--ok); font-weight: bold; text-align: right; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="full">🍗 {{ negocio }} <small style="font-size: 0.4em;">NIT: {{ nit }}</small></h1>

        <div class="card full">
            <h2>📦 Inventario con Alertas</h2>
            <table>
                <tr><th>Producto</th><th>Precio</th><th>Stock</th><th>Vencimiento</th></tr>
                {% for p in inventario %}
                <tr>
                    <td>{{ p.producto }}</td>
                    <td>${{ "{:,.0f}".format(p.precio) }}</td>
                    <td><span class="{{ 'alert-stock' if p.stock <= 5 else '' }}">{{ p.stock }} {{ p.tipo }}</span></td>
                    <td><span class="{{ 'alert-vence' if p.alerta_vence else '' }}">{{ p.fecha_vencimiento }}</span></td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h2>🛒 Vender</h2>
            <form action="/agregar" method="POST">
                <select name="producto">
                    {% for p in inventario %}
                    <option value="{{ p.producto }}">{{ p.producto }} (${{ p.precio }})</option>
                    {% endfor %}
                </select>
                <input type="number" step="0.01" name="cantidad" placeholder="Cantidad" required>
                <button type="submit">Añadir al Carrito</button>
            </form>
            <hr>
            <h3>👤 Datos Cliente</h3>
            <form action="/cliente" method="POST">
                <input type="text" name="nombre" placeholder="Nombre" value="{{ cliente.nombre }}">
                <input type="text" name="documento" placeholder="NIT/CC" value="{{ cliente.documento }}">
                <button type="submit" style="background: #95a5a6;">Actualizar Datos</button>
            </form>
        </div>

        <div class="card">
            <h2>📋 Detalle</h2>
            <ul>
                {% for item in carrito %}
                <li>{{ item.cantidad }} x {{ item.nombre }} = ${{ "{:,.0f}".format(item.total) }}</li>
                {% endfor %}
            </ul>
            <p class="total">Total: ${{ "{:,.0f}".format(total_venta) }}</p>
            {% if carrito %}
            <a href="/facturar"><button class="btn-vender">✅ FACTURAR</button></a>
            <a href="/reset" style="text-decoration:none;"><button style="background:var(--err); margin-top:5px;">Borrar Carrito</button></a>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# ==============================
# RUTAS DE LA APLICACIÓN
# ==============================
@app.route("/")
def index():
    conn = get_db_connection()
    productos = conn.execute("SELECT * FROM inventario").fetchall()
    conn.close()

    # Lógica de alertas de vencimiento (3 días)
    hoy = datetime.now()
    inv_final = []
    for p in productos:
        p_dict = dict(p)
        f_vence = datetime.strptime(p['fecha_vencimiento'], '%Y-%m-%d')
        p_dict['alerta_vence'] = (f_vence - hoy).days <= 3
        inv_final.append(p_dict)

    total_carrito = sum(item['total'] for item in carrito_de_compras)
    return render_template_string(INDEX_HTML, negocio=NOMBRE_LOCAL, nit=NIT_LOCAL,
                                 inventario=inv_final, carrito=carrito_de_compras, 
                                 total_venta=total_carrito, cliente=cliente_actual)

@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form.get("producto")
    cantidad = float(request.form.get("cantidad", 0))
    if cantidad > 0:
        conn = get_db_connection()
        prod = conn.execute("SELECT precio FROM inventario WHERE producto=?", (nombre,)).fetchone()
        conn.close()
        if prod:
            carrito_de_compras.append({"nombre": nombre, "cantidad": cantidad, 
                                       "precio": prod['precio'], "total": prod['precio']*cantidad})
    return redirect("/")

@app.route("/cliente", methods=["POST"])
def cliente():
    cliente_actual['nombre'] = request.form.get("nombre")
    cliente_actual['documento'] = request.form.get("documento")
    return redirect("/")

@app.route("/facturar")
def facturar():
    if not carrito_de_compras: return redirect("/")
    
    total = sum(item['total'] for item in carrito_de_compras)
    subtotal = total / (1 + VALOR_IVA)
    iva = total - subtotal

    conn = get_db_connection()
    # 1. Guardar en historial
    conn.execute("INSERT INTO facturas (subtotal, iva, total, cliente_nombre, cliente_documento) VALUES (?,?,?,?,?)",
                 (subtotal, iva, total, cliente_actual['nombre'], cliente_actual['documento']))
    
    # 2. Descontar Inventario
    for item in carrito_de_compras:
        conn.execute("UPDATE inventario SET stock = stock - ? WHERE producto = ?", 
                     (item['cantidad'], item['nombre']))
    
    conn.commit()
    conn.close()
    carrito_de_compras.clear()
    return redirect("/")

@app.route("/reset")
def reset():
    carrito_de_compras.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)