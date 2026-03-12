from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ==============================
# Datos del negocio
# ==============================
NIT_LOCAL = "900.555.222-1"
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
valor_iva = 0.19

carrito_de_compras = []
suma_total_cuenta = 0
cliente_nombre = ""
cliente_documento = ""

# ==============================
# Inicialización de la base de datos
# ==============================
def init_db():
    conn = sqlite3.connect("pos.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS inventario (
        producto TEXT PRIMARY KEY,
        precio REAL,
        stock REAL,
        tipo TEXT,
        fecha_expedicion TEXT,
        fecha_vencimiento TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS facturas (
        numero INTEGER PRIMARY KEY AUTOINCREMENT,
        subtotal REAL,
        iva REAL,
        total REAL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cliente_nombre TEXT,
        cliente_documento TEXT
    )""")
    conn.commit()
    conn.close()

def seed_inventario():
    conn = sqlite3.connect("pos.db")
    c = conn.cursor()
    productos = [
        ("POLLO POR KILO", 18000, 40.0, "Peso", "2026-03-01", "2026-03-20"),
        ("CUBETA HUEVOS", 16000, 10.0, "Unidad", "2026-03-05", "2026-03-25"),
        ("QUESO CAMPESINO", 12000, 15.0, "Peso", "2026-03-02", "2026-03-18"),
        ("CHORIZO X UNID", 3500, 30.0, "Unidad", "2026-03-07", "2026-03-30")
    ]
    for p in productos:
        c.execute("INSERT OR IGNORE INTO inventario VALUES (?, ?, ?, ?, ?, ?)", p)
    conn.commit()
    conn.close()

def cargar_inventario():
    conn = sqlite3.connect("pos.db")
    c = conn.cursor()
    c.execute("SELECT producto, precio, stock, tipo, fecha_expedicion, fecha_vencimiento FROM inventario")
    data = {row[0]: {"precio": row[1], "stock": row[2], "tipo": row[3],
                     "fecha_expedicion": row[4], "fecha_vencimiento": row[5]} for row in c.fetchall()}
    conn.close()
    return data

init_db()
seed_inventario()

# ==============================
# Plantillas HTML
# ==============================
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ negocio }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #2c3e50; }
        .card { background: white; padding: 20px; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); max-width: 700px; }
        select, input, button { padding: 10px; margin: 5px 0; width: 100%; border-radius: 5px; border: 1px solid #ccc; }
        button { background: #3498db; color: white; border: none; cursor: pointer; }
        button:hover { background: #2980b9; }
        ul { list-style: none; padding: 0; }
        li { padding: 5px 0; border-bottom: 1px solid #eee; }
        .total { font-weight: bold; color: #27ae60; }
        .links a { margin: 10px; text-decoration: none; color: #3498db; }
    </style>
</head>
<body>
    <h1>{{ negocio }}</h1>
    <div class="card">
        <h2>Inventario</h2>
        <form action="/agregar" method="post">
            <select name="producto">
                {% for p, d in inventario.items() %}
                    <option value="{{ p }}">
                        {{ p }} - ${{ d['precio'] }} 
                        (Stock: {{ d['stock'] }} {{ d['tipo'] }}) 
                        | Expedición: {{ d['fecha_expedicion'] }} 
                        | Vence: {{ d['fecha_vencimiento'] }}
                    </option>
                {% endfor %}
            </select>
            <input type="number" step="0.1" name="cantidad" placeholder="Cantidad">
            <button type="submit">Agregar al carrito</button>
        </form>
    </div>

    <div class="card">
        <h2>Datos del Cliente</h2>
        <form action="/cliente" method="post">
            <input type="text" name="nombre" placeholder="Nombre del Cliente" required>
            <input type="text" name="documento" placeholder="Documento (CC/NIT)" required>
            <button type="submit">Guardar Cliente</button>
        </form>
    </div>

    <div class="card">
        <h2>Carrito</h2>
        <ul>
            {% for item in carrito %}
                <li>{{ item[1] }} {{ item[4] }} de {{ item[0] }} = ${{ "{:,.0f}".format(item[3]) }}</li>
            {% endfor %}
        </ul>
        <p class="total">Total: ${{ "{:,.0f}".format(total) }}</p>
        <div class="links">
            <a href="/factura">🧾 Generar Factura</a> | <a href="/reset">🔄 Nueva Venta</a> | <a href="/ventas">📊 Historial</a>
        </div>
    </div>
</body>
</html>
"""

FACTURA_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Factura {{ factura.numero }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #fff; padding: 20px; }
        h1 { text-align: center; color: #2c3e50; }
        .factura { max-width: 700px; margin: auto; border: 1px solid #ccc; padding: 20px; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background: #f4f6f9; }
        .totales { margin-top: 20px; font-weight: bold; text-align: right; }
    </style>
</head>
<body>
    <div class="factura">
        <h1>{{ factura.negocio }}</h1>
        <p>NIT: {{ factura.nit }}</p>
        <p>Dirección: Calle 10 #15-20, Cúcuta</p>
        <p>Teléfono: 3001234567</p>
        <p>Factura No: {{ factura.numero }}</p>
        <p>Fecha Expedición: {{ factura.fecha }}</p>
        <hr>
        <p><strong>Cliente:</strong> {{ factura.cliente_nombre }} - CC/NIT: {{ factura.cliente_documento }}</p>
        <table>
            <tr>
                <th>Cantidad</th>
                <th>Descripción</th>
                <th>Precio Unitario</th>
                <th>Total</th>
            </tr>
            {% for item in factura.carrito %}
            <tr>
                <td>{{ item[1] }}</td>
                <td>{{ item[0] }}</td>
                <td>${{ "{:,.0f}".format(item[2]) }}</td>
                <td>${{ "{:,.0f}".format(item[3]) }}</td>
            </tr>
            {% endfor %}
        </table>
        <div class="totales">
            <p>Subtotal: ${{ "{:,.0f}".format(factura.subtotal) }}</p>
            <p>IVA (19%): ${{ "{:,.0f}".format(factura.iva) }}</p>
            <p>Total a Pagar: ${{ "{:,.0f}".format(factura.total) }}</p>
        </div>
        <hr>
        <p>Resolución DIAN No. 123456789 - Vigencia: 2026</p>
        <p style="text-align:center;">¡Gracias por su compra!</p>
    </div>
</body>
</html>
"""

VENTAS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Historial de Ventas</title>
    <style>
        body { font-family: Arial, sans-serif;
</table>
        <br>
        <a href="/">Volver al Inicio</a>
    </div>
</body>
</html>
"""

# ==============================
# Rutas de la Aplicación
# ==============================

@app.route("/")
def index():
    inventario = cargar_inventario()
    return render_template_string(INDEX_HTML, 
                                 negocio=NOMBRE_LOCAL, 
                                 inventario=inventario, 
                                 carrito=carrito_de_compras, 
                                 total=suma_total_cuenta)

@app.route("/agregar", methods=["POST"])
def agregar():
    global suma_total_cuenta
    producto_nombre = request.form.get("producto")
    cantidad = float(request.form.get("cantidad", 0))
    
    inventario = cargar_inventario()
    if producto_nombre in inventario and cantidad > 0:
        datos = inventario[producto_nombre]
        precio_unitario = datos["precio"]
        tipo = datos["tipo"]
        total_item = precio_unitario * cantidad
        
        # Guardar en el carrito: [Nombre, Cantidad, Precio Unid, Total, Tipo]
        carrito_de_compras.append([producto_nombre, cantidad, precio_unitario, total_item, tipo])
        suma_total_cuenta += total_item
        
    return redirect("/")

@app.route("/cliente", methods=["POST"])
def cliente():
    global cliente_nombre, cliente_documento
    cliente_nombre = request.form.get("nombre")
    cliente_documento = request.form.get("documento")
    return redirect("/")

@app.route("/factura")
def factura():
    if not carrito_de_compras:
        return redirect("/")
        
    subtotal = suma_total_cuenta / (1 + valor_iva)
    iva_calculado = suma_total_cuenta - subtotal
    
    # Guardar en la base de datos
    conn = sqlite3.connect("pos.db")
    c = conn.cursor()
    c.execute("INSERT INTO facturas (subtotal, iva, total, cliente_nombre, cliente_documento) VALUES (?, ?, ?, ?, ?)",
              (subtotal, iva_calculado, suma_total_cuenta, cliente_nombre, cliente_documento))
    factura_id = c.lastrowid
    conn.commit()
    conn.close()
    
    datos_factura = {
        "numero": factura_id,
        "negocio": NOMBRE_LOCAL,
        "nit": NIT_LOCAL,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cliente_nombre": cliente_nombre,
        "cliente_documento": cliente_documento,
        "carrito": carrito_de_compras,
        "subtotal": subtotal,
        "iva": iva_calculado,
        "total": suma_total_cuenta
    }
    return render_template_string(FACTURA_HTML, factura=datos_factura)

@app.route("/reset")
def reset():
    global carrito_de_compras, suma_total_cuenta, cliente_nombre, cliente_documento
    carrito_de_compras = []
    suma_total_cuenta = 0
    cliente_nombre = ""
    cliente_documento = ""
    return redirect("/")

@app.route("/ventas")
def ventas():
    conn = sqlite3.connect("pos.db")
    c = conn.cursor()
    c.execute("SELECT * FROM facturas ORDER BY fecha DESC")
    historial = c.fetchall()
    conn.close()
    return render_template_string(VENTAS_HTML, ventas=historial)

# ==============================
# Ejecución del Servidor
# ==============================
if __name__ == "__main__":
    app.run(debug=True)