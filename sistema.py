from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# ==============================
# Datos del negocio
# ==============================
NIT_LOCAL = "900.555.222-1"
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
valor_iva = 0.19
numero_de_factura = 1

inventario = {
    "POLLO POR KILO": {"precio": 18000, "stock": 40.0, "tipo": "Peso"},
    "CUBETA HUEVOS": {"precio": 16000, "stock": 10.0, "tipo": "Unidad"},
    "QUESO CAMPESINO": {"precio": 12000, "stock": 15.0, "tipo": "Peso"},
    "CHORIZO X UNID": {"precio": 3500, "stock": 30.0, "tipo": "Unidad"}
}

carrito_de_compras = []
suma_total_cuenta = 0

# ==============================
# Plantillas HTML con CSS moderno
# ==============================
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ negocio }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #2c3e50; }
        .card { background: white; padding: 20px; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); max-width: 600px; }
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
                    <option value="{{ p }}">{{ p }} - ${{ d['precio'] }} (Stock: {{ d['stock'] }})</option>
                {% endfor %}
            </select>
            <input type="number" step="0.1" name="cantidad" placeholder="Cantidad">
            <button type="submit">Agregar al carrito</button>
        </form>
    </div>

    <div class="card">
        <h2>Carrito</h2>
        <ul>
            {% for item in carrito %}
                <li>{{ item[1] }} x {{ item[0] }} = ${{ "{:,.0f}".format(item[3]) }}</li>
            {% endfor %}
        </ul>
        <p class="total">Total: ${{ "{:,.0f}".format(total) }}</p>
        <div class="links">
            <a href="/factura">🧾 Generar Factura</a> | <a href="/reset">🔄 Nueva Venta</a>
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
        .factura { max-width: 600px; margin: auto; border: 1px solid #ccc; padding: 20px; border-radius: 8px; }
        ul { list-style: none; padding: 0; }
        li { padding: 5px 0; border-bottom: 1px solid #eee; }
        .totales { margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="factura">
        <h1>{{ factura.negocio }}</h1>
        <p>NIT: {{ factura.nit }}</p>
        <p>Factura No: {{ factura.numero }}</p>
        <hr>
        <ul>
            {% for item in factura.carrito %}
                <li>{{ item[1] }} x {{ item[0] }} = ${{ "{:,.0f}".format(item[3]) }}</li>
            {% endfor %}
        </ul>
        <div class="totales">
            <p>Subtotal: ${{ "{:,.0f}".format(factura.subtotal) }}</p>
            <p>IVA: ${{ "{:,.0f}".format(factura.iva) }}</p>
            <p>Total: ${{ "{:,.0f}".format(factura.total) }}</p>
        </div>
        <hr>
        <p style="text-align:center;">¡Gracias por su compra!</p>
    </div>
</body>
</html>
"""

# ==============================
# Rutas Flask
# ==============================
@app.route("/")
def home():
    return render_template_string(INDEX_HTML, negocio=NOMBRE_LOCAL, inventario=inventario, carrito=carrito_de_compras, total=suma_total_cuenta)

@app.route("/agregar", methods=["POST"])
def agregar():
    global suma_total_cuenta
    producto = request.form.get("producto")
    cantidad = float(request.form.get("cantidad"))

    if producto in inventario and cantidad > 0 and inventario[producto]["stock"] >= cantidad:
        inventario[producto]["stock"] -= cantidad
        precio_item = inventario[producto]["precio"]
        total_item = precio_item * cantidad
        suma_total_cuenta += total_item
        carrito_de_compras.append([producto, cantidad, precio_item, total_item])
    return redirect("/")

@app.route("/factura")
def factura():
    global numero_de_factura
    subtotal_sin_iva = suma_total_cuenta / (1 + valor_iva)
    iva_calculado = suma_total_cuenta - subtotal_sin_iva
    factura_data = {
        "numero": numero_de_factura,
        "subtotal": subtotal_sin_iva,
        "iva": iva_calculado,
        "total": suma_total_cuenta,
        "carrito": carrito_de_compras,
        "negocio": NOMBRE_LOCAL,
        "nit": NIT_LOCAL
    }
    numero_de_factura += 1
    return render_template_string(FACTURA_HTML, factura=factura_data)

@app.route("/reset")
def reset():
    global carrito_de_compras, suma_total_cuenta
    carrito_de_compras = []
    suma_total_cuenta = 0
    return redirect("/")

# ==============================
# Configuración para Vercel
# ==============================
# requirements.txt -> flask
# vercel.json ->
# {
#   "builds": [{ "src": "app.py", "use": "@vercel/python" }],
#   "routes": [{ "src": "/(.*)", "dest": "app.py" }]
# }

if __name__ == "__main__":
    app.run(debug=True)