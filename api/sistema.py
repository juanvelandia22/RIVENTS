# ============================================================
# SISTEMA DE FACTURACIÓN - POLLO Y CHARCUTERÍA RAÚL
# BILLING SYSTEM - POLLO Y CHARCUTERÍA RAÚL
#
# Framework: Flask (Python) | Base de datos / Database: Supabase
# Generación de PDF / PDF Generation: fpdf
# Sesiones / Sessions: Flask Session
# AVANCE 11: Pila, Cola, Diccionario de Colas
# ============================================================
import csv
from flask import Flask, render_template_string, request, redirect, session, send_file, url_for, jsonify
from supabase import create_client, Client
from datetime import datetime
import os
from fpdf import FPDF
import io
from collections import deque   # AVANCE 11: Para la Cola eficiente / For efficient Queue

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
# AVANCE 10 MVP - LINKED LIST / LISTA ENLAZADA
# ============================================================
class Node:
    """Nodo de lista enlazada. / Linked list node."""
    def __init__(self, product):
        self.product = product
        self.next = None

class LinkedList:
    """Lista enlazada para inventario. / Linked list for inventory."""
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
        print("Producto no encontrado / Product not found")
        return False

    def find_node(self, codigo):
        current = self.head
        while current:
            if current.product.codigo == codigo:
                return current.product
            current = current.next
        return None

    def display_list(self):
        current = self.head
        while current:
            print(f"{current.product.codigo} - {current.product.nombre}")
            current = current.next

    def generate_report(self):
        current = self.head
        while current:
            p = current.product
            print(f"{p.codigo} | {p.nombre} | ${p.precio}")
            current = current.next

inventario_lista = LinkedList()

# ============================================================
# AVANCE 11 - MÓDULO 1: PILA (STACK) PARA HISTORIAL DE ACCIONES
# AVANCE 11 - MODULE 1: STACK FOR ACTION HISTORY (UNDO)
# ============================================================
class PilaAcciones:
    """
    ESP: Pila (LIFO) para registrar acciones del sistema y permitir deshacer.
    ENG: Stack (LIFO) to register system actions and enable undo.

    Operaciones / Operations:
    - push(accion): Registra una acción / Registers an action.
    - pop(): Retira y retorna la última acción / Removes and returns the last action.
    - peek(): Consulta sin eliminar / Peeks without removing.
    - esta_vacia(): Verifica si está vacía / Checks if empty.
    """
    def __init__(self):
        self._datos = []  # Lista interna como base de la pila / Internal list as stack base

    def push(self, accion: dict):
        """Apila una acción. / Pushes an action onto the stack."""
        self._datos.append(accion)
        print(f"[PILA PUSH] Acción registrada: {accion.get('tipo')} / Action registered: {accion.get('tipo')}")

    def pop(self):
        """Desapila la última acción. / Pops the last action."""
        if self.esta_vacia():
            print("[PILA POP] Pila vacía / Stack is empty")
            return None
        accion = self._datos.pop()
        print(f"[PILA POP] Deshaciendo: {accion.get('tipo')} / Undoing: {accion.get('tipo')}")
        return accion

    def peek(self):
        """Consulta la cima sin eliminar. / Peeks at the top without removing."""
        if self.esta_vacia():
            return None
        return self._datos[-1]

    def esta_vacia(self):
        return len(self._datos) == 0

    def tamanio(self):
        return len(self._datos)

    def a_lista(self):
        """Retorna copia como lista (cima al inicio). / Returns copy as list (top first)."""
        return list(reversed(self._datos))


