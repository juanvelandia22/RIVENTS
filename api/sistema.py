# ============================================================
# SISTEMA DE FACTURACIÓN - POLLO Y CHARCUTERÍA RAÚL
# BILLING SYSTEM - POLLO Y CHARCUTERÍA RAÚL
#
# Framework: Flask (Python) | Base de datos / Database: Supabase
# Generación de PDF / PDF Generation: fpdf
# Sesiones / Sessions: Flask Session
# ============================================================

from flask import Flask, render_template_string, request, redirect, session, send_file, url_for, jsonify
from supabase import create_client, Client  # Cliente oficial de Supabase / Official Supabase client
from datetime import datetime               # Para fechas y horas / For dates and times
import os                                  # Variables del sistema / System environment variables
from fpdf import FPDF                      # Generación de PDFs / PDF generation
import io                                  # Flujos de datos en memoria / In-memory data streams

# ------------------------------------------------------------
# INICIALIZACIÓN DE LA APLICACIÓN FLASK
# FLASK APPLICATION INITIALIZATION
#
# secret_key: llave para cifrar cookies de sesión
# secret_key: key used to sign and encrypt session cookies
# ------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'pollo_raul_secret_key'
# ==============================
# ✅ PASO 1 / STEP 1: SIMULADOR DE MEMORIA / MEMORY SIMULATOR
# ==============================
# Lista global que representa componentes iniciales en "memoria"
# Global list representing initial components in "memory"
# Se usa como base para demostrar operaciones sobre listas en Python
# It is used as a basis for demonstrating operations on lists in Python
memoria_test = ["CPU", "RAM", "DISCO"]

def simulador_memoria():
    """
    Función didáctica que simula operaciones básicas sobre listas (memoria volátil).
    Se ejecuta automáticamente al iniciar la aplicación.
    Demuestra: copia, append, insert, remove, pop, sort y búsqueda con 'in'.

    Educational function that simulates basic operations on lists (volatile memory).
    It runs automatically when the application starts.
    It demonstrates: copy, append, insert, remove, pop, sort, and search using 'in'.

    """
    print("\n=== SIMULADOR DE MEMORIA VOLÁTIL ===")

    lista = memoria_test.copy()        # Copia la lista original para no modificarla # Copy the original list so you don't modify it
    print("1. Inicial:", lista)

    lista.append("MONITOR")            # Agrega "MONITOR" al final  # Add "MONITOR" to the end
    lista.insert(1, "TECLADO")         # Inserta "TECLADO" en la posición 1 # Insert "KEYBOARD" in position 1
    print("2. Expansión:", lista)

    lista.remove("RAM")                # Elimina el primer elemento con valor "RAM"  # Remove the first item with the value "RAM"
    lista.pop(2)                       # Elimina el elemento en el índice 2  # Remove the element at index 2
    print("3. Depuración:", lista)

    lista.sort()                       # Ordena la lista alfabéticamente  # Sort the list alphabetically
    print("4. Ordenado:", lista)

    if "CPU" in lista:                 # Verifica si "CPU" existe en la lista  # Check if "CPU" exists in the list
        print("5. CPU SI existe")
    else:
        print("5. CPU NO existe")


# ==============================
# ✅ FUNCIÓN DE ESTANDARIZACIÓN
#      STANDARDIZATION FUNCTION
# ==============================
def estandarizar_dato(texto_entrada, mayusculas=False):
    """
    Limpia y estandariza un texto de entrada.
    - Elimina espacios al inicio y al final (strip).
    - Si mayusculas=True, convierte el texto a MAYÚSCULAS.
    - Si mayusculas=False (por defecto), convierte a minúsculas.
    - Retorna cadena vacía si el texto está vacío o es None.
    
    Parámetros:
        texto_entrada (str): Texto a limpiar.
        mayusculas (bool): Define si el resultado va en mayúsculas o minúsculas.
    
    Retorna:
        str: Texto limpio y estandarizado.
    """
    if not texto_entrada:
        return ""
    limpio = texto_entrada.strip()
    return limpio.upper() if mayusculas else limpio.lower()

