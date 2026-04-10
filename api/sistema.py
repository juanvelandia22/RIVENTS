from flask import Flask, render_template_string, request, redirect, session, send_file, url_for, jsonify
from supabase import create_client, Client
from datetime import datetime
import os
from fpdf import FPDF
import io

app = Flask(__name__)
app.secret_key = 'pollo_raul_secret_key'

# ==============================
# ✅ PASO 1: SIMULADOR DE MEMORIA
# ==============================
memoria_test = ["CPU", "RAM", "DISCO"]

def simulador_memoria():
    print("\n=== SIMULADOR DE MEMORIA VOLÁTIL ===")

    lista = memoria_test.copy()
    print("1. Inicial:", lista)

    lista.append("MONITOR")
    lista.insert(1, "TECLADO")
    print("2. Expansión:", lista)

    lista.remove("RAM")
    lista.pop(2)
    print("3. Depuración:", lista)

    lista.sort()
    print("4. Ordenado:", lista)

    if "CPU" in lista:
        print("5. CPU SI existe")
    else:
        print("5. CPU NO existe")


# ==============================
# ✅ FUNCIÓN DE ESTANDARIZACIÓN
# ==============================
def estandarizar_dato(texto_entrada, mayusculas=False):
    if not texto_entrada:
        return ""
    limpio = texto_entrada.strip()
    return limpio.upper() if mayusculas else limpio.lower()


# ==============================
# CONFIGURACIÓN
# ==============================
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_NEGOCIO = "123.456.789-0"
DIRECCION = "Cúcuta, Norte de Santander"
TELEFONO = "300 000 0000"
VALOR_IVA = 0.19


# ==============================
# SUPABASE
# ==============================
URL_SUPABASE = "https://paulpnqsfytnpbbitquo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdWxwbnFzZnl0bnBiYml0cXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNzg2NTIsImV4cCI6MjA4OTg1NDY1Mn0.ts4H83Yba2J8id7-evY-Q2ayFHMluBXjfJVyiZFWtig"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)


