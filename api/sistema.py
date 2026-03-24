from flask import Flask, render_template_string, request, redirect, session, send_file, url_for
from supabase import create_client, Client
from datetime import datetime
import os
from fpdf import FPDF
import io

app = Flask(__name__)
app.secret_key = 'pollo_raul_secret_key'

# === CONFIGURACIÓN LEGAL ===
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
NIT_NEGOCIO = "123.456.789-0"
DIRECCION = "Cúcuta, Norte de Santander"
TELEFONO = "300 000 0000"
VALOR_IVA = 0.19

# === CONEXIÓN A SUPABASE ===# Ahora Python leerá las llaves que acabas de guardar en Vercel
URL_SUPABASE = os.environ.get("SUPABASE_URL")
KEY_SUPABASE = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

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
            <h2>📦 Inventario</h2>
            <form action="/inventario/guardar" method="POST">
                <div style="display:flex; gap:10px;">
                    <input type="number" name="codigo" placeholder="Cód" required>
                    <input type="text" name="producto" placeholder="Producto" required>
                </div>
                <div style="display:flex; gap:10px;">
                    <input type="number" step="0.01" name="precio" placeholder="Precio" required>
                    <input type="number" step="0.01" name="stock" placeholder="Stock" required>
                    <select name="tipo">
                        <option value="Kilo">Kilo</option>
                        <option value="Und">Unidad</option>
                    </select>
                </div>
                <button type="submit" class="btn-success">Guardar Producto</button>
            </form>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead><tr><th>Cód</th><th>Producto</th><th>Precio</th><th>Stock</th><th>Tipo</th><th>Acción</th></tr></thead>
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
            <h2>🛒 Venta Rápida</h2>
            <form action="/carrito/agregar" method="POST">
                <div style="display:flex; gap:10px;">
                    <input type="number" name="codigo_vta" placeholder="Código..." required autofocus>
                    <input type="number" step="0.01" name="cantidad" placeholder="Cant." required style="width:100px;">
                    <button type="submit" style="width:120px;">Añadir</button>
                </div>
            </form>
            <hr>
            <h3>👤 Datos Cliente</h3>
            <form action="/cliente/actualizar" method="POST">
                <input type="text" name="nombre" placeholder="Nombre" value="{{ cliente.nombre }}">
                <input type="text" name="documento" placeholder="Cédula/NIT" value="{{ cliente.documento }}">
                <button type="submit" style="background:#95a5a6">Actualizar</button>
            </form>
            <div class="total-display">TOTAL: ${{ "{:,.0f}".format(total_venta) }}</div>
            {% if carrito %}
                {% for item in carrito %}
                <p style="font-size:13px; margin:5px 0;">• {{ item.nombre }} ({{ item.cantidad }} {{ item.tipo }}) - ${{ "{:,.0f}".format(item.total) }}</p>
                {% endfor %}
                <a href="/venta/finalizar"><button class="btn-success">FINALIZAR Y FACTURAR PDF</button></a>
                <a href="/carrito/limpiar"><button style="background:#e74c3c; margin-top:5px;">VACIAR</button></a>
            {% endif %}
        </div>

        <div class="card full-width">
            <h2>📊 Historial y Buscador</h2>
            <form action="/" method="GET" style="display:flex; gap:10px; margin-bottom:15px;">
                <input type="text" name="buscar" placeholder="Cédula o Nombre..." value="{{ busqueda }}">
                <button type="submit" style="width:120px;">🔍 Buscar</button>
            </form>
            <table>
                <thead><tr><th>No.</th><th>Fecha</th><th>Cliente</th><th>Cédula</th><th>Total</th><th>Opciones</th></tr></thead>
                <tbody>
                    {% for f in historial %}
                    <tr>
                        <td>#{{ f.id }}</td>
                        <td>{{ f.fecha[:16] }}</td>
                        <td>{{ f.cliente_nombre }}</td>
                        <td>{{ f.cliente_documento }}</td>
                        <td><b>${{ "{:,.0f}".format(f.total) }}</b></td>
                        <td><a href="/factura/pdf/{{ f.id }}" target="_blank">🖨️ Descargar / Imprimir</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    if 'carrito' not in session: session['carrito'] = []
    if 'cliente' not in session: session['cliente'] = {"nombre": "Consumidor Final", "documento": "222222222222"}
    buscar = request.args.get('buscar', '')
    
    # Traer inventario ordenado
    inv_res = supabase.table("inventario").select("*").order("codigo").execute()
    inv = inv_res.data if inv_res.data else []
    
    # Buscador en historial
    if buscar:
        his_res = supabase.table("facturas").select("*")\
            .or_(f"cliente_documento.ilike.%{buscar}%,cliente_nombre.ilike.%{buscar}%")\
            .order("fecha", desc=True).execute()
    else:
        his_res = supabase.table("facturas").select("*").order("fecha", desc=True).limit(10).execute()
    
    his = his_res.data if his_res.data else []
        
    total = sum(item['total'] for item in session['carrito'])
    return render_template_string(HTML_SISTEMA, nombre=NOMBRE_LOCAL, nit=NIT_NEGOCIO, direccion=DIRECCION, 
                                   inventario=inv, carrito=session['carrito'], total_venta=total, 
                                   cliente=session['cliente'], historial=his, busqueda=buscar)

@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    try:
        c = request.form
        datos = {
            "codigo": int(c['codigo']),
            "producto": c['producto'].upper(),
            "precio": float(c['precio']),
            "stock": float(c['stock']),
            "tipo": c['tipo'],
            "fecha_registro": datetime.now().strftime('%Y-%m-%d')
        }
        supabase.table("inventario").upsert(datos).execute()
        return redirect("/")
    except Exception as e:
        return f"Error al guardar: {str(e)}"

