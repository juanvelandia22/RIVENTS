import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime # Esto nos da la fecha y hora

# ==========================================
# 1. DATOS DEL NEGOCIO (ESTO NO CAMBIA)
# ==========================================
NIT_LOCAL = "900.555.222-1"
NOMBRE_LOCAL = "POLLO Y CHARCUTERIA RAUL"
valor_iva = 0.19
numero_de_factura = 1 # Empezamos con la factura 1

# Inventario: El precio ya tiene el IVA incluido
inventario = {
    "POLLO POR KILO": {"precio": 18000, "stock": 40.0, "tipo": "Peso"},
    "CUBETA HUEVOS": {"precio": 16000, "stock": 10.0, "tipo": "Unidad"},
    "QUESO CAMPESINO": {"precio": 12000, "stock": 15.0, "tipo": "Peso"},
    "CHORIZO X UNID": {"precio": 3500, "stock": 30.0, "tipo": "Unidad"}
}

carrito_de_compras = []
suma_total_cuenta = 0

# ==========================================
# 2. FUNCIONES (LAS ACCIONES)
# ==========================================

def ir_a_pantalla(pantalla):
    # Escondemos todas
    frame_principal.pack_forget()
    frame_ventas.pack_forget()
    frame_ajustes.pack_forget()
    # Mostramos la que elegimos
    pantalla.pack(fill="both", expand=True)
    # Actualizamos las listas para que se vea lo nuevo
    actualizar_menu_productos()
    actualizar_tabla_negocio()

def sumar_al_carrito():
    global suma_total_cuenta
    
    producto_elegido = combo_elegir_prod.get()
    if producto_elegido == "":
        messagebox.showwarning("Ojo", "Selecciona un producto")
        return

    # Saber si es peso o unidad
    modo = inventario[producto_elegido]["tipo"]

    try:
        cantidad_ingresada = float(entrada_cuanto.get())
        # Si es unidad, no dejamos vender 1.5
        if modo == "Unidad" and not cantidad_ingresada.is_integer():
            messagebox.showerror("Error", "Este producto solo se vende por unidades (1, 2, 3...)")
            return
        if cantidad_ingresada <= 0:
            messagebox.showerror("Error", "La cantidad debe ser mayor a cero")
            return
    except:
        messagebox.showerror("Error", "Escribe solo números en la cantidad")
        return

    # Revisar si hay en el estante (stock)
    if inventario[producto_elegido]["stock"] >= cantidad_ingresada:
        # Restamos del inventario
        inventario[producto_elegido]["stock"] -= cantidad_ingresada
        
        # Calculamos precio
        precio_item = inventario[producto_elegido]["precio"]
        total_item = precio_item * cantidad_ingresada
        
        # Guardamos en nuestra lista de esta venta
        suma_total_cuenta += total_item
        carrito_de_compras.append([producto_elegido, cantidad_ingresada, precio_item, total_item])
        
        # Escribimos en el papel de la factura
        medida = "Kg" if modo == "Peso" else "Und"
        linea = f"{cantidad_ingresada} {medida} x {producto_elegido}\n"
        linea += f"   Valor Unit: ${precio_item:,.0f} | Sub: ${total_item:,.0f}\n"
        papel_factura.insert(tk.END, linea)
        
        entrada_cuanto.delete(0, tk.END)
    else:
        messagebox.showwarning("Agotado", "No tienes tanta mercancía en el estante")

