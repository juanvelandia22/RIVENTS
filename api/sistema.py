# ============================================================
# SISTEMA DE FACTURACIÓN - POLLO Y CHARCUTERÍA RAÚL
# BILLING SYSTEM - POLLO Y CHARCUTERÍA RAÚL
#
# Framework: Flask (Python) | Base de datos / Database: Supabase
# Generación de PDF / PDF Generation: fpdf
# Sesiones / Sessions: Flask Session
# AVANCE 11: Pila, Cola, Diccionario de Colas
# FIX VERCEL: Estructuras dinámicas guardadas en sesión (no globales)
# ============================================================
import csv
import unicodedata
from flask import Flask, render_template_string, request, redirect, session, send_file, url_for, jsonify
from supabase import create_client, Client
from datetime import datetime
import os
from fpdf import FPDF
import io

# ============================================================
# TAD: ABSTRACT DATA TYPE / TIPO DE DATO ABSTRACTO
# ============================================================
class Producto:
    def __init__(self, codigo, nombre, precio, categoria):
        self.codigo = int(codigo)
        self.nombre = nombre.upper()
        self.precio = float(precio)
        self.categoria = categoria

    def to_dict(self):
        return {
            "codigo": self.codigo,
            "producto": self.nombre,
            "precio": self.precio,
            "categoria": self.categoria
        }

# ============================================================
# AVANCE 10 - LINKED LIST / LISTA ENLAZADA
# (Solo en memoria local, no en Vercel serverless)
# ============================================================
class Node:
    def __init__(self, product):
        self.product = product
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def add_node(self, product):
        new_node = Node(product)
        if self.head is None:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node

    def delete_node(self, codigo):
        current = self.head
        previous = None
        while current:
            if current.product.codigo == codigo:
                if previous is None:
                    self.head = current.next
                else:
                    previous.next = current.next
                return True
            previous = current
            current = current.next
        return False

    def find_node(self, codigo):
        current = self.head
        while current:
            if current.product.codigo == codigo:
                return current.product
            current = current.next
        return None

    def generate_report(self):
        current = self.head
        while current:
            p = current.product
            print(f"{p.codigo} | {p.nombre} | ${p.precio}")
            current = current.next

inventario_lista = LinkedList()

# ============================================================
# AVANCE 11 - HELPERS DE SESIÓN PARA PILA, COLA Y DICT-COLAS
#
# FIX VERCEL: En entornos serverless no existen variables globales
# persistentes entre requests. Guardamos las estructuras como
# listas/dicts serializables dentro de session (cookie cifrada).
#
# AVANCE 11 - SESSION HELPERS FOR STACK, QUEUE AND DICT-QUEUES
#
# VERCEL FIX: In serverless environments there are no persistent
# globals between requests. We store the structures as serializable
# lists/dicts inside session (signed cookie).
# ============================================================

# ── PILA (STACK / LIFO) ──────────────────────────────────────
def pila_push(accion: dict):
    """Apila una acción en la sesión. / Pushes an action to the session stack."""
    if 'pila' not in session:
        session['pila'] = []
    pila = session['pila']
    pila.append(accion)
    session['pila'] = pila
    print(f"[PILA PUSH] {accion.get('tipo')}")

def pila_pop() -> dict | None:
    """Desapila la última acción. / Pops the last action."""
    pila = session.get('pila', [])
    if not pila:
        print("[PILA POP] Vacía / Empty")
        return None
    accion = pila.pop()
    session['pila'] = pila
    print(f"[PILA POP] Deshaciendo / Undoing: {accion.get('tipo')}")
    return accion

def pila_peek() -> dict | None:
    """Consulta la cima sin eliminar. / Peeks at the top."""
    pila = session.get('pila', [])
    return pila[-1] if pila else None

def pila_lista() -> list:
    """Retorna la pila con la cima al inicio. / Returns stack with top first."""
    return list(reversed(session.get('pila', [])))

# ── COLA (QUEUE / FIFO) ──────────────────────────────────────
def cola_encolar(pedido: dict):
    """Agrega al final de la cola. / Enqueues to the end."""
    if 'cola' not in session:
        session['cola'] = []
        session['cola_contador'] = 0
    cola = session['cola']
    contador = session.get('cola_contador', 0) + 1
    pedido['turno'] = contador
    pedido['hora_ingreso'] = datetime.now().strftime("%H:%M:%S")
    cola.append(pedido)
    session['cola'] = cola
    session['cola_contador'] = contador
    print(f"[COLA ENCOLAR] Turno #{contador} — {pedido.get('cliente')}")

def cola_desencolar() -> dict | None:
    """Atiende el primero (FIFO). / Dequeues the first (FIFO)."""
    cola = session.get('cola', [])
    if not cola:
        print("[COLA] Vacía / Empty")
        return None
    pedido = cola.pop(0)
    session['cola'] = cola
    print(f"[COLA DESENCOLAR] Atendido turno #{pedido.get('turno')}")
    return pedido

def cola_lista() -> list:
    return session.get('cola', [])