@app.route("/inventario/eliminar/<int:codigo>")
def inv_eliminar(codigo):
    supabase.table("inventario").delete().eq("codigo", codigo).execute()
    return redirect("/")

@app.route("/carrito/agregar", methods=["POST"])
def car_agregar():
    cod = request.form.get("codigo_vta")
    try:
        cant = float(request.form.get("cantidad", 0))
        if cant <= 0: return redirect("/")
    except: return redirect("/")

    res = supabase.table("inventario").select("*").eq("codigo", cod).execute()
    p = res.data[0] if res.data else None

    if not p or float(p['stock']) < cant:
        return redirect("/")

    carrito = session.get('carrito', [])
    carrito.append({
        "codigo": cod,
        "nombre": p['producto'],
        "cantidad": cant,
        "total": round(float(p['precio']) * cant, 2),
        "tipo": p['tipo']
    })
    session['carrito'] = carrito
    return redirect("/")

@app.route("/cliente/actualizar", methods=["POST"])
def cli_upd():
    session['cliente'] = {"nombre": request.form.get("nombre"), "documento": request.form.get("documento")}
    return redirect("/")

@app.route("/venta/finalizar")
def finalizar():
    carrito = session.get('carrito', [])
    if not carrito: return redirect("/")
    
    total = sum(item['total'] for item in carrito)
    sub = total / (1 + VALOR_IVA)
    iva = total - sub
    cliente = session.get('cliente')
    detalles = "|".join([f"{i['nombre']},{i['cantidad']},{i['total']}" for i in carrito])
    
    factura_data = {
        "subtotal": float(sub), "iva": float(iva), "total": float(total),
        "cliente_nombre": cliente['nombre'], 
        "cliente_documento": cliente['documento'], 
        "detalles_json": detalles
    }
    
    # Guardar factura y obtener el ID generado
    res = supabase.table("facturas").insert(factura_data).execute()
    factura_id = res.data[0]['id']
    
    # Descontar stock
    for item in carrito:
        prod_res = supabase.table("inventario").select("stock").eq("codigo", item['codigo']).single().execute()
        nuevo_stock = float(prod_res.data['stock']) - float(item['cantidad'])
        supabase.table("inventario").update({"stock": nuevo_stock}).eq("codigo", item['codigo']).execute()
        
    session['carrito'] = []
    return redirect(url_for('generar_pdf', id_factura=factura_id))

@app.route("/factura/pdf/<int:id_factura>")
def generar_pdf(id_factura):
    res = supabase.table("facturas").select("*").eq("id", id_factura).execute()
    f = res.data[0] if res.data else None

    if not f: return "Factura no encontrada", 404

    pdf = FPDF(unit='mm', format=(80, 200))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=5)
    pdf.set_margins(5, 5, 5)

    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(70, 6, NOMBRE_LOCAL, 0, "C")
    pdf.set_font("Arial", "", 8)
    pdf.cell(70, 4, f"NIT: {NIT_NEGOCIO}", ln=True, align="C")
    pdf.multi_cell(70, 4, DIRECCION, 0, "C")
    pdf.cell(70, 4, f"Tel: {TELEFONO}", ln=True, align="C")
    pdf.ln(2)
    pdf.cell(70, 2, "-"*40, ln=True, align="C")
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(70, 5, f"FACTURA No. {f['id']}", ln=True, align="C")
    pdf.set_font("Arial", "", 8)
    pdf.cell(70, 4, f"Fecha: {f['fecha'][:16]}", ln=True)
    pdf.multi_cell(70, 4, f"Cliente: {f['cliente_nombre']}")
    pdf.cell(70, 4, f"CC/NIT: {f['cliente_documento']}", ln=True)
    pdf.cell(70, 2, "-"*40, ln=True, align="C")

    pdf.set_font("Arial", "B", 8)
    pdf.cell(35, 5, "Producto")
    pdf.cell(10, 5, "Cant", 0, 0, "C")
    pdf.cell(25, 5, "Total", 0, 1, "R")
    pdf.set_font("Arial", "", 8)

    if f['detalles_json']:
        items = f['detalles_json'].split("|")
        for item in items:
            try:
                nom, cant, tot = item.split(",")
                if len(nom) > 18: nom = nom[:18] + "..."
                pdf.cell(35, 4, nom)
                pdf.cell(10, 4, f"{float(cant):.2f}", 0, 0, "C")
                pdf.cell(25, 4, f"${float(tot):,.0f}", 0, 1, "R")
            except: continue

    pdf.cell(70, 2, "-"*40, ln=True, align="C")
    pdf.cell(40, 5, "SUBTOTAL:", 0, 0, "R")
    pdf.cell(30, 5, f"${float(f['subtotal']):,.0f}", 0, 1, "R")
    pdf.cell(40, 5, f"IVA ({int(VALOR_IVA*100)}%):", 0, 0, "R")
    pdf.cell(30, 5, f"${float(f['iva']):,.0f}", 0, 1, "R")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 8, "TOTAL:", 0, 0, "R")
    pdf.cell(30, 8, f"${float(f['total']):,.0f}", 0, 1, "R")
    pdf.ln(5)
    pdf.set_font("Arial", "I", 7)
    pdf.multi_cell(70, 4, "Gracias por su compra. Vuelva pronto!", 0, "C")

    output = io.BytesIO()
    pdf_out = pdf.output(dest='S').encode('latin1')
    output.write(pdf_out)
    output.seek(0)

    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name=f"Factura_{id_factura}.pdf")

@app.route("/carrito/limpiar")
def car_limpiar():
    session['carrito'] = []
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)