# ==============================
# HTML (NO SE TOCA - MANTENIDO IGUAL)
# ==============================
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
        h1, h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top:0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
        input, select, button { width: 100%; padding: 10px; margin: 5px 0; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #3498db; color: white; border: none; font-weight: bold; cursor: pointer; }
        .btn-success { background: #2ecc71; }
        .btn-danger { background: #e74c3c; width: auto; padding: 5px 10px; }
        .total-display { font-size: 24px; font-weight: bold; color: #27ae60; text-align: center; padding: 15px; background: #f9fffb; border: 2px dashed #2ecc71; }
        .badge { padding: 2px 6px; border-radius: 4px; font-size: 12px; background: #eee; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card full-width" style="text-align:center;">
            <h1>🍗 {{ nombre }}</h1>
            <p>NIT: {{ nit }} | {{ direccion }}</p>
        </div>

        <div class="card">
            <h2>📦 Inventario / Inventory</h2>
            <form action="/inventario/guardar" method="POST">
                <div style="display:flex; gap:10px;">
                    <input type="number" name="codigo" placeholder="Cód" required>
                    <input type="text" name="producto" placeholder="Producto / Product" required>
                </div>
                <div style="display:flex; gap:10px;">
                    <input type="number" step="0.01" name="precio" placeholder="Precio / Price" required>
                    <input type="number" step="0.01" name="stock" placeholder="Stock" required>
                    <select name="tipo">
                        <option value="Kilo">Kilo</option>
                        <option value="Und">Unidad / Unit</option>
                    </select>
                </div>
                <button type="submit" class="btn-success">Guardar / Save</button>
            </form>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead><tr><th>Cód</th><th>Producto / Product</th><th>Precio</th><th>Stock</th><th>Tipo</th><th>Acción</th></tr></thead>
                    <tbody>
                        {% for p in inventario %}
                        <tr>
                            <td><b>{{ p.codigo }}</b></td>
                            <td>{{ p.producto }}</td>
                            <td>${{ "{:,.0f}".format(p.precio) }}</td>
                            <td>{{ p.stock }}</td>
                            <td><span class="badge">{{ p.tipo }}</span></td>
                            <td><a href="/inventario/eliminar/{{ p.codigo }}"><button class="btn-danger">🗑️</button></a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>🛒 Venta Rápida / Fast Sale</h2>
            <form action="/carrito/agregar" method="POST">
                <div style="display:flex; gap:10px;">
                    <input type="number" name="codigo_vta" placeholder="Código / Code..." required autofocus>
                    <input type="number" step="0.01" name="cantidad" placeholder="Cant." required style="width:100px;">
                    <button type="submit" style="width:120px;">Añadir / Add</button>
                </div>
            </form>
            <hr>
            <h3>👤 Datos Cliente / Client Data</h3>
            <form action="/cliente/actualizar" method="POST">
                <input type="text" name="nombre" placeholder="Nombre / Name" value="{{ cliente.nombre }}">
                <input type="text" name="documento" placeholder="Cédula/NIT" value="{{ cliente.documento }}">
                <button type="submit" style="background:#95a5a6">Actualizar / Update</button>
            </form>
            <div class="total-display">TOTAL: ${{ "{:,.0f}".format(total_venta) }}</div>
            {% if carrito %}
                {% for item in carrito %}
                <p style="font-size:13px; margin:5px 0;">• {{ item.nombre }} ({{ item.cantidad }} {{ item.tipo }}) - ${{ "{:,.0f}".format(item.total) }}</p>
                {% endfor %}
                <a href="/venta/finalizar"><button class="btn-success">FINALIZAR Y FACTURAR / FINISH & BILL</button></a>
                <a href="/carrito/limpiar"><button style="background:#e74c3c; margin-top:5px;">VACIAR / CLEAR</button></a>
            {% endif %}
        </div>

        <div class="card full-width">
            <h2>📊 Historial y Buscador / History & Search</h2>
            <form action="/" method="GET" style="display:flex; gap:10px; margin-bottom:15px;">
                <input type="text" name="buscar" placeholder="Cédula o Nombre / ID or Name..." value="{{ busqueda }}">
                <button type="submit" style="width:120px;">🔍 Buscar / Search</button>
            </form>
            <table>
                <thead><tr><th>No.</th><th>Fecha / Date</th><th>Cliente / Client</th><th>Cédula / ID</th><th>Total</th><th>Opciones / Options</th></tr></thead>
                <tbody>
                    {% for f in historial %}
                    <tr>
                        <td>#{{ f.id }}</td>
                        <td>{{ f.fecha[:16] }}</td>
                        <td>{{ f.cliente_nombre }}</td>
                        <td>{{ f.cliente_documento }}</td>
                        <td><b>${{ "{:,.0f}".format(f.total) }}</b></td>
                        <td><a href="/factura/pdf/{{ f.id }}" target="_blank">🖨️ Imprimir / Print PDF</a></td>
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
# INDEX (MEJORADO)
# ==============================
@app.route("/")
def index():
    if 'carrito' not in session:
        session['carrito'] = []

    if 'cliente' not in session:
        # Reto Avance 7: El cliente ahora es un objeto (diccionario) con más de 3 atributos
        session['cliente'] = {
            "nombre": "Consumidor Final", 
            "documento": "222222222222",
            "puntos": 0,            # Atributo Integer
            "es_frecuente": False    # Atributo Boolean
        }

    buscar = estandarizar_dato(request.args.get('buscar', '')).strip()

    inv_res = supabase.table("inventario").select("*").order("codigo").execute()
    inv = inv_res.data if inv_res.data else []

    if buscar:
        his_res = supabase.table("facturas").select("*")\
            .or_(f"cliente_documento.ilike.%{buscar}%,cliente_nombre.ilike.%{buscar}%")\
            .order("fecha", desc=True).execute()
    else:
        his_res = supabase.table("facturas").select("*").order("fecha", desc=True).limit(10).execute()

    his = his_res.data if his_res.data else []
    total = sum(item['total'] for item in session['carrito'])

    return render_template_string(
        HTML_SISTEMA,
        nombre=NOMBRE_LOCAL,
        nit=NIT_NEGOCIO,
        direccion=DIRECCION,
        inventario=inv,
        carrito=session['carrito'],
        total_venta=total,
        cliente=session['cliente'],
        historial=his,
        busqueda=buscar
    )


# ==============================
# INVENTARIO
# ==============================
@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    try:
        c = request.form

        prod_limpio = estandarizar_dato(c['producto'], mayusculas=True)

        # RETO AVANCE 7: Cada registro ahora es un objeto (diccionario) con atributos múltiples
        datos = {
            "codigo": int(c['codigo']),         # Integer
            "producto": prod_limpio,            # String
            "precio": float(c['precio']),       # Float
            "stock": float(c['stock']),         # Float
            "tipo": c['tipo'],                  # String
            "disponible": float(c['stock']) > 0, # Boolean (Requerimiento técnico)
            "fecha_registro": datetime.now().strftime('%Y-%m-%d')
        }

        # 🔥 USO DE LISTA (EVIDENCIA) - NO SE BORRA
        registro_lista = [datos['codigo'], datos['producto'], datos['stock']]
        print("Registro en lista:", registro_lista)

        supabase.table("inventario").upsert(datos).execute()
        return redirect("/")

    except Exception as e:
        return f"Error: {str(e)}"


# ==============================
# ✅ ACTUALIZACIÓN DE DATOS (NUEVO RETO AVANCE 7)
# ==============================
@app.route("/inventario/actualizar_precio", methods=["POST"])
def actualizar_precio_por_llave():
    """
    Busca por la llave (código) y actualiza el precio.
    Mensajes en Inglés y Español.
    """
    try:
        cod = int(request.form.get("codigo"))
        nuevo_p = float(request.form.get("nuevo_precio"))

        # Actualizamos en Supabase buscando por la llave
        res = supabase.table("inventario").update({"precio": nuevo_p}).eq("codigo", cod).execute()

        if res.data:
            print(f"SUCCESS: Product {cod} updated / Producto {cod} actualizado")
        else:
            print(f"NOT FOUND: Search key {cod} invalid / Llave de búsqueda {cod} no válida")
        
        return redirect("/")
    except Exception as e:
        print(f"ERROR: Update failed / Fallo en actualización: {str(e)}")
        return redirect("/")


@app.route("/inventario/eliminar/<int:codigo>")
def inv_eliminar(codigo):
    supabase.table("inventario").delete().eq("codigo", codigo).execute()
    return redirect("/")


# ==============================
# 🛒 CARRITO (MEJORADO PRO)
# ==============================
@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    cod = request.form.get("codigo_vta")

    try:
        cant = float(request.form.get("cantidad", 0))
        if cant <= 0:
            return redirect("/")
    except:
        return redirect("/")

    res = supabase.table("inventario").select("*").eq("codigo", cod).execute()
    p = res.data[0] if res.data else None

    if not p or float(p['stock']) < cant:
        return redirect("/")

    carrito = session.get('carrito', [])

    # 🔥 EVITAR DUPLICADOS (LISTA + FOR)
    existe = False
    for item in carrito:
        if item['codigo'] == cod:
            item['cantidad'] += cant
            item['total'] = round(item['cantidad'] * float(p['precio']), 2)
            existe = True
            break

    if not existe:
        carrito.append({
            "codigo": cod,
            "nombre": p['producto'],
            "cantidad": cant,
            "total": round(float(p['precio']) * cant, 2),
            "tipo": p['tipo']
        })

    session['carrito'] = carrito
    return redirect("/")


# ==============================
# CLIENTE
# ==============================
@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    # nom_cli = estandarizar_dato(request.form.get("nombre"), mayusculas=True)
    # doc_cli = estandarizar_dato(request.form.get("documento"))
    # (Comentamos lo anterior para implementar la búsqueda real en Supabase)

    nom_cli = estandarizar_dato(request.form.get("nombre"), mayusculas=True)
    doc_cli = estandarizar_dato(request.form.get("documento"))

    # Intentamos buscar el cliente en la base de datos para "colocar los datos"
    res = supabase.table("clientes").select("*").eq("cedula", doc_cli).execute()
    
    if res.data:
        # Si existe, lo cargamos como objeto (diccionario)
        c_db = res.data[0]
        session['cliente'] = {
            "nombre": c_db['nombre'],
            "documento": c_db['cedula'],
            "puntos": c_db.get('puntos', 0),
            "es_frecuente": True
        }
        print("CLIENT DATA RETRIEVED / DATOS DE CLIENTE RECUPERADOS")
    else:
        # Si no existe, creamos el objeto nuevo
        session['cliente'] = {
            "nombre": nom_cli,
            "documento": doc_cli,
            "puntos": 0,
            "es_frecuente": False
        }
        print("NEW CLIENT IN SESSION / NUEVO CLIENTE EN SESIÓN")

    return redirect("/")


# ==============================
# LIMPIAR CARRITO
# ==============================
@app.route("/carrito/limpiar")
def car_limpiar():
    session['carrito'] = []
    return redirect("/")


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    simulador_memoria()  # 🔥 PASO 1 AUTOMÁTICO
    app.run(debug=True)