# ============================================================
# AVANCE 11 - MÓDULO 2: COLA (QUEUE) PARA TURNOS/PEDIDOS
# AVANCE 11 - MODULE 2: QUEUE FOR TURNS/ORDERS (FIFO)
# ============================================================
class ColaTurnos:
    """
    ESP: Cola (FIFO) para gestionar pedidos en orden de llegada.
    ENG: Queue (FIFO) to manage orders in arrival order.

    Operaciones / Operations:
    - encolar(pedido): Agrega al final / Adds to the end.
    - desencolar(): Atiende el primero / Serves the first.
    - ver_primero(): Consulta sin eliminar / Peeks without removing.
    - esta_vacia(): Verifica si está vacía / Checks if empty.
    """
    def __init__(self):
        self._datos = deque()  # deque es O(1) en ambos extremos / deque is O(1) at both ends
        self._contador = 0     # Contador de turno / Turn counter

    def encolar(self, pedido: dict):
        """Agrega un pedido al final de la cola. / Enqueues an order."""
        self._contador += 1
        pedido['turno'] = self._contador
        pedido['hora_ingreso'] = datetime.now().strftime("%H:%M:%S")
        self._datos.append(pedido)
        print(f"[COLA ENCOLAR] Turno #{self._contador} asignado a {pedido.get('cliente')} / Turn #{self._contador} assigned to {pedido.get('cliente')}")

    def desencolar(self):
        """Atiende el primer pedido de la cola. / Dequeues and serves first order."""
        if self.esta_vacia():
            print("[COLA DESENCOLAR] Cola vacía / Queue is empty")
            return None
        pedido = self._datos.popleft()
        print(f"[COLA DESENCOLAR] Atendiendo turno #{pedido.get('turno')} / Serving turn #{pedido.get('turno')}")
        return pedido

    def ver_primero(self):
        """Consulta el primero sin atenderlo. / Peeks at the first without serving."""
        if self.esta_vacia():
            return None
        return self._datos[0]

    def esta_vacia(self):
        return len(self._datos) == 0

    def tamanio(self):
        return len(self._datos)

    def a_lista(self):
        """Retorna todos los turnos como lista. / Returns all turns as a list."""
        return list(self._datos)


# ============================================================
# AVANCE 11 - MÓDULO 3: DICCIONARIO DE COLAS (ESTRUCTURA COMBINADA)
# AVANCE 11 - MODULE 3: DICTIONARY OF QUEUES (COMBINED STRUCTURE)
#
# ESP: Organiza productos por categoría. Cada categoría es una Cola.
#      Esto cumple el requisito de "Estructura Combinada" del microcurrículo.
# ENG: Organizes products by category. Each category is a Queue.
#      This fulfills the "Combined Structure" requirement of the microcurriculum.
# ============================================================
class DiccionarioDeColas:
    """
    ESP: Diccionario de Colas. Cada clave es una categoría; el valor es una Cola de productos.
         Permite gestionar el inventario agrupado por categoría en orden de ingreso.
    ENG: Dictionary of Queues. Each key is a category; the value is a Queue of products.
         Allows managing inventory grouped by category in order of entry.
    """
    def __init__(self):
        self._mapa = {}  # { "categoria": deque([producto1, producto2, ...]) }

    def encolar_producto(self, categoria: str, producto: dict):
        """Agrega un producto a la cola de su categoría. / Adds product to its category queue."""
        cat = categoria.upper()
        if cat not in self._mapa:
            self._mapa[cat] = deque()
        self._mapa[cat].append(producto)
        print(f"[DICT-COLAS] Producto '{producto.get('producto')}' encolado en categoría '{cat}' / Product enqueued in category '{cat}'")

    def desencolar_producto(self, categoria: str):
        """Atiende (desencola) el primer producto de la categoría. / Dequeues first product of category."""
        cat = categoria.upper()
        if cat not in self._mapa or len(self._mapa[cat]) == 0:
            print(f"[DICT-COLAS] Categoría '{cat}' vacía o inexistente / Category '{cat}' empty or not found")
            return None
        return self._mapa[cat].popleft()

    def ver_categoria(self, categoria: str):
        """Retorna todos los productos de una categoría. / Returns all products of a category."""
        cat = categoria.upper()
        return list(self._mapa.get(cat, []))

    def todas_las_categorias(self):
        """Retorna el diccionario completo como listas. / Returns full dict as lists."""
        return {cat: list(cola) for cat, cola in self._mapa.items()}

    def categorias_disponibles(self):
        """Lista de categorías registradas. / List of registered categories."""
        return list(self._mapa.keys())

    def cargar_desde_inventario(self, lista_productos: list):
        """
        Carga masiva de productos al diccionario de colas.
        Bulk loads products into the dictionary of queues.
        """
        self._mapa = {}
        for p in lista_productos:
            cat = str(p.get('categoria', 'GENERAL')).upper()
            if cat not in self._mapa:
                self._mapa[cat] = deque()
            self._mapa[cat].append(p)
        print(f"[DICT-COLAS] {len(lista_productos)} productos cargados en {len(self._mapa)} categorías / {len(lista_productos)} products loaded into {len(self._mapa)} categories")