def crear_factura_final():
    global numero_de_factura
    
    nombre_cli = entrada_nombre_cli.get()
    cedula_cli = entrada_cedula_cli.get()

    if nombre_cli == "" or cedula_cli == "" or not carrito_de_compras:
        messagebox.showwarning("Faltan datos", "Escribe los datos del cliente y agrega productos")
        return

    # Sacamos el IVA (Precio / 1.19)
    subtotal_sin_iva = suma_total_cuenta / (1 + valor_iva)
    iva_calculado = suma_total_cuenta - subtotal_sin_iva
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Limpiamos y escribimos el encabezado real
    papel_factura.delete(1.0, tk.END)
    papel_factura.insert(tk.END, f"{NOMBRE_LOCAL}\n")
    papel_factura.insert(tk.END, f"NIT: {NIT_LOCAL}\n")
    papel_factura.insert(tk.END, f"Factura No: {numero_de_factura}\n")
    papel_factura.insert(tk.END, f"Fecha: {fecha_hoy}\n")
    papel_factura.insert(tk.END, "-"*35 + "\n")
    papel_factura.insert(tk.END, f"CLIENTE: {nombre_cli.upper()}\n")
    papel_factura.insert(tk.END, f"CC/NIT:  {cedula_cli}\n")
    papel_factura.insert(tk.END, f"PAGO:    {combo_forma_pago.get()}\n")
    papel_factura.insert(tk.END, "="*35 + "\n")

    # Ponemos otra vez los productos
    for item in carrito_de_compras:
        papel_factura.insert(tk.END, f"{item[1]} x {item[0]} -> ${item[3]:,.0f}\n")

    # Totales
    papel_factura.insert(tk.END, "="*35 + "\n")
    papel_factura.insert(tk.END, f"SUBTOTAL:      ${subtotal_sin_iva:,.0f}\n")
    papel_factura.insert(tk.END, f"IVA (19%):     ${iva_calculado:,.0f}\n")
    papel_factura.insert(tk.END, f"TOTAL A PAGAR: ${suma_total_cuenta:,.0f}\n")
    papel_factura.insert(tk.END, "="*35 + "\n")
    papel_factura.insert(tk.END, " ¡GRACIAS POR SU COMPRA! ")

    numero_de_factura += 1 # La próxima factura será la siguiente
    boton_add.config(state="disabled")

def nueva_venta_limpia():
    global suma_total_cuenta, carrito_de_compras
    suma_total_cuenta = 0
    carrito_de_compras = []
    papel_factura.delete(1.0, tk.END)
    entrada_nombre_cli.delete(0, tk.END)
    entrada_cedula_cli.delete(0, tk.END)
    boton_add.config(state="normal")

# --- FUNCIONES DEL NEGOCIO ---

def actualizar_menu_productos():
    combo_elegir_prod['values'] = list(inventario.keys())

def actualizar_tabla_negocio():
    for dato in tabla_stock.get_children():
        tabla_stock.delete(dato)
    for p, d in inventario.items():
        tabla_stock.insert("", tk.END, values=(p, f"${d['precio']:,.0f}", d['stock'], d['tipo']))

def guardar_en_estante():
    n = entrada_nuevo_nombre.get().upper()
    try:
        p = float(entrada_nuevo_precio.get())
        s = float(entrada_nuevo_stock.get())
        t = combo_nuevo_tipo.get()
        inventario[n] = {"precio": p, "stock": s, "tipo": t}
        messagebox.showinfo("Listo", "Producto guardado")
        actualizar_tabla_negocio()
    except:
        messagebox.showerror("Error", "Revisa que el precio y stock sean números")

# ==========================================
# 3. LA VENTANA (EL DIBUJO)
# ==========================================
ventana = tk.Tk()
ventana.title("SISTEMA RAUL - PRINCIPIANTE")
ventana.geometry("480x800")

# --- PANTALLA MENU ---
frame_principal = tk.Frame(ventana)
tk.Label(frame_principal, text=NOMBRE_LOCAL, font=("Arial", 14, "bold")).pack(pady=50)
tk.Button(frame_principal, text="1. VENDER", bg="lightblue", width=20, height=2, command=lambda: ir_a_pantalla(frame_ventas)).pack(pady=10)
tk.Button(frame_principal, text="2. INVENTARIO", bg="lightgreen", width=20, height=2, command=lambda: ir_a_pantalla(frame_ajustes)).pack(pady=10)
tk.Button(frame_principal, text="CERRAR", command=ventana.quit).pack(pady=50)
frame_principal.pack()

