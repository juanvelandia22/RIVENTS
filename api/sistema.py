# ============================================================
# SISTEMA DE FACTURACIÓN - POLLO Y CHARCUTERÍA RAÚL
# Framework: Flask (Python) | Base de datos: Supabase
# Generación de PDF: fpdf | Sesiones: Flask Session
# ============================================================

from flask import Flask, render_template_string, request, redirect, session, send_file, url_for, jsonify
from supabase import create_client, Client  # Cliente oficial de Supabase para Python
from datetime import datetime               # Para registrar fechas y horas
import os                                  # Para variables de entorno del sistema operativo
from fpdf import FPDF                      # Para generar archivos PDF
import io                                  # Para manejar flujos de datos en memoria (sin guardar archivos físicos)

# ------------------------------------------------------------
# INICIALIZACIÓN DE LA APLICACIÓN FLASK
# secret_key: llave para firmar y cifrar las cookies de sesión
# ------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'pollo_raul_secret_key'


# ==============================
# ✅ PASO 1: SIMULADOR DE MEMORIA
# ==============================
# Lista global que representa los componentes iniciales en "memoria"
# Se usa como base para demostrar operaciones sobre listas en Python
memoria_test = ["CPU", "RAM", "DISCO"]

def simulador_memoria():
    """
    Función didáctica que simula operaciones básicas sobre listas (memoria volátil).
    Se ejecuta automáticamente al iniciar la aplicación.
    Demuestra: copia, append, insert, remove, pop, sort y búsqueda con 'in'.
    """
    print("\n=== SIMULADOR DE MEMORIA VOLÁTIL ===")

    lista = memoria_test.copy()        # Copia la lista original para no modificarla
    print("1. Inicial:", lista)

    lista.append("MONITOR")            # Agrega "MONITOR" al final
    lista.insert(1, "TECLADO")         # Inserta "TECLADO" en la posición 1
    print("2. Expansión:", lista)

    lista.remove("RAM")                # Elimina el primer elemento con valor "RAM"
    lista.pop(2)                       # Elimina el elemento en el índice 2
    print("3. Depuración:", lista)

    lista.sort()                       # Ordena la lista alfabéticamente
    print("4. Ordenado:", lista)

    if "CPU" in lista:                 # Verifica si "CPU" existe en la lista
        print("5. CPU SI existe")
    else:
        print("5. CPU NO existe")


# ==============================
# ✅ FUNCIÓN DE ESTANDARIZACIÓN
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
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_NEGOCIO = "123.456.789-0"
DIRECCION = "Cúcuta, Norte de Santander"
TELEFONO = "300 000 0000"
VALOR_IVA = 0.19   # IVA del 19% aplicado en cálculos de facturación


# ==============================
# SUPABASE
# ==============================
# Credenciales de conexión al proyecto en Supabase (base de datos en la nube)
# URL_SUPABASE: Endpoint del proyecto
# KEY_SUPABASE: Llave pública anónima (anon key) para autenticación
URL_SUPABASE = "https://paulpnqsfytnpbbitquo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdWxwbnFzZnl0bnBiYml0cXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNzg2NTIsImV4cCI6MjA4OTg1NDY1Mn0.ts4H83Yba2J8id7-evY-Q2ayFHMluBXjfJVyiZFWtig"

# Se crea la instancia del cliente Supabase para usar en todas las rutas
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)