# ============================================================
# INSTANCIAS GLOBALES DE AVANCE 11 / GLOBAL INSTANCES - ADVANCE 11
# ============================================================
pila_acciones = PilaAcciones()       # Módulo 1: Pila de historial / History stack
cola_turnos   = ColaTurnos()         # Módulo 2: Cola de pedidos / Order queue
dict_colas    = DiccionarioDeColas() # Módulo 3: Estructura combinada / Combined structure


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
        print("No se encontró archivo de persistencia, iniciando lista vacía.")
    return datos

def guardar_datos_csv(lista_datos):
    if not lista_datos:
        return
    with open(ARCHIVO_PERSISTENCIA, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=lista_datos[0].keys())
        writer.writeheader()
        writer.writerows(lista_datos)
    print("Datos guardados en disco.")

# --- LÓGICA DE APAREO / DATA PAIRING LOGIC ---
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

def estandarizar_dato(texto_entrada, mayusculas=False):
    if not texto_entrada:
        return ""
    limpio = texto_entrada.strip()
    return limpio.upper() if mayusculas else limpio.lower()

# ============================================================
# CONSTANTES / CONSTANTS
# ============================================================
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_NEGOCIO  = "123.456.789-0"
DIRECCION    = "Cúcuta, Norte de Santander"
TELEFONO     = "300 000 0000"
VALOR_IVA    = 0.19