# ==============================
# CONFIGURACIÓN
# ==============================
# Constantes globales del negocio, usadas en toda la aplicación
# para mostrar encabezados en la interfaz y en los PDFs de factura
# ==============================
# CONFIGURATION
# ==============================
# Global business constants, used throughout the application
# to display headers in the interface and invoice PDFs

NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_NEGOCIO = "123.456.789-0"
DIRECCION = "Cúcuta, Norte de Santander"
TELEFONO = "300 000 0000"
VALOR_IVA = 0.19   # IVA del 19% aplicado en cálculos de facturación  # 19% VAT applied to billing calculations

# ==============================
# SUPABASE
# ==============================
# Connection credentials to the project in Supabase (cloud database)
# URL_SUPABASE: Project endpoint
# KEY_SUPABASE: Anonymous public key for authentication
# ==============================
# SUPABASE
# ==============================
# Credenciales de conexión al proyecto en Supabase (base de datos en la nube)
# URL_SUPABASE: Endpoint del proyecto
# KEY_SUPABASE: Llave pública anónima (anon key) para autenticación
URL_SUPABASE = "https://paulpnqsfytnpbbitquo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdWxwbnFzZnl0bnBiYml0cXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNzg2NTIsImV4cCI6MjA4OTg1NDY1Mn0.ts4H83Yba2J8id7-evY-Q2ayFHMluBXjfJVyiZFWtig"

# Se crea la instancia del cliente Supabase para usar en todas las rutas   # The Supabase client instance is created for use on all routes
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# ===============================
# HTML
# ==============================
# Complete HTML template rendered with Jinja2 from Flask.

# Contains the entire system interface:
# - Business header
# - Inventory form and table
# - Quick Sale module with shopping cart and customer data
# - Invoice history with search function
# Dynamic values ​​are injected using Jinja2's {{ variable }}
# ==============================
# HTML 
# ==============================
# Plantilla HTML completa renderizada con Jinja2 desde Flask.
# Contiene toda la interfaz del sistema:
#   - Encabezado del negocio
#   - Formulario y tabla de Inventario
#   - Módulo de Venta Rápida con carrito y datos del cliente
#   - Historial de facturas con buscador
# Los valores dinámicos se inyectan con {{ variable }} de Jinja2