# ==============================
# HTML (NO SE TOCA - MANTENIDO IGUAL)
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
# INDEX (MEJORADO)
# ==============================
@app.route("/")
def index():
    """
    Ruta principal del sistema. Carga y renderiza la interfaz completa.

    Comportamiento:
    - Inicializa el carrito de compras en sesión si no existe.
    - Inicializa el objeto cliente en sesión con valores por defecto si no existe.
    - El cliente tiene 4 atributos: nombre (str), documento (str),
    - puntos (int) y es_frecuente (bool).
    - Permite buscar facturas por cédula o nombre del cliente.
    - Consulta el inventario completo ordenado por código.
    - Si hay búsqueda activa, filtra las facturas; si no, carga las últimas 10.
    - Calcula el total del carrito sumando los totales de cada ítem.
    - Renderiza la plantilla HTML con todos los datos necesarios.
    """
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

    # Limpia y estandariza el parámetro de búsqueda de la URL (?buscar=...)
    buscar = estandarizar_dato(request.args.get('buscar', '')).strip()

    # Consulta todos los productos del inventario ordenados por código ascendente
    inv_res = supabase.table("inventario").select("*").order("codigo").execute()
    inv = inv_res.data if inv_res.data else []

    # Consulta el historial de facturas con o sin filtro de búsqueda
    if buscar:
        # Filtra por documento o nombre del cliente (búsqueda parcial, insensible a mayúsculas)
        his_res = supabase.table("facturas").select("*")\
            .or_(f"cliente_documento.ilike.%{buscar}%,cliente_nombre.ilike.%{buscar}%")\
            .order("fecha", desc=True).execute()
    else:
        # Sin búsqueda, trae las últimas 10 facturas ordenadas por fecha descendente
        his_res = supabase.table("facturas").select("*").order("fecha", desc=True).limit(10).execute()

    his = his_res.data if his_res.data else []

    # Calcula el total del carrito sumando el campo 'total' de cada ítem
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
    """
    Recibe los datos del formulario de inventario y los guarda en Supabase.

    Proceso:
    - Extrae los campos del formulario (codigo, producto, precio, stock, tipo).
    - Estandariza el nombre del producto a MAYÚSCULAS.
    - Construye un diccionario con todos los atributos del producto,
    -  incluyendo 'disponible' (booleano) y 'fecha_registro' (fecha actual).
    - Imprime el registro como lista (evidencia de uso de listas).
    - Usa upsert para insertar o actualizar si el código ya existe.
    - Redirige al index al finalizar.
    - En caso de error, retorna el mensaje de excepción.
    """
    try:
        c = request.form

        # Limpia y convierte el nombre del producto a mayúsculas
        prod_limpio = estandarizar_dato(c['producto'], mayusculas=True)

        # RETO AVANCE 7: Cada registro ahora es un objeto (diccionario) con atributos múltiples
        datos = {
            "codigo": int(c['codigo']),          # Integer
            "producto": prod_limpio,             # String (estandarizado)
            "precio": float(c['precio']),        # Float
            "stock": float(c['stock']),          # Float
            "tipo": c['tipo'],                   # String (Kilo / Unidad)
            "disponible": float(c['stock']) > 0, # Boolean: True si stock > 0
            "fecha_registro": datetime.now().strftime('%Y-%m-%d')  # Fecha actual formateada
        }

        # 🔥 USO DE LISTA (EVIDENCIA) - NO SE BORRA
        # Crea una lista con los datos principales para trazabilidad en consola
        registro_lista = [datos['codigo'], datos['producto'], datos['stock']]
        print("Registro en lista:", registro_lista)

        # Inserta o actualiza el producto en la tabla "inventario" de Supabase
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
    Actualiza el precio de un producto buscándolo por su código (llave primaria).
    Mensajes de confirmación en Inglés y Español.

    Proceso:
    - Recibe el código del producto y el nuevo precio del formulario.
    - Ejecuta un UPDATE en Supabase filtrando por el código (eq).
    - Si encuentra y actualiza el registro, imprime mensaje de éxito.
    - Si no encuentra el código, imprime mensaje de advertencia.
    - En cualquier caso (éxito o error), redirige al index.
    """
    try:
        cod = int(request.form.get("codigo"))
        nuevo_p = float(request.form.get("nuevo_precio"))

        # Actualiza el campo 'precio' del producto que coincida con el código
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

    Parámetro de URL:
        codigo (int): Código único del producto a eliminar.

    Proceso:
    - Ejecuta un DELETE en Supabase filtrando por el código recibido en la URL.
    - Redirige al index al finalizar.
    """
    supabase.table("inventario").delete().eq("codigo", codigo).execute()
    return redirect("/")