# ============================================================
# SUPABASE
# ============================================================
URL_SUPABASE = "https://paulpnqsfytnpbbitquo.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdWxwbnFzZnl0bnBiYml0cXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNzg2NTIsImV4cCI6MjA4OTg1NDY1Mn0.ts4H83Yba2J8id7-evY-Q2ayFHMluBXjfJVyiZFWtig"
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# ============================================================
# HTML TEMPLATE - CON MÓDULOS AVANCE 11 / WITH ADVANCE 11 MODULES
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
        .btn-dark    { background: #2c3e50; }
        .btn-purple  { background: #8e44ad; }
        .total-display { font-size: 24px; font-weight: bold; color: #27ae60; text-align: center; padding: 15px; background: #f9fffb; border: 2px dashed #2ecc71; border-radius: 8px; margin: 10px 0; }
        .badge { padding: 3px 8px; border-radius: 12px; font-size: 12px; background: #eee; }
        .badge-blue   { background: #d6eaf8; color: #1a5276; }
        .badge-green  { background: #d5f5e3; color: #1e8449; }
        .badge-orange { background: #fdebd0; color: #784212; }
        .badge-red    { background: #fadbd8; color: #922b21; }

        /* ── AVANCE 11 PANEL STYLES ── */
        .avance11-panel { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #eee; border-radius: 12px; padding: 20px; }
        .avance11-panel h2 { color: #e0e0ff; border-color: #5c5cff; }
        .avance11-panel h3 { color: #aad4f5; }
        .avance11-panel table th { background: #0f3460; color: #eee; }
        .avance11-panel table td { border-color: #2a2a4a; color: #ccc; }
        .avance11-panel input, .avance11-panel select {
            background: #0f3460; color: white; border: 1px solid #5c5cff;
        }
        .avance11-panel input::placeholder { color: #aaa; }
        .stack-item { background: #0f3460; border-left: 4px solid #5c5cff; padding: 8px 12px; margin: 4px 0; border-radius: 4px; font-size: 13px; }
        .stack-item:first-child { border-left-color: #e74c3c; background: #1a0f3c; }
        .queue-item { background: #0a3d2e; border-left: 4px solid #2ecc71; padding: 8px 12px; margin: 4px 0; border-radius: 4px; font-size: 13px; }
        .queue-item:first-child { border-left-color: #f39c12; background: #3d2a0a; }
        .cat-block { background: #0f3460; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
        .cat-block h4 { color: #aad4f5; margin: 0 0 8px 0; font-size: 13px; text-transform: uppercase; }
        .cat-prod { font-size: 12px; color: #ccc; padding: 3px 0; border-bottom: 1px solid #1a2a4a; }
        .estrutura-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }
        @media(max-width: 900px) { .estrutura-grid { grid-template-columns: 1fr; } }
        .turno-badge { display: inline-block; background: #f39c12; color: #1a1a2e; font-weight: bold; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 6px; }
    </style>
</head>
<body>
<div class="container">

    <!-- ENCABEZADO / HEADER -->
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
                <thead>
                    <tr><th>Cód</th><th>Producto</th><th>Precio</th><th>Stock</th><th>Tipo</th><th>🗑️</th></tr>
                </thead>
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
            <!-- AVANCE 11: Al finalizar, también se envía a la cola de turnos -->
            <a href="/venta/finalizar"><button class="btn-success">FINALIZAR Y FACTURAR / FINISH & BILL</button></a>
            <a href="/carrito/limpiar"><button style="background:#e74c3c; margin-top:5px;">VACIAR / CLEAR</button></a>
        {% endif %}
    </div>

    <!-- HISTORIAL / HISTORY -->
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
    <!-- AVANCE 11: PANEL PRINCIPAL / MAIN PANEL                -->
    <!-- ====================================================== -->
    <div class="avance11-panel full-width">
        <h2>⚡ AVANCE 11 — Estructuras Dinámicas / Dynamic Structures</h2>

        <div class="estrutura-grid">

            <!-- MÓDULO 1: PILA / STACK -->
            <div>
                <h3>🗂️ Módulo 1: Pila de Historial (LIFO)</h3>
                <p style="font-size:12px; color:#aaa;">Registra cada acción. La cima (rojo) es la última acción — puedes deshacerla. / Records each action. Top (red) is the last — undo it.</p>
                {% if pila_acciones %}
                    {% for accion in pila_acciones %}
                    <div class="stack-item">
                        <b>{{ loop.index }}. {{ accion.tipo }}</b><br>
                        <span style="font-size:11px; color:#aaa;">{{ accion.detalle }} | {{ accion.hora }}</span>
                    </div>
                    {% endfor %}
                    <form action="/pila/deshacer" method="POST" style="margin-top:10px;">
                        <button class="btn-danger" style="width:100%;">↩️ Deshacer Última Acción / Undo Last Action</button>
                    </form>
                {% else %}
                    <p style="color:#666; font-size:13px;">Pila vacía — realiza acciones para verlas aquí. / Stack empty — perform actions to see them here.</p>
                {% endif %}
                <p style="font-size:11px; color:#666; margin-top:8px;">Elementos en pila / Items in stack: <b style="color:#aad4f5;">{{ pila_acciones|length }}</b></p>
            </div>

            <!-- MÓDULO 2: COLA / QUEUE -->
            <div>
                <h3>🎫 Módulo 2: Cola de Turnos (FIFO)</h3>
                <p style="font-size:12px; color:#aaa;">Pedidos en orden de llegada. El primero (naranja) es el próximo a atender. / Orders in arrival order. First (orange) is next to serve.</p>
                <form action="/cola/agregar_turno" method="POST">
                    <input type="text" name="nombre_turno" placeholder="Nombre del pedido / Order name" required>
                    <button class="btn-success" style="width:100%;">➕ Agregar Turno / Add Turn</button>
                </form>
                <div style="margin-top:10px;">
                    {% if cola_turnos %}
                        {% for turno in cola_turnos %}
                        <div class="queue-item">
                            <span class="turno-badge">#{{ turno.turno }}</span>
                            <b>{{ turno.cliente }}</b>
                            <span style="font-size:11px; color:#aaa;"> — {{ turno.hora_ingreso }}</span>
                            {% if turno.items is defined %}<br><span style="font-size:11px; color:#88cc88;">{{ turno.items }}</span>{% endif %}
                        </div>
                        {% endfor %}
                        <form action="/cola/atender_turno" method="POST" style="margin-top:8px;">
                            <button class="btn-warning" style="width:100%;">✅ Atender Siguiente / Serve Next</button>
                        </form>
                    {% else %}
                        <p style="color:#666; font-size:13px;">Cola vacía — no hay turnos pendientes. / Queue empty — no pending turns.</p>
                    {% endif %}
                </div>
                <p style="font-size:11px; color:#666; margin-top:8px;">En espera / Waiting: <b style="color:#aad4f5;">{{ cola_turnos|length }}</b></p>
            </div>

            <!-- MÓDULO 3: DICCIONARIO DE COLAS / DICT OF QUEUES -->
            <div>
                <h3>📂 Módulo 3: Diccionario de Colas</h3>
                <p style="font-size:12px; color:#aaa;">Inventario agrupado por categoría. Cada categoría es una cola independiente. / Inventory grouped by category. Each category is an independent queue.</p>
                <form action="/dict_colas/recargar" method="POST">
                    <button class="btn-purple" style="width:100%; margin-bottom:8px;">🔄 Recargar desde Inventario / Reload from Inventory</button>
                </form>
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
                    <p style="color:#666; font-size:13px;">Vacío — usa "Recargar" para cargar el inventario. / Empty — use "Reload" to load inventory.</p>
                {% endif %}
                <p style="font-size:11px; color:#666; margin-top:8px;">Categorías activas / Active categories: <b style="color:#aad4f5;">{{ dict_colas_datos|length }}</b></p>
            </div>

        </div>
    </div>
    <!-- FIN AVANCE 11 / END ADVANCE 11 -->

</div><!-- /container -->
</body>
</html>
"""


# ============================================================
# INDEX ROUTE
# ============================================================
@app.route("/")
def index():
    if 'carrito' not in session:
        session['carrito'] = []
    if 'cliente' not in session:
        session['cliente'] = {
            "nombre": "Consumidor Final",
            "documento": "222222222",
            "puntos": 0,
            "es_frecuente": False
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
        telefono=TELEFONO,
        inventario=inv,
        carrito=session['carrito'],
        total_venta=total,
        cliente=session['cliente'],
        historial=his,
        busqueda=buscar,
        # AVANCE 11: Datos de las estructuras para el template
        pila_acciones=pila_acciones.a_lista(),
        cola_turnos=cola_turnos.a_lista(),
        dict_colas_datos=dict_colas.todas_las_categorias()
    )


# ============================================================
# INVENTARIO / INVENTORY
# ============================================================
def backup_local_csv(datos):
    try:
        if not datos:
            return
        with open("respaldo_inventario.csv", mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=datos[0].keys())
            writer.writeheader()
            writer.writerows(datos)
        print(">>> ÉXITO: Datos guardados en hardware.")
    except Exception as e:
        print(f">>> ERROR DE PERSISTENCIA: {e}")


@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    try:
        c = request.form
        id_cat = c.get('categoria_id', '1')
        nombre_cat = obtener_nombre_categoria(id_cat)

        nuevo_prod = Producto(
            codigo=c.get('codigo'),
            nombre=c.get('producto'),
            precio=c.get('precio'),
            categoria=nombre_cat
        )

        # Avance 10: insertar en lista enlazada
        inventario_lista.add_node(nuevo_prod)

        datos_preparados = nuevo_prod.to_dict()
        datos_preparados["stock"] = float(c.get('stock') or 0)
        datos_preparados["tipo"] = c.get('tipo', 'Und')

        supabase.table("inventario").upsert(datos_preparados).execute()

        # AVANCE 11 - PILA: Registrar acción "GUARDAR PRODUCTO"
        pila_acciones.push({
            "tipo": "GUARDAR PRODUCTO",
            "detalle": f"Producto {nuevo_prod.nombre} (Cód: {nuevo_prod.codigo})",
            "hora": datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {"codigo": nuevo_prod.codigo}  # Para deshacer / For undo
        })

        # AVANCE 11 - DICT DE COLAS: Encolar en su categoría
        dict_colas.encolar_producto(nombre_cat, datos_preparados)

        if not os.environ.get('VERCEL'):
            try:
                res = supabase.table("inventario").select("*").execute()
                backup_local_csv(res.data)
            except Exception as e:
                print(f"Error respaldo local: {e}")

        return redirect("/")
    except Exception as e:
        print("ERROR INVENTARIO:", e)
        return f"<h1>ERROR INVENTARIO</h1><pre>{str(e)}</pre>"


@app.route("/inventario/eliminar/<int:codigo>")
def inv_eliminar(codigo):
    # Avance 10: eliminar de lista enlazada
    inventario_lista.delete_node(codigo)
    supabase.table("inventario").delete().eq("codigo", codigo).execute()

    # AVANCE 11 - PILA: Registrar acción "ELIMINAR PRODUCTO"
    pila_acciones.push({
        "tipo": "ELIMINAR PRODUCTO",
        "detalle": f"Código eliminado: {codigo}",
        "hora": datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {"codigo": codigo}
    })

    if not os.environ.get('VERCEL'):
        try:
            res = supabase.table("inventario").select("*").execute()
            backup_local_csv(res.data)
        except Exception as e:
            print(f"Error respaldo local: {e}")

    return redirect("/")


@app.route("/inventario/actualizar_precio", methods=["POST"])
def actualizar_precio_por_llave():
    try:
        cod = int(request.form.get("codigo"))
        nuevo_p = float(request.form.get("nuevo_precio"))

        res = supabase.table("inventario").update({"precio": nuevo_p}).eq("codigo", cod).execute()

        if res.data:
            print(f"SUCCESS: Product {cod} updated")
            # AVANCE 11 - PILA: Registrar acción "ACTUALIZAR PRECIO"
            pila_acciones.push({
                "tipo": "ACTUALIZAR PRECIO",
                "detalle": f"Código {cod} → nuevo precio ${nuevo_p:,.0f}",
                "hora": datetime.now().strftime("%H:%M:%S"),
                "datos_reversa": {"codigo": cod, "precio_anterior": None}
            })
        else:
            print(f"NOT FOUND: Key {cod} not valid")

        if not os.environ.get('VERCEL'):
            res_respaldo = supabase.table("inventario").select("*").execute()
            backup_local_csv(res_respaldo.data)

        return redirect("/")
    except Exception as e:
        print(f"ERROR: Update failed: {str(e)}")
        return redirect("/")


# ============================================================
# CARRITO / CART
# ============================================================
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

    # AVANCE 11 - PILA: Registrar acción "AGREGAR AL CARRITO"
    pila_acciones.push({
        "tipo": "AGREGAR AL CARRITO",
        "detalle": f"{p['producto']} x{cant}",
        "hora": datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {"codigo": cod, "cantidad": cant}
    })

    return redirect("/")


@app.route("/carrito/limpiar")
def car_limpiar():
    session['carrito'] = []
    # AVANCE 11 - PILA: Registrar acción "VACIAR CARRITO"
    pila_acciones.push({
        "tipo": "VACIAR CARRITO",
        "detalle": "Carrito limpiado manualmente",
        "hora": datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {}
    })
    return redirect("/")


# ============================================================
# CLIENTE / CLIENT
# ============================================================
@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    nom_cli = estandarizar_dato(request.form.get("nombre"), mayusculas=True)
    doc_cli = estandarizar_dato(request.form.get("documento"))

    res = supabase.table("clientes").select("*").eq("cedula", doc_cli).execute()

    if res.data:
        c_db = res.data[0]
        session['cliente'] = {
            "nombre": c_db['nombre'],
            "documento": c_db['cedula'],
            "puntos": c_db.get('puntos', 0),
            "es_frecuente": True
        }
        print("CLIENT DATA RETRIEVED")
    else:
        session['cliente'] = {
            "nombre": nom_cli,
            "documento": doc_cli,
            "puntos": 0,
            "es_frecuente": False
        }
        print("NEW CLIENT IN SESSION")

    # AVANCE 11 - PILA: Registrar acción "ACTUALIZAR CLIENTE"
    pila_acciones.push({
        "tipo": "ACTUALIZAR CLIENTE",
        "detalle": f"Cliente: {nom_cli} | Doc: {doc_cli}",
        "hora": datetime.now().strftime("%H:%M:%S"),
        "datos_reversa": {}
    })

    return redirect("/")


# ============================================================
# VENTA FINALIZAR / FINALIZE SALE
# (Si ya tenías esta ruta, aquí se integra la cola de turnos)
# ============================================================
@app.route("/venta/finalizar")
def venta_finalizar():
    """
    Finaliza la venta, guarda la factura y:
    - Apila la acción en la Pila / Pushes action to the Stack
    - Encola el pedido en la Cola de Turnos / Enqueues order in Turn Queue
    - Vacía el carrito / Clears the cart
    """
    carrito = session.get('carrito', [])
    cliente = session.get('cliente', {})

    if not carrito:
        return redirect("/")

    total = sum(item['total'] for item in carrito)
    fecha = datetime.now().isoformat()

    # Guardar factura en Supabase
    try:
        res = supabase.table("facturas").insert({
            "cliente_nombre": cliente.get('nombre', 'Consumidor Final'),
            "cliente_documento": cliente.get('documento', '0'),
            "total": total,
            "fecha": fecha,
            "detalle": str(carrito)
        }).execute()

        factura_id = res.data[0]['id'] if res.data else "?"

        # AVANCE 11 - PILA: Registrar acción "FACTURA GENERADA"
        pila_acciones.push({
            "tipo": "FACTURA GENERADA",
            "detalle": f"Factura #{factura_id} | Cliente: {cliente.get('nombre')} | Total: ${total:,.0f}",
            "hora": datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {"factura_id": factura_id}
        })

        # AVANCE 11 - COLA: Encolar el pedido como turno a entregar
        resumen_items = ", ".join([f"{i['nombre']} x{i['cantidad']}" for i in carrito])
        cola_turnos.encolar({
            "cliente": cliente.get('nombre', 'Consumidor Final'),
            "documento": cliente.get('documento', '0'),
            "total": total,
            "items": resumen_items,
            "factura_id": factura_id
        })

    except Exception as e:
        print(f"ERROR AL FINALIZAR VENTA: {e}")

    session['carrito'] = []
    return redirect("/")


# ============================================================
# AVANCE 11 - RUTA: DESHACER ÚLTIMA ACCIÓN / UNDO LAST ACTION
# ============================================================
@app.route("/pila/deshacer", methods=["POST"])
def pila_deshacer():
    """
    ESP: Desapila la última acción y ejecuta la lógica de reversa según el tipo.
    ENG: Pops the last action and executes reverse logic based on type.
    """
    accion = pila_acciones.pop()

    if accion is None:
        print("[UNDO] No hay acciones para deshacer / No actions to undo")
        return redirect("/")

    tipo = accion.get("tipo", "")
    reversa = accion.get("datos_reversa", {})

    print(f"[UNDO] Deshaciendo acción tipo: {tipo} / Undoing action type: {tipo}")

    # Lógica de reversa por tipo de acción / Reverse logic by action type
    if tipo == "GUARDAR PRODUCTO":
        # Deshacer = eliminar el producto guardado
        codigo = reversa.get("codigo")
        if codigo:
            inventario_lista.delete_node(int(codigo))
            supabase.table("inventario").delete().eq("codigo", int(codigo)).execute()
            print(f"[UNDO] Producto {codigo} eliminado (revertido) / Product {codigo} deleted (reverted)")

    elif tipo == "AGREGAR AL CARRITO":
        # Deshacer = quitar la última unidad agregada al carrito
        codigo = str(reversa.get("codigo"))
        cant = reversa.get("cantidad", 0)
        carrito = session.get('carrito', [])
        nuevo_carrito = []
        for item in carrito:
            if item['codigo'] == codigo:
                item['cantidad'] -= cant
                item['total'] = round(item['cantidad'] * (item['total'] / (item['cantidad'] + cant)), 2)
                if item['cantidad'] > 0:
                    nuevo_carrito.append(item)
                # Si cantidad <= 0, se descarta el ítem
            else:
                nuevo_carrito.append(item)
        session['carrito'] = nuevo_carrito
        print(f"[UNDO] Producto {codigo} x{cant} removido del carrito / Removed from cart")

    elif tipo == "ELIMINAR PRODUCTO":
        # No se puede restaurar automáticamente sin snapshot completo
        print(f"[UNDO] Eliminación de producto no reversible automáticamente / Product deletion not auto-reversible")

    elif tipo == "VACIAR CARRITO":
        print(f"[UNDO] Vaciado de carrito no reversible automáticamente / Cart clear not auto-reversible")

    else:
        print(f"[UNDO] Acción '{tipo}' registrada pero sin reversa automática / Action registered without auto-reverse")

    return redirect("/")


# ============================================================
# AVANCE 11 - RUTA: AGREGAR TURNO MANUAL / ADD MANUAL TURN
# ============================================================
@app.route("/cola/agregar_turno", methods=["POST"])
def cola_agregar_turno():
    """
    ESP: Permite agregar un turno manualmente a la cola (pedidos presenciales).
    ENG: Allows manually adding a turn to the queue (in-person orders).
    """
    nombre_turno = estandarizar_dato(request.form.get("nombre_turno", ""), mayusculas=True)
    if nombre_turno:
        cola_turnos.encolar({
            "cliente": nombre_turno,
            "documento": "---",
            "total": 0,
            "items": "Pedido presencial / In-person order"
        })
        # AVANCE 11 - PILA: Registrar la acción de agregar turno
        pila_acciones.push({
            "tipo": "TURNO AGREGADO",
            "detalle": f"Turno manual: {nombre_turno}",
            "hora": datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {}
        })
    return redirect("/")


# ============================================================
# AVANCE 11 - RUTA: ATENDER SIGUIENTE TURNO / SERVE NEXT TURN
# ============================================================
@app.route("/cola/atender_turno", methods=["POST"])
def cola_atender_turno():
    """
    ESP: Desencola y atiende el primer turno en la cola (FIFO).
    ENG: Dequeues and serves the first turn in the queue (FIFO).
    """
    turno = cola_turnos.desencolar()
    if turno:
        print(f"[COLA ATENDIDA] Turno #{turno.get('turno')} — {turno.get('cliente')} / Turn served")
        # AVANCE 11 - PILA: Registrar que se atendió un turno
        pila_acciones.push({
            "tipo": "TURNO ATENDIDO",
            "detalle": f"Turno #{turno.get('turno')} — {turno.get('cliente')}",
            "hora": datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {}
        })
    return redirect("/")


# ============================================================
# AVANCE 11 - RUTA: RECARGAR DICCIONARIO DE COLAS / RELOAD DICT OF QUEUES
# ============================================================
@app.route("/dict_colas/recargar", methods=["POST"])
def dict_colas_recargar():
    """
    ESP: Recarga el Diccionario de Colas desde el inventario actual en Supabase.
    ENG: Reloads the Dictionary of Queues from current inventory in Supabase.
    """
    try:
        res = supabase.table("inventario").select("*").execute()
        productos = res.data if res.data else []
        dict_colas.cargar_desde_inventario(productos)
        print(f"[DICT-COLAS] Recargado con {len(productos)} productos / Reloaded with {len(productos)} products")
        pila_acciones.push({
            "tipo": "DICT-COLAS RECARGADO",
            "detalle": f"{len(productos)} productos en {len(dict_colas.categorias_disponibles())} categorías",
            "hora": datetime.now().strftime("%H:%M:%S"),
            "datos_reversa": {}
        })
    except Exception as e:
        print(f"[DICT-COLAS] Error al recargar: {e}")
    return redirect("/")


# ============================================================
# AVANCE 11 - API JSON: ESTADO DE LAS ESTRUCTURAS / STRUCTURES STATE
# ============================================================
@app.route("/avance11/estado")
def avance11_estado():
    """
    ESP: Retorna el estado actual de las 3 estructuras en formato JSON.
         Útil para debugging y verificación del avance.
    ENG: Returns current state of the 3 structures in JSON format.
         Useful for debugging and advance verification.
    """
    return jsonify({
        "avance": 11,
        "modulo_1_pila": {
            "descripcion": "LIFO - Historial de acciones / Action history",
            "tamanio": pila_acciones.tamanio(),
            "cima": pila_acciones.peek(),
            "contenido": pila_acciones.a_lista()
        },
        "modulo_2_cola": {
            "descripcion": "FIFO - Cola de turnos / Turn queue",
            "tamanio": cola_turnos.tamanio(),
            "primero": cola_turnos.ver_primero(),
            "contenido": cola_turnos.a_lista()
        },
        "modulo_3_dict_colas": {
            "descripcion": "Diccionario de Colas por categoría / Dict of Queues by category",
            "categorias": dict_colas.categorias_disponibles(),
            "contenido": dict_colas.todas_las_categorias()
        }
    })


# ============================================================
# REPORTE LISTA ENLAZADA / LINKED LIST REPORT (AVANCE 10)
# ============================================================
@app.route("/inventario/reporte")
def reporte_lista_enlazada():
    inventario_lista.generate_report()
    return "<h2>Reporte generado en consola / Report generated in console</h2><a href='/'>Volver / Back</a>"


# ============================================================
# CORTE DE CONTROL / CONTROL BREAK REPORT
# ============================================================
def generar_reporte_agrupado(lista_datos):
    datos_ordenados = sorted(lista_datos, key=lambda x: x['categoria'])
    cat_actual = None
    acumulado = 0
    print("\n" + "="*40)
    print("REPORTE GRUPAL - CORTE DE CONTROL")
    print("="*40)
    for item in datos_ordenados:
        if item['categoria'] != cat_actual:
            if cat_actual is not None:
                print(f"--- TOTAL {cat_actual}: ${acumulado:,.0f} ---")
            cat_actual = item['categoria']
            acumulado = 0
            print(f"\n[ CATEGORÍA: {cat_actual} ]")
        print(f" > {item['producto']}: ${float(item['precio']):,.0f}")
        acumulado += float(item['precio'])
    if cat_actual:
        print(f"--- TOTAL {cat_actual}: ${acumulado:,.0f} ---")
    print("="*40 + "\n")


# ============================================================
# RUN / EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    simulador_memoria()
    print("\n=== AVANCE 11: ESTRUCTURAS DINÁMICAS INICIADAS ===")
    print(f"  Pila de Acciones : LISTA LIFO activa / LIFO list active")
    print(f"  Cola de Turnos   : DEQUE FIFO activa / FIFO deque active")
    print(f"  Diccionario Colas: DICT vacío — usa /dict_colas/recargar / DICT empty — use /dict_colas/recargar")
    print(f"  API de estado    : GET /avance11/estado")
    print("=" * 50 + "\n")
    app.run(debug=True)