# --- PANTALLA VENTAS ---
frame_ventas = tk.Frame(ventana, padx=20)
tk.Button(frame_ventas, text="<- Volver", command=lambda: ir_a_pantalla(frame_principal)).pack(anchor="w")

tk.Label(frame_ventas, text="NOMBRE CLIENTE:").pack(anchor="w")
entrada_nombre_cli = tk.Entry(frame_ventas); entrada_nombre_cli.pack(fill="x")
tk.Label(frame_ventas, text="CEDULA CLIENTE:").pack(anchor="w")
entrada_cedula_cli = tk.Entry(frame_ventas); entrada_cedula_cli.pack(fill="x")
tk.Label(frame_ventas, text="FORMA DE PAGO:").pack(anchor="w")
combo_forma_pago = ttk.Combobox(frame_ventas, values=["Efectivo", "Nequi/Daviplata", "Tarjeta"], state="readonly")
combo_forma_pago.current(0); combo_forma_pago.pack(fill="x")

tk.Label(frame_ventas, text="ELIGE EL PRODUCTO:").pack(anchor="w", pady=5)
combo_elegir_prod = ttk.Combobox(frame_ventas, state="readonly")
combo_elegir_prod.pack(fill="x")
tk.Label(frame_ventas, text="¿CUÁNTO? (Peso o Unidades):").pack(anchor="w")
entrada_cuanto = tk.Entry(frame_ventas); entrada_cuanto.pack(fill="x")

boton_add = tk.Button(frame_ventas, text="AGREGAR", bg="skyblue", command=sumar_al_carrito)
boton_add.pack(fill="x", pady=10)

papel_factura = tk.Text(frame_ventas, height=12, font=("Courier", 10), bg="white")
papel_factura.pack(fill="x")

tk.Button(frame_ventas, text="GENERAR FACTURA", bg="lightgreen", font=("Arial", 10, "bold"), command=crear_factura_final).pack(fill="x", pady=5)
tk.Button(frame_ventas, text="NUEVA VENTA", command=nueva_venta_limpia).pack()

# --- PANTALLA INVENTARIO ---
frame_ajustes = tk.Frame(ventana, padx=20)
tk.Button(frame_ajustes, text="<- Volver", command=lambda: ir_a_pantalla(frame_principal)).pack(anchor="w")

cols = ("Producto", "Precio", "Stock", "Tipo")
tabla_stock = ttk.Treeview(frame_ajustes, columns=cols, show="headings", height=8)
for c in cols: tabla_stock.heading(c, text=c); tabla_stock.column(c, width=90)
tabla_stock.pack(fill="x", pady=10)

tk.Label(frame_ajustes, text="Nombre:").pack(anchor="w")
entrada_nuevo_nombre = tk.Entry(frame_ajustes); entrada_nuevo_nombre.pack(fill="x")
tk.Label(frame_ajustes, text="Precio con IVA:").pack(anchor="w")
entrada_nuevo_precio = tk.Entry(frame_ajustes); entrada_nuevo_precio.pack(fill="x")
tk.Label(frame_ajustes, text="Stock Actual:").pack(anchor="w")
entrada_nuevo_stock = tk.Entry(frame_ajustes); entrada_nuevo_stock.pack(fill="x")
tk.Label(frame_ajustes, text="Se vende por:").pack(anchor="w")
combo_nuevo_tipo = ttk.Combobox(frame_ajustes, values=["Peso", "Unidad"], state="readonly")
combo_nuevo_tipo.current(0); combo_nuevo_tipo.pack(fill="x")

tk.Button(frame_ajustes, text="GUARDAR CAMBIOS", bg="orange", command=guardar_en_estante).pack(fill="x", pady=20)

ventana.mainloop()