# ==============================
# 🛒 CARRITO (MEJORADO PRO)
# ==============================
@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    """
    Agrega un producto al carrito de compras de la sesión actual.

    Proceso:
    - Recibe el código del producto y la cantidad del formulario.
    - Valida que la cantidad sea un número positivo válido.
    - Consulta el producto en Supabase por su código.
    - Verifica que el producto exista y que haya stock suficiente.
    - Si el producto ya está en el carrito, suma la cantidad y recalcula el total.
    - Si no está, lo agrega como nuevo ítem con todos sus datos.
    - Guarda el carrito actualizado en la sesión y redirige al index.
    """
    cod = request.form.get("codigo_vta")

    try:
        cant = float(request.form.get("cantidad", 0))
        if cant <= 0:          # Rechaza cantidades cero o negativas
            return redirect("/")
    except:
        return redirect("/")   # Rechaza valores no numéricos

    # Busca el producto en el inventario por código
    res = supabase.table("inventario").select("*").eq("codigo", cod).execute()
    p = res.data[0] if res.data else None

    # Valida existencia del producto y disponibilidad de stock
    if not p or float(p['stock']) < cant:
        return redirect("/")

    carrito = session.get('carrito', [])

    # 🔥 EVITAR DUPLICADOS (LISTA + FOR)
    # Recorre el carrito; si el producto ya existe, actualiza cantidad y total
    existe = False
    for item in carrito:
        if item['codigo'] == cod:
            item['cantidad'] += cant
            item['total'] = round(item['cantidad'] * float(p['precio']), 2)
            existe = True
            break  # Sale del ciclo al encontrar el producto

    # Si el producto no estaba en el carrito, lo agrega como nuevo ítem
    if not existe:
        carrito.append({
            "codigo": cod,
            "nombre": p['producto'],
            "cantidad": cant,
            "total": round(float(p['precio']) * cant, 2),
            "tipo": p['tipo']
        })

    # Guarda el carrito modificado en la sesión
    session['carrito'] = carrito
    return redirect("/")


# ==============================
# CLIENTE
# ==============================
@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    """
    Actualiza los datos del cliente activo en la sesión.

    Proceso:
    - Estandariza el nombre (MAYÚSCULAS) y documento (minúsculas) recibidos del formulario.
    - Busca el cliente en la tabla "clientes" de Supabase por su cédula.
    - Si el cliente existe en la BD: carga sus datos reales y marca es_frecuente=True.
    - Si no existe: crea un objeto nuevo con los datos del formulario y es_frecuente=False.
    - En ambos casos, guarda el objeto cliente en la sesión y redirige al index.

    Nota: Las líneas comentadas muestran la implementación anterior simple,
    reemplazada por la búsqueda real en Supabase.
    """
    # nom_cli = estandarizar_dato(request.form.get("nombre"), mayusculas=True)
    # doc_cli = estandarizar_dato(request.form.get("documento"))
    # (Comentamos lo anterior para implementar la búsqueda real en Supabase)

    nom_cli = estandarizar_dato(request.form.get("nombre"), mayusculas=True)
    doc_cli = estandarizar_dato(request.form.get("documento"))

    # Busca el cliente en Supabase usando la cédula como llave de búsqueda
    res = supabase.table("clientes").select("*").eq("cedula", doc_cli).execute()
    
    if res.data:
        # Cliente encontrado: carga sus datos desde la base de datos
        c_db = res.data[0]
        session['cliente'] = {
            "nombre": c_db['nombre'],
            "documento": c_db['cedula'],
            "puntos": c_db.get('puntos', 0),  # Usa 0 si el campo no existe
            "es_frecuente": True               # Marcado como cliente frecuente
        }
        print("CLIENT DATA RETRIEVED / DATOS DE CLIENTE RECUPERADOS")
    else:
        # Cliente no encontrado: crea objeto nuevo con datos del formulario
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
    """
    Vacía completamente el carrito de compras de la sesión actual.

    Proceso:
    - Asigna una lista vacía al carrito en la sesión.
    - Redirige al index para refrescar la vista.
    """
    session['carrito'] = []
    return redirect("/")


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    simulador_memoria()  # 🔥 PASO 1 AUTOMÁTICO: ejecuta el simulador al arrancar
    app.run(debug=True)  # Inicia el servidor Flask en modo debug (recarga automática en cambios)