# ── DICCIONARIO DE COLAS ─────────────────────────────────────
def dict_colas_encolar(categoria: str, producto: dict):
    """Agrega un producto a la cola de su categoría. / Adds product to its category queue."""
    if 'dict_colas' not in session:
        session['dict_colas'] = {}
    dc = session['dict_colas']
    cat = categoria.upper()
    if cat not in dc:
        dc[cat] = []
    dc[cat].append(producto)
    session['dict_colas'] = dc
    print(f"[DICT-COLAS] '{producto.get('producto')}' → categoría '{cat}'")

def dict_colas_cargar(lista_productos: list):
    """Carga masiva desde inventario. / Bulk loads from inventory."""
    dc = {}
    for p in lista_productos:
        cat = str(p.get('categoria', 'GENERAL')).upper()
        if cat not in dc:
            dc[cat] = []
        dc[cat].append(p)
    session['dict_colas'] = dc
    print(f"[DICT-COLAS] Cargados {len(lista_productos)} productos en {len(dc)} categorías")

def dict_colas_datos() -> dict:
    return session.get('dict_colas', {})

# ============================================================
# PERSISTENCIA CSV / CSV PERSISTENCE
# ============================================================
ARCHIVO_PERSISTENCIA = "datos_rivents.csv"

def cargar_datos_csv():
    datos = []
    try:
        with open(ARCHIVO_PERSISTENCIA, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                datos.append(dict(row))
        print(f"Datos cargados desde {ARCHIVO_PERSISTENCIA}")
    except FileNotFoundError:
        print("No se encontró archivo de persistencia.")
    return datos

def guardar_datos_csv(lista_datos):
    if not lista_datos:
        return
    with open(ARCHIVO_PERSISTENCIA, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=lista_datos[0].keys())
        writer.writeheader()
        writer.writerows(lista_datos)

def obtener_nombre_categoria(id_buscado):
    try:
        with open("api/categorias.csv", mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for fila in reader:
                if fila['id'] == str(id_buscado):
                    return fila['nombre_cat']
        return "General"
    except FileNotFoundError:
        return "Sin Categoría"

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
app.secret_key = 'pollo_raul_secret_key'

# ============================================================
# CONSTANTES / CONSTANTS
# ============================================================
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_NEGOCIO  = "123.456.789-0"
DIRECCION    = "Cucuta, Norte de Santander"
TELEFONO     = "300 000 0000"
VALOR_IVA    = 0.19

# ============================================================
# SUPABASE
# ============================================================
URL_SUPABASE = "https://paulpnqsfytnpbbitquo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdWxwbnFzZnl0bnBiYml0cXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNzg2NTIsImV4cCI6MjA4OTg1NDY1Mn0.ts4H83Yba2J8id7-evY-Q2ayFHMluBXjfJVyiZFWtig"
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# ============================================================
# SIMULADOR DE MEMORIA / MEMORY SIMULATOR
# ============================================================
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
    print("5. CPU SI existe" if "CPU" in lista else "5. CPU NO existe")

def estandarizar_dato(texto_entrada, mayusculas=False):
    if not texto_entrada:
        return ""
    limpio = texto_entrada.strip()
    return limpio.upper() if mayusculas else limpio.lower()

# ============================================================
# FIX PDF: NORMALIZAR TEXTO PARA FPDF (LATIN-1)
# ============================================================
def limpiar_texto_pdf(texto):
    """
    ESP: Convierte caracteres Unicode (tildes, ñ, guiones especiales, etc.)
         a su equivalente latin-1 para que fpdf no falle.
    ENG: Converts Unicode characters (accents, ñ, special dashes, etc.)
         to their latin-1 equivalent so fpdf doesn't crash.
    """
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', str(texto))
    return texto.encode('latin-1', errors='ignore').decode('latin-1')

# ============================================================
# HTML TEMPLATE
# ============================================================
HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ nombre }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 1400px; margin: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
        .full-width { grid-column: 1 / -1; }
        h1, h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top: 0; }
        h3 { color: #34495e; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
        th { background: #f8f9fa; font-weight: 600; }
        input, select, button { width: 100%; padding: 10px; margin: 5px 0; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #3498db; color: white; border: none; font-weight: bold; cursor: pointer; transition: opacity .2s; }
        button:hover { opacity: .85; }
        .btn-success { background: #2ecc71; }
        .btn-danger  { background: #e74c3c; width: auto; padding: 5px 10px; }
        .btn-warning { background: #f39c12; }
        .btn-purple  { background: #8e44ad; }
        .total-display { font-size: 24px; font-weight: bold; color: #27ae60; text-align: center; padding: 15px; background: #f9fffb; border: 2px dashed #2ecc71; border-radius: 8px; margin: 10px 0; }
        .badge { padding: 3px 8px; border-radius: 12px; font-size: 12px; background: #eee; }

        /* AVANCE 11 */
        .avance11-panel { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #eee; border-radius: 12px; padding: 20px; }
        .avance11-panel h2 { color: #e0e0ff; border-color: #5c5cff; }
        .avance11-panel h3 { color: #aad4f5; }
        .avance11-panel table th { background: #0f3460; color: #eee; }
        .avance11-panel table td { border-color: #2a2a4a; color: #ccc; }
        .avance11-panel input, .avance11-panel select { background: #0f3460; color: white; border: 1px solid #5c5cff; }
        .avance11-panel input::placeholder { color: #aaa; }
        .estrutura-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }
        @media(max-width: 900px) { .estrutura-grid { grid-template-columns: 1fr; } }
        .stack-item { background: #0f3460; border-left: 4px solid #5c5cff; padding: 8px 12px; margin: 4px 0; border-radius: 4px; font-size: 13px; }
        .stack-item.cima { border-left-color: #e74c3c; background: #1a0f3c; }
        .queue-item { background: #0a3d2e; border-left: 4px solid #2ecc71; padding: 8px 12px; margin: 4px 0; border-radius: 4px; font-size: 13px; }
        .queue-item.primero { border-left-color: #f39c12; background: #3d2a0a; }
        .cat-block { background: #0f3460; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
        .cat-block h4 { color: #aad4f5; margin: 0 0 8px 0; font-size: 13px; text-transform: uppercase; }
        .cat-prod { font-size: 12px; color: #ccc; padding: 3px 0; border-bottom: 1px solid #1a2a4a; }
        .turno-badge { display: inline-block; background: #f39c12; color: #1a1a2e; font-weight: bold; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 6px; }
        .avance11-panel button { background: #3498db; }
        .avance11-panel .btn-success { background: #2ecc71; color: #1a1a2e; }
        .avance11-panel .btn-warning { background: #f39c12; color: #1a1a2e; }
        .avance11-panel .btn-danger  { background: #e74c3c; width: 100%; padding: 10px; }
        .avance11-panel .btn-purple  { background: #8e44ad; }
    </style>
</head>
<body>
<div class="container">

    <!-- ENCABEZADO -->
    <div class="card full-width" style="text-align:center;">
        <h1>🍗 {{ nombre }}</h1>
        <p>NIT: {{ nit }} | {{ direccion }} | Tel: {{ telefono }}</p>
    </div>

    <!-- INVENTARIO -->
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
        <div style="max-height: 280px; overflow-y: auto; margin-top: 10px;">
            <table>
                <thead><tr><th>Cód</th><th>Producto</th><th>Precio</th><th>Stock</th><th>Tipo</th><th>🗑️</th></tr></thead>
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

    <!-- VENTA RÁPIDA -->
    <div class="card">
        <h2>🛒 Venta Rápida / Fast Sale</h2>
        <form action="/carrito/agregar" method="POST">
            <div style="display:flex; gap:10px;">
                <input type="number" name="codigo_vta" placeholder="Código / Code..." required autofocus>
                <input type="number" step="0.01" name="cantidad" placeholder="Cant." required style="width:100px;">
                <button type="submit" style="width:120px;">Añadir</button>
            </div>
        </form>
        <hr>
        <h3>👤 Datos Cliente / Client Data</h3>
        <form action="/cliente/actualizar" method="POST">
            <input type="text" name="nombre" placeholder="Nombre / Name" value="{{ cliente.nombre }}">
            <input type="text" name="documento" placeholder="Cédula/NIT" value="{{ cliente.documento }}">
            <button type="submit" style="background:#95a5a6;">Actualizar / Update</button>
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

    <!-- HISTORIAL -->
    <div class="card full-width">
        <h2>📊 Historial y Buscador / History & Search</h2>
        <form action="/" method="GET" style="display:flex; gap:10px; margin-bottom:15px;">
            <input type="text" name="buscar" placeholder="Cédula o Nombre / ID or Name..." value="{{ busqueda }}">
            <button type="submit" style="width:140px;">🔍 Buscar / Search</button>
        </form>
        <table>
            <thead><tr><th>No.</th><th>Fecha / Date</th><th>Cliente</th><th>Cédula</th><th>Total</th><th>Opciones</th></tr></thead>
            <tbody>
                {% for f in historial %}
                <tr>
                    <td>#{{ f.id }}</td>
                    <td>{{ f.fecha[:16] }}</td>
                    <td>{{ f.cliente_nombre }}</td>
                    <td>{{ f.cliente_documento }}</td>
                    <td><b>${{ "{:,.0f}".format(f.total) }}</b></td>
                    <td><a href="/factura/pdf/{{ f.id }}" target="_blank">🖨️ PDF</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- ====================================================== -->
    <!-- AVANCE 11: PANEL DE ESTRUCTURAS DINÁMICAS              -->
    <!-- ====================================================== -->
    <div class="avance11-panel full-width">
        <h2>⚡ AVANCE 11 — Estructuras Dinámicas / Dynamic Structures</h2>

        <div class="estrutura-grid">

            <!-- MÓDULO 1: PILA -->
            <div>
                <h3>🗂️ Módulo 1: Pila de Historial (LIFO)</h3>
                <p style="font-size:12px; color:#aaa;">
                    Registra cada acción del sistema. La cima (borde rojo) es la última — puedes deshacerla.<br>
                    Records every system action. Top (red border) is the last — undo it.
                </p>
                {% if pila_acciones %}
                    {% for accion in pila_acciones %}
                    <div class="stack-item {% if loop.first %}cima{% endif %}">
                        <b>{{ loop.index }}. {{ accion.tipo }}</b><br>
                        <span style="font-size:11px; color:#aaa;">{{ accion.detalle }} | {{ accion.hora }}</span>
                    </div>
                    {% endfor %}
                    <form action="/pila/deshacer" method="POST" style="margin-top:10px;">
                        <button class="btn-danger">↩️ Deshacer Última Acción / Undo Last Action</button>
                    </form>
                {% else %}
                    <p style="color:#666; font-size:13px;">Pila vacía — realiza acciones para verlas aquí.<br>Stack empty — perform actions to see them here.</p>
                {% endif %}
                <p style="font-size:11px; color:#666; margin-top:8px;">
                    Elementos en pila / Items in stack: <b style="color:#aad4f5;">{{ pila_acciones|length }}</b>
                </p>
            </div>

            <!-- MÓDULO 2: COLA -->
            <div>
                <h3>🎫 Módulo 2: Cola de Turnos (FIFO)</h3>
                <p style="font-size:12px; color:#aaa;">
                    Pedidos en orden de llegada. El primero (borde naranja) es el próximo a atender.<br>
                    Orders in arrival order. First (orange border) is next to serve.
                </p>
                <form action="/cola/agregar_turno" method="POST">
                    <input type="text" name="nombre_turno" placeholder="Nombre del pedido / Order name" required>
                    <button class="btn-success">➕ Agregar Turno / Add Turn</button>
                </form>
                <div style="margin-top:10px;">
                    {% if cola_turnos %}
                        {% for turno in cola_turnos %}
                        <div class="queue-item {% if loop.first %}primero{% endif %}">
                            <span class="turno-badge">#{{ turno.turno }}</span>
                            <b>{{ turno.cliente }}</b>
                            <span style="font-size:11px; color:#aaa;"> — {{ turno.hora_ingreso }}</span>
                            {% if turno.items is defined and turno.items %}
                            <br><span style="font-size:11px; color:#88cc88;">{{ turno.items }}</span>
                            {% endif %}
                        </div>
                        {% endfor %}
                        <form action="/cola/atender_turno" method="POST" style="margin-top:8px;">
                            <button class="btn-warning">✅ Atender Siguiente / Serve Next</button>
                        </form>
                    {% else %}
                        <p style="color:#666; font-size:13px;">Cola vacía — no hay turnos pendientes.<br>Queue empty — no pending turns.</p>
                    {% endif %}
                </div>
                <p style="font-size:11px; color:#666; margin-top:8px;">
                    En espera / Waiting: <b style="color:#aad4f5;">{{ cola_turnos|length }}</b>
                </p>
            </div>

            <!-- MÓDULO 3: DICCIONARIO DE COLAS -->
            <div>
                <h3>📂 Módulo 3: Diccionario de Colas</h3>
                <p style="font-size:12px; color:#aaa;">
                    Inventario agrupado por categoría. Cada categoría es una cola independiente.<br>
                    Inventory grouped by category. Each category is an independent queue.
                </p>
                <form action="/dict_colas/recargar" method="POST">
                    <button class="btn-purple">🔄 Recargar desde Inventario / Reload from Inventory</button>
                </form>
                <div style="margin-top:10px; max-height:300px; overflow-y:auto;">
                    {% if dict_colas_datos %}
                        {% for cat, productos in dict_colas_datos.items() %}
                        <div class="cat-block">
                            <h4>📁 {{ cat }} ({{ productos|length }} productos)</h4>
                            {% for prod in productos[:3] %}
                            <div class="cat-prod">• {{ prod.producto }} — ${{ "{:,.0f}".format(prod.precio|float) }}</div>
                            {% endfor %}
                            {% if productos|length > 3 %}
                            <div class="cat-prod" style="color:#888;">... y {{ productos|length - 3 }} más / and {{ productos|length - 3 }} more</div>
                            {% endif %}
                        </div>
                        {% endfor %}
                    {% else %}
                        <p style="color:#666; font-size:13px;">Vacío — usa "Recargar" para cargar el inventario.<br>Empty — use "Reload" to load inventory.</p>
                    {% endif %}
                </div>
                <p style="font-size:11px; color:#666; margin-top:8px;">
                    Categorías activas / Active categories: <b style="color:#aad4f5;">{{ dict_colas_datos|length }}</b>
                </p>
            </div>

        </div>
    </div>
    <!-- FIN AVANCE 11 -->

</div>
</body>
</html>
"""

# ============================================================
# INICIALIZAR SESIÓN / INITIALIZE SESSION
# ============================================================
def init_session():
    if 'carrito' not in session:
        session['carrito'] = []
    if 'cliente' not in session:
        session['cliente'] = {
            "nombre": "Consumidor Final",
            "documento": "222222222",
            "puntos": 0,
            "es_frecuente": False
        }
    if 'pila' not in session:
        session['pila'] = []
    if 'cola' not in session:
        session['cola'] = []
        session['cola_contador'] = 0
    if 'dict_colas' not in session:
        session['dict_colas'] = {}

# ============================================================
# INDEX
# ============================================================
@app.route("/")
def index():
    init_session()

    buscar = estandarizar_dato(request.args.get('buscar', '')).strip()

    inv_res = supabase.table("inventario").select("*").order("codigo").execute()
    inv = inv_res.data if inv_res.data else []

    if buscar:
        his_res = supabase.table("facturas").select("*")\
            .or_(f"cliente_documento.ilike.%{buscar}%,cliente_nombre.ilike.%{buscar}%")\
            .order("fecha", desc=True).execute()
    else:
        his_res = supabase.table("facturas").select("*").order("fecha", desc=True).limit(10).execute()

    his   = his_res.data if his_res.data else []
    total = sum(item['total'] for item in session['carrito'])

    return render_template_string(
        HTML_SISTEMA,
        nombre=NOMBRE_LOCAL,
        nit=NIT_NEGOCIO,
        direccion=DIRECCION,
        telefono=TELEFONO,
        inventario=inv,
        carrito=session['carrito'],
        total_venta=total,
        cliente=session['cliente'],
        historial=his,
        busqueda=buscar,
        pila_acciones=pila_lista(),
        cola_turnos=cola_lista(),
        dict_colas_datos=dict_colas_datos()
    )

# ============================================================
# INVENTARIO
# ============================================================
def backup_local_csv(datos):
    try:
        if not datos:
            return
        with open("respaldo_inventario.csv", mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=datos[0].keys())
            writer.writeheader()
            writer.writerows(datos)
        print(">>> Backup guardado en hardware.")
    except Exception as e:
        print(f">>> ERROR backup: {e}")


@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    try:
        init_session()
        c = request.form
        id_cat     = c.get('categoria_id', '1')
        nombre_cat = obtener_nombre_categoria(id_cat)

        nuevo_prod = Producto(
            codigo=c.get('codigo'),
            nombre=c.get('producto'),
            precio=c.get('precio'),
            categoria=nombre_cat
        )

        inventario_lista.add_node(nuevo_prod)

        datos_preparados = nuevo_prod.to_dict()
        datos_preparados["stock"] = float(c.get('stock') or 0)
        datos_preparados["tipo"]  = c.get('tipo', 'Und')

        supabase.table("inventario").upsert(datos_preparados).execute()

        pila_push({
            "tipo":          "GUARDAR PRODUCTO",
            "detalle":       f"{nuevo_prod.nombre} (Cod: {nuevo_prod.codigo})",
            "hora":          datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {"codigo": nuevo_prod.codigo}
        })

        dict_colas_encolar(nombre_cat, datos_preparados)

        if not os.environ.get('VERCEL'):
            try:
                res = supabase.table("inventario").select("*").execute()
                backup_local_csv(res.data)
            except Exception as e:
                print(f"Error backup: {e}")

        return redirect("/")
    except Exception as e:
        print("ERROR INVENTARIO:", e)
        return f"<h1>ERROR</h1><pre>{str(e)}</pre>"


@app.route("/inventario/eliminar/<int:codigo>")
def inv_eliminar(codigo):
    init_session()
    inventario_lista.delete_node(codigo)
    supabase.table("inventario").delete().eq("codigo", codigo).execute()

    pila_push({
        "tipo":          "ELIMINAR PRODUCTO",
        "detalle":       f"Codigo eliminado: {codigo}",
        "hora":          datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {"codigo": codigo}
    })

    if not os.environ.get('VERCEL'):
        try:
            res = supabase.table("inventario").select("*").execute()
            backup_local_csv(res.data)
        except Exception as e:
            print(f"Error backup: {e}")

    return redirect("/")


@app.route("/inventario/actualizar_precio", methods=["POST"])
def actualizar_precio_por_llave():
    try:
        init_session()
        cod     = int(request.form.get("codigo"))
        nuevo_p = float(request.form.get("nuevo_precio"))

        res = supabase.table("inventario").update({"precio": nuevo_p}).eq("codigo", cod).execute()

        if res.data:
            print(f"SUCCESS: Producto {cod} actualizado")
            pila_push({
                "tipo":          "ACTUALIZAR PRECIO",
                "detalle":       f"Codigo {cod} -> ${nuevo_p:,.0f}",
                "hora":          datetime.now().strftime("%H:%M:%S"),
                "datos_reversa": {"codigo": cod}
            })
        else:
            print(f"NOT FOUND: Codigo {cod}")

        if not os.environ.get('VERCEL'):
            res_r = supabase.table("inventario").select("*").execute()
            backup_local_csv(res_r.data)

        return redirect("/")
    except Exception as e:
        print(f"ERROR actualizar precio: {e}")
        return redirect("/")

# ============================================================
# CARRITO / CART
# ============================================================
@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    init_session()
    cod = request.form.get("codigo_vta")

    try:
        cant = float(request.form.get("cantidad", 0))
        if cant <= 0:
            return redirect("/")
    except:
        return redirect("/")

    res = supabase.table("inventario").select("*").eq("codigo", cod).execute()
    p   = res.data[0] if res.data else None

    if not p or float(p['stock']) < cant:
        return redirect("/")

    carrito = session.get('carrito', [])
    existe  = False
    for item in carrito:
        if item['codigo'] == cod:
            item['cantidad'] += cant
            item['total']    = round(item['cantidad'] * float(p['precio']), 2)
            existe = True
            break

    if not existe:
        carrito.append({
            "codigo":   cod,
            "nombre":   p['producto'],
            "cantidad": cant,
            "total":    round(float(p['precio']) * cant, 2),
            "tipo":     p['tipo']
        })

    session['carrito'] = carrito

    pila_push({
        "tipo":          "AGREGAR AL CARRITO",
        "detalle":       f"{p['producto']} x{cant}",
        "hora":          datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {"codigo": cod, "cantidad": cant}
    })

    return redirect("/")


@app.route("/carrito/limpiar")
def car_limpiar():
    init_session()
    session['carrito'] = []
    pila_push({
        "tipo":          "VACIAR CARRITO",
        "detalle":       "Carrito limpiado manualmente",
        "hora":          datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {}
    })
    return redirect("/")

# ============================================================
# CLIENTE / CLIENT
# ============================================================
@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    init_session()
    nom_cli = estandarizar_dato(request.form.get("nombre"),    mayusculas=True)
    doc_cli = estandarizar_dato(request.form.get("documento"))

    res = supabase.table("clientes").select("*").eq("cedula", doc_cli).execute()

    if res.data:
        c_db = res.data[0]
        session['cliente'] = {
            "nombre":       c_db['nombre'],
            "documento":    c_db['cedula'],
            "puntos":       c_db.get('puntos', 0),
            "es_frecuente": True
        }
        print("CLIENT DATA RETRIEVED")
    else:
        session['cliente'] = {
            "nombre":       nom_cli,
            "documento":    doc_cli,
            "puntos":       0,
            "es_frecuente": False
        }
        print("NEW CLIENT IN SESSION")

    pila_push({
        "tipo":          "ACTUALIZAR CLIENTE",
        "detalle":       f"{nom_cli} | Doc: {doc_cli}",
        "hora":          datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {}
    })
    return redirect("/")

# ============================================================
# VENTA FINALIZAR / FINALIZE SALE
# ============================================================
@app.route("/venta/finalizar")
def venta_finalizar():
    init_session()
    carrito = session.get('carrito', [])
    cliente = session.get('cliente', {})

    if not carrito:
        return redirect("/")

    total = sum(item['total'] for item in carrito)
    fecha = datetime.now().isoformat()

    try:
        res = supabase.table("facturas").insert({
            "cliente_nombre":    cliente.get('nombre', 'Consumidor Final'),
            "cliente_documento": cliente.get('documento', '0'),
            "total":             total,
            "fecha":             fecha,
            "detalle":           str(carrito)
        }).execute()

        factura_id    = res.data[0]['id'] if res.data else "?"
        resumen_items = ", ".join([f"{i['nombre']} x{i['cantidad']}" for i in carrito])

        pila_push({
            "tipo":          "FACTURA GENERADA",
            "detalle":       f"Factura #{factura_id} | {cliente.get('nombre')} | ${total:,.0f}",
            "hora":          datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {"factura_id": factura_id}
        })

        cola_encolar({
            "cliente":    cliente.get('nombre', 'Consumidor Final'),
            "documento":  cliente.get('documento', '0'),
            "total":      total,
            "items":      resumen_items,
            "factura_id": factura_id
        })

    except Exception as e:
        print(f"ERROR AL FINALIZAR VENTA: {e}")

    session['carrito'] = []
    return redirect("/")

# ============================================================
# AVANCE 11 — RUTA: DESHACER ÚLTIMA ACCIÓN / UNDO LAST ACTION
# ============================================================
@app.route("/pila/deshacer", methods=["POST"])
def pila_deshacer():
    init_session()
    accion = pila_pop()

    if accion is None:
        return redirect("/")

    tipo    = accion.get("tipo", "")
    reversa = accion.get("datos_reversa", {})

    if tipo == "GUARDAR PRODUCTO":
        codigo = reversa.get("codigo")
        if codigo:
            inventario_lista.delete_node(int(codigo))
            supabase.table("inventario").delete().eq("codigo", int(codigo)).execute()
            print(f"[UNDO] Producto {codigo} eliminado (revertido)")

    elif tipo == "AGREGAR AL CARRITO":
        codigo = str(reversa.get("codigo"))
        cant   = reversa.get("cantidad", 0)
        carrito = session.get('carrito', [])
        nuevo_carrito = []
        for item in carrito:
            if item['codigo'] == codigo:
                item['cantidad'] -= cant
                if item['cantidad'] > 0:
                    item['total'] = round(item['total'] * item['cantidad'] / (item['cantidad'] + cant), 2)
                    nuevo_carrito.append(item)
            else:
                nuevo_carrito.append(item)
        session['carrito'] = nuevo_carrito
        print(f"[UNDO] Removido del carrito: {codigo} x{cant}")

    else:
        print(f"[UNDO] Accion '{tipo}' sin reversa automatica / No auto-reverse for '{tipo}'")

    return redirect("/")

# ============================================================
# AVANCE 11 — COLA: AGREGAR TURNO MANUAL / ADD MANUAL TURN
# ============================================================
@app.route("/cola/agregar_turno", methods=["POST"])
def cola_agregar_turno():
    init_session()
    nombre_turno = estandarizar_dato(request.form.get("nombre_turno", ""), mayusculas=True)
    if nombre_turno:
        cola_encolar({
            "cliente":  nombre_turno,
            "documento":"---",
            "total":    0,
            "items":    "Pedido presencial / In-person order"
        })
        pila_push({
            "tipo":          "TURNO AGREGADO",
            "detalle":       f"Turno manual: {nombre_turno}",
            "hora":          datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {}
        })
    return redirect("/")

# ============================================================
# AVANCE 11 — COLA: ATENDER SIGUIENTE TURNO / SERVE NEXT TURN
# ============================================================
@app.route("/cola/atender_turno", methods=["POST"])
def cola_atender_turno():
    init_session()
    turno = cola_desencolar()
    if turno:
        pila_push({
            "tipo":          "TURNO ATENDIDO",
            "detalle":       f"Turno #{turno.get('turno')} — {turno.get('cliente')}",
            "hora":          datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {}
        })
    return redirect("/")

# ============================================================
# AVANCE 11 — DICT-COLAS: RECARGAR DESDE INVENTARIO
# ============================================================
@app.route("/dict_colas/recargar", methods=["POST"])
def dict_colas_recargar():
    init_session()
    try:
        res      = supabase.table("inventario").select("*").execute()
        productos = res.data if res.data else []
        dict_colas_cargar(productos)
        pila_push({
            "tipo":          "DICT-COLAS RECARGADO",
            "detalle":       f"{len(productos)} productos cargados",
            "hora":          datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {}
        })
    except Exception as e:
        print(f"[DICT-COLAS] Error al recargar: {e}")
    return redirect("/")

# ============================================================
# AVANCE 11 — API JSON: ESTADO DE ESTRUCTURAS / STRUCTURES STATE
# ============================================================
@app.route("/avance11/estado")
def avance11_estado():
    init_session()
    return jsonify({
        "avance": 11,
        "modulo_1_pila": {
            "descripcion": "LIFO — Historial de acciones / Action history",
            "tamanio":     len(session.get('pila', [])),
            "cima":        pila_peek(),
            "contenido":   pila_lista()
        },
        "modulo_2_cola": {
            "descripcion": "FIFO — Cola de turnos / Turn queue",
            "tamanio":     len(session.get('cola', [])),
            "primero":     cola_lista()[0] if cola_lista() else None,
            "contenido":   cola_lista()
        },
        "modulo_3_dict_colas": {
            "descripcion": "Diccionario de Colas por categoria / Dict of Queues by category",
            "categorias":  list(dict_colas_datos().keys()),
            "contenido":   dict_colas_datos()
        }
    })

# ============================================================
# FACTURA PDF / INVOICE PDF  ← ARREGLADO: limpiar_texto_pdf()
# ============================================================
@app.route("/factura/pdf/<int:factura_id>")
def factura_pdf(factura_id):
    """
    ESP: Genera y devuelve el PDF de una factura consultada desde Supabase.
         FIX: Se usa limpiar_texto_pdf() para evitar errores con caracteres
         especiales (tildes, ñ, guiones largos, etc.) en fpdf.
    ENG: Generates and returns the PDF of an invoice queried from Supabase.
         FIX: limpiar_texto_pdf() used to avoid special character errors in fpdf.
    """
    try:
        res = supabase.table("facturas").select("*").eq("id", factura_id).execute()
        if not res.data:
            return f"<h2>Factura #{factura_id} no encontrada / Invoice not found</h2><a href='/'>← Volver</a>", 404

        f = res.data[0]

        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)

        # Encabezado
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, limpiar_texto_pdf(NOMBRE_LOCAL), ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"NIT: {limpiar_texto_pdf(NIT_NEGOCIO)}", ln=True, align="C")
        pdf.cell(0, 6, limpiar_texto_pdf(DIRECCION), ln=True, align="C")
        pdf.cell(0, 6, f"Tel: {limpiar_texto_pdf(TELEFONO)}", ln=True, align="C")
        pdf.ln(4)

        # Línea separadora
        pdf.set_draw_color(52, 152, 219)
        pdf.set_line_width(0.8)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

        # Datos de la factura
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"FACTURA No. {f['id']}", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        fecha_str = f.get('fecha', '')[:16].replace('T', ' ')
        pdf.cell(0, 6, f"Fecha / Date: {fecha_str}", ln=True, align="C")
        pdf.ln(4)

        # Datos del cliente
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(230, 240, 255)
        pdf.cell(0, 7, "DATOS DEL CLIENTE / CLIENT DATA", ln=True, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"Nombre / Name:     {limpiar_texto_pdf(f.get('cliente_nombre', '---'))}", ln=True)
        pdf.cell(0, 6, f"Cedula / ID:       {limpiar_texto_pdf(f.get('cliente_documento', '---'))}", ln=True)
        pdf.ln(4)

        # Detalle de productos
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(230, 240, 255)
        pdf.cell(0, 7, "DETALLE / DETAIL", ln=True, fill=True)

        detalle_raw = f.get('detalle', '')
        try:
            import ast
            items = ast.literal_eval(detalle_raw) if detalle_raw else []
        except:
            items = []

        if items:
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(52, 152, 219)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(70, 7, "Producto / Product", border=1, fill=True)
            pdf.cell(30, 7, "Cantidad / Qty", border=1, fill=True, align="C")
            pdf.cell(30, 7, "Tipo / Unit", border=1, fill=True, align="C")
            pdf.cell(40, 7, "Total", border=1, fill=True, align="R")
            pdf.ln()

            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(0, 0, 0)
            fill = False
            for item in items:
                pdf.set_fill_color(245, 249, 255) if fill else pdf.set_fill_color(255, 255, 255)
                pdf.cell(70, 6, limpiar_texto_pdf(str(item.get('nombre', ''))), border=1, fill=fill)
                pdf.cell(30, 6, limpiar_texto_pdf(str(item.get('cantidad', ''))), border=1, fill=fill, align="C")
                pdf.cell(30, 6, limpiar_texto_pdf(str(item.get('tipo', ''))), border=1, fill=fill, align="C")
                pdf.cell(40, 6, f"${float(item.get('total', 0)):,.0f}", border=1, fill=fill, align="R")
                pdf.ln()
                fill = not fill
        else:
            pdf.set_font("Arial", "I", 9)
            pdf.cell(0, 6, limpiar_texto_pdf(str(detalle_raw)[:200]), ln=True)

        pdf.ln(4)

        # Totales
        total     = float(f.get('total', 0))
        subtotal  = round(total / (1 + VALOR_IVA), 2)
        iva_valor = round(total - subtotal, 2)

        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Arial", "", 10)
        pdf.cell(140, 6, "Subtotal:", align="R")
        pdf.cell(40, 6, f"${subtotal:,.0f}", ln=True, align="R")
        pdf.cell(140, 6, f"IVA ({int(VALOR_IVA*100)}%):", align="R")
        pdf.cell(40, 6, f"${iva_valor:,.0f}", ln=True, align="R")
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(39, 174, 96)
        pdf.cell(140, 8, "TOTAL:", align="R")
        pdf.cell(40, 8, f"${total:,.0f}", ln=True, align="R")
        pdf.set_text_color(0, 0, 0)

        pdf.ln(6)
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, "Gracias por su compra / Thank you for your purchase", ln=True, align="C")
        pdf.cell(0, 5, limpiar_texto_pdf(f"{NOMBRE_LOCAL} - {DIRECCION}"), ln=True, align="C")

        # Enviar PDF
        pdf_bytes = bytes(pdf.output())
        buffer    = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"factura_{factura_id}.pdf"
        )

    except Exception as e:
        print(f"ERROR GENERANDO PDF: {e}")
        return f"<h2>Error al generar PDF</h2><pre>{str(e)}</pre><a href='/'>← Volver</a>", 500


# ============================================================
# REPORTE LISTA ENLAZADA (AVANCE 10)
# ============================================================
@app.route("/inventario/reporte")
def reporte_lista_enlazada():
    inventario_lista.generate_report()
    return "<h2>Reporte generado en consola / Report in console</h2><a href='/'>Volver / Back</a>"

# ============================================================
# CORTE DE CONTROL / CONTROL BREAK REPORT
# ============================================================
def generar_reporte_agrupado(lista_datos):
    datos_ordenados = sorted(lista_datos, key=lambda x: x['categoria'])
    cat_actual, acumulado = None, 0
    print("\n" + "="*40 + "\nREPORTE GRUPAL - CORTE DE CONTROL\n" + "="*40)
    for item in datos_ordenados:
        if item['categoria'] != cat_actual:
            if cat_actual is not None:
                print(f"--- TOTAL {cat_actual}: ${acumulado:,.0f} ---")
            cat_actual = item['categoria']
            acumulado  = 0
            print(f"\n[ CATEGORIA: {cat_actual} ]")
        print(f" > {item['producto']}: ${float(item['precio']):,.0f}")
        acumulado += float(item['precio'])
    if cat_actual:
        print(f"--- TOTAL {cat_actual}: ${acumulado:,.0f} ---")
    print("="*40 + "\n")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    simulador_memoria()
    print("\n=== AVANCE 11: ESTRUCTURAS DINÁMICAS (sesión) ===")
    print("  Pila  : LIFO en session['pila']")
    print("  Cola  : FIFO en session['cola']")
    print("  Dict  : session['dict_colas']")
    print("  API   : GET /avance11/estado")
    print("=" * 50 + "\n")
    app.run(debug=True)