HTML_SISTEMA ="""
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
# INDEX 
# ==============================
@app.route("/")
def index():
    """
    Ruta principal del sistema. Carga y renderiza la interfaz completa.
    Main route of the system. Loads and renders the full interface.

    Comportamiento / Behavior:
    - Inicializa el carrito en sesión si no existe.
    -  Initializes the shopping cart in session if it doesn't exist.
    - Inicializa el objeto cliente con valores por defecto si no existe.
    -  Initializes the client object with default values if it doesn't exist.
    -  Atributos / Attributes: nombre (str), documento (str), puntos (int), es_frecuente (bool).
    - Estandariza el parámetro de búsqueda de la URL.
    -  Standardizes the search parameter from the URL.
    - Consulta el inventario completo ordenado por código.
    -  Queries the full inventory ordered by product code.
    - Si hay búsqueda activa, filtra facturas; si no, carga las últimas 10.
    -  If search is active, filters invoices; otherwise loads the last 10.
    - Calcula el total del carrito.
    -  Calculates the cart total.
    - Renderiza la plantilla HTML con todos los datos.
    -  Renders the HTML template with all required data.
    """
    if 'carrito' not in session:
        session['carrito'] = []

    if 'cliente' not in session:
        # Reto Avance 7: El cliente es un objeto diccionario con más de 3 atributos
        # Advance Challenge 7: Client is a dictionary object with more than 3 attributes
        session['cliente'] = {
            "nombre": "Consumidor Final",
            "documento": "222222222222",
            "puntos": 0,             # Atributo entero / Integer attribute
            "es_frecuente": False     # Atributo booleano / Boolean attribute
        }

    # Limpia y estandariza el parámetro de búsqueda de la URL (?buscar=...)
    # Cleans and standardizes the search parameter from the URL (?buscar=...)
    buscar = estandarizar_dato(request.args.get('buscar', '')).strip()

    # Consulta todos los productos ordenados por código ascendente
    # Queries all products ordered by code in ascending order
    inv_res = supabase.table("inventario").select("*").order("codigo").execute()
    inv = inv_res.data if inv_res.data else []

    if buscar:
        # Filtra por documento o nombre (búsqueda parcial, insensible a mayúsculas)
        # Filters by document or name (partial search, case-insensitive)
        his_res = supabase.table("facturas").select("*")\
            .or_(f"cliente_documento.ilike.%{buscar}%,cliente_nombre.ilike.%{buscar}%")\
            .order("fecha", desc=True).execute()
    else:
        # Sin búsqueda: trae las últimas 10 facturas
        # No search: fetches the last 10 invoices
        his_res = supabase.table("facturas").select("*").order("fecha", desc=True).limit(10).execute()

    his = his_res.data if his_res.data else []

    # Suma el campo 'total' de cada ítem del carrito
    # Sums the 'total' field from each item in the cart
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
# INVENTARIO / INVENTORY
# ==============================
@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    """
    Recibe los datos del formulario de inventario y los guarda en Supabase.
    Receives inventory form data and saves it to Supabase.

    Proceso / Process:
    - Extrae los campos del formulario / Extracts form fields.
    - Estandariza el nombre del producto a MAYÚSCULAS / Standardizes product name to UPPERCASE.
    - Construye un diccionario con todos los atributos del producto.
    -  Builds a dictionary with all product attributes.
    - 'disponible' es un booleano derivado del stock / 'disponible' is a boolean derived from stock.
    - Imprime el registro como lista (evidencia de uso de listas).
    -  Prints the record as a list (evidence of list usage).
    - Usa upsert: inserta o actualiza si el código ya existe.
    -  Uses upsert: inserts or updates if the code already exists.
    - En caso de error, retorna el mensaje de excepción.
    -  On error, returns the exception message.
    """
    try:
        c = request.form

        # Limpia y convierte el nombre del producto a MAYÚSCULAS
        # Cleans and converts the product name to UPPERCASE
        prod_limpio = estandarizar_dato(c['producto'], mayusculas=True)

        # RETO AVANCE 7 / ADVANCE CHALLENGE 7:
        # Cada registro es un objeto (diccionario) con atributos múltiples
        # Each record is an object (dictionary) with multiple attributes
        datos = {
            "codigo": int(c['codigo']),          # Entero / Integer
            "producto": prod_limpio,             # Cadena estandarizada / Standardized string
            "precio": float(c['precio']),        # Decimal / Float
            "stock": float(c['stock']),          # Decimal / Float
            "tipo": c['tipo'],                   # Kilo / Unidad (Unit)
            "disponible": float(c['stock']) > 0, # Booleano: True si stock > 0 / Boolean: True if stock > 0
            "fecha_registro": datetime.now().strftime('%Y-%m-%d')  # Fecha actual / Current date
        }

        # 🔥 USO DE LISTA (EVIDENCIA / LIST USAGE EVIDENCE) - NO SE BORRA / DO NOT REMOVE
        # Lista con datos principales para trazabilidad en consola
        # List with main data for console traceability
        registro_lista = [datos['codigo'], datos['producto'], datos['stock']]
        print("Registro en lista / Record as list:", registro_lista)

        # Inserta o actualiza el producto en Supabase
        # Inserts or updates the product in Supabase
        supabase.table("inventario").upsert(datos).execute()
        return redirect("/")

    except Exception as e:
        return f"Error / Error: {str(e)}"


# ==============================
# ✅ ACTUALIZACIÓN DE DATOS / DATA UPDATE (NUEVO RETO AVANCE 7 / NEW ADVANCE CHALLENGE 7)
# ==============================
@app.route("/inventario/actualizar_precio", methods=["POST"])
def actualizar_precio_por_llave():
    """
    Actualiza el precio de un producto buscándolo por su código (llave primaria).
    Updates the price of a product by searching with its code (primary key).

    Mensajes en Inglés y Español / Messages in English and Spanish.

    Proceso / Process:
    - Recibe el código y el nuevo precio del formulario.
    -  Receives the product code and new price from the form.
    - Ejecuta UPDATE en Supabase filtrando por código (eq).
    -  Executes UPDATE in Supabase filtering by code (eq).
    - Si encuentra el registro, imprime mensaje de éxito.
    -  If record is found, prints success message.
    - Si no lo encuentra, imprime mensaje de advertencia.
    -  If not found, prints warning message.
    - En cualquier caso redirige al index.
    -  In any case, redirects to index.
    """
    try:
        cod = int(request.form.get("codigo"))
        nuevo_p = float(request.form.get("nuevo_precio"))

        # Actualiza el precio del producto que coincida con el código
        # Updates the price of the product matching the given code
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
    """
    Elimina un producto del inventario por su código.
    Deletes a product from the inventory by its code.

    Parámetro de URL / URL Parameter:
        codigo (int): Código único del producto / Unique product code.

    Proceso / Process:
    - Ejecuta DELETE en Supabase filtrando por el código.
    -  Executes DELETE in Supabase filtering by the given code.
    - Redirige al index al finalizar / Redirects to index when done.
    """
    supabase.table("inventario").delete().eq("codigo", codigo).execute()
    return redirect("/")


# ==============================
# 🛒 CARRITO / CART (MEJORADO PRO / PRO IMPROVED)
# ==============================
@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    """
    Agrega un producto al carrito de compras de la sesión.
    Adds a product to the session shopping cart.

    Proceso / Process:
    - Recibe código y cantidad del formulario / Receives code and quantity from form.
    - Valida que la cantidad sea un número positivo válido.
    -  Validates that the quantity is a valid positive number.
    - Consulta el producto en Supabase por código.
    -  Queries the product in Supabase by code.
    - Verifica existencia y stock suficiente.
    -  Verifies product existence and sufficient stock.
    - Si el producto ya está en el carrito: suma cantidad y recalcula total.
    -  If product already in cart: adds quantity and recalculates total.
    - Si no está: lo agrega como nuevo ítem al carrito.
    -  If not in cart: appends it as a new item.
    - Guarda el carrito en sesión y redirige al index.
    -  Saves the cart in session and redirects to index.
    """
    cod = request.form.get("codigo_vta")

    try:
        cant = float(request.form.get("cantidad", 0))
        if cant <= 0:          # Rechaza cantidades inválidas / Rejects invalid quantities
            return redirect("/")
    except:
        return redirect("/")   # Rechaza valores no numéricos / Rejects non-numeric values

    # Busca el producto en el inventario por código
    # Queries the product from inventory by code
    res = supabase.table("inventario").select("*").eq("codigo", cod).execute()
    p = res.data[0] if res.data else None

    # Valida existencia del producto y disponibilidad de stock
    # Validates product existence and stock availability
    if not p or float(p['stock']) < cant:
        return redirect("/")

    carrito = session.get('carrito', [])

    # 🔥 EVITAR DUPLICADOS (LISTA + FOR / LIST + FOR LOOP)
    # Recorre el carrito; si el producto existe, actualiza cantidad y total
    # Iterates the cart; if product exists, updates quantity and total
    existe = False
    for item in carrito:
        if item['codigo'] == cod:
            item['cantidad'] += cant
            item['total'] = round(item['cantidad'] * float(p['precio']), 2)
            existe = True
            break  # Sale del ciclo al encontrar el producto / Exits loop when product is found

    # Si no estaba en el carrito, lo agrega como nuevo ítem
    # If not already in cart, appends it as a new item
    if not existe:
        carrito.append({
            "codigo": cod,
            "nombre": p['producto'],
            "cantidad": cant,
            "total": round(float(p['precio']) * cant, 2),
            "tipo": p['tipo']
        })

    # Guarda el carrito actualizado en la sesión
    # Saves the updated cart to the session
    session['carrito'] = carrito
    return redirect("/")


# ==============================
# CLIENTE / CLIENT
# ==============================
@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    """
    Actualiza los datos del cliente activo en la sesión.
    Updates the active client's data in the session.

    Proceso / Process:
    - Estandariza nombre (MAYÚSCULAS) y documento (minúsculas) del formulario.
    -  Standardizes name (UPPERCASE) and document (lowercase) from form.
    - Busca el cliente en Supabase por cédula.
    -  Searches the client in Supabase by ID number.
    - Si existe: carga datos reales y marca es_frecuente=True.
    -  If found: loads real data and sets es_frecuente=True.
    - Si no existe: crea objeto nuevo con datos del formulario.
    -  If not found: creates new object with form data.
    - Guarda el cliente en sesión y redirige al index.
    - Saves client to session and redirects to index.

    Nota / Note:
    Las líneas comentadas muestran la implementación anterior simple.
    Commented lines show the previous simple implementation.
    """
    # nom_cli = estandarizar_dato(request.form.get("nombre"), mayusculas=True)
    # doc_cli = estandarizar_dato(request.form.get("documento"))
    # (Comentamos lo anterior para implementar la búsqueda real en Supabase)
    # (Commented out to implement real Supabase lookup)

    nom_cli = estandarizar_dato(request.form.get("nombre"), mayusculas=True)
    doc_cli = estandarizar_dato(request.form.get("documento"))

    # Busca el cliente en Supabase por cédula (llave de búsqueda)
    # Searches for the client in Supabase by ID number (search key)
    res = supabase.table("clientes").select("*").eq("cedula", doc_cli).execute()

    if res.data:
        # Cliente encontrado: carga sus datos desde la base de datos
        # Client found: loads their data from the database
        c_db = res.data[0]
        session['cliente'] = {
            "nombre": c_db['nombre'],
            "documento": c_db['cedula'],
            "puntos": c_db.get('puntos', 0),  # Usa 0 si el campo no existe / Defaults to 0 if field missing
            "es_frecuente": True               # Cliente frecuente confirmado / Confirmed frequent client
        }
        print("CLIENT DATA RETRIEVED / DATOS DE CLIENTE RECUPERADOS")
    else:
        # Cliente no encontrado: crea objeto nuevo con datos del formulario
        # Client not found: creates new object with form data
        session['cliente'] = {
            "nombre": nom_cli,
            "documento": doc_cli,
            "puntos": 0,
            "es_frecuente": False
        }
        print("NEW CLIENT IN SESSION / NUEVO CLIENTE EN SESIÓN")

    return redirect("/")


# ==============================
# LIMPIAR CARRITO / CLEAR CART
# ==============================
@app.route("/carrito/limpiar")
def car_limpiar():
    """
    Vacía completamente el carrito de compras de la sesión.
    Completely clears the shopping cart from the session.

    Proceso / Process:
    - Asigna una lista vacía al carrito en sesión.
    -  Assigns an empty list to the cart in session.
    - Redirige al index para refrescar la vista.
    - Redirects to index to refresh the view.
    """
    session['carrito'] = []
    return redirect("/")


# ==============================
# RUN / EJECUCIÓN
# ==============================
if __name__ == "__main__":
    simulador_memoria()  # 🔥 PASO 1 AUTOMÁTICO / AUTOMATIC STEP 1: ejecuta el simulador / runs the simulator
    app.run(debug=True)  # Inicia servidor Flask en modo debug / Starts Flask server in debug mode