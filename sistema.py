import tkinter as tk
from tkinter import messagebox, ttk

# ==========================================
# 1. BASE DE DATOS (CON TIPO DE MEDIDA)
# ==========================================
# Agregamos "medida" para saber si es Unidad o Kilo
inventario = {
    "POLLO ENTERO": {"precio": 18000.0, "stock": 50.0, "medida": "Peso"},
    "CUBETA DE HUEVOS": {"precio": 15000.0, "stock": 20.0, "medida": "Unidad"},
    "QUESO MOZZARELLA": {"precio": 22000.0, "stock": 15.0, "medida": "Peso"}
}

lista_carrito = []
total_a_pagar = 0

# ==========================================
# 2. FUNCIONES LÓGICAS
# ==========================================

def cambiar_pantalla(pantalla_nueva):
    frame_menu.pack_forget()
    frame_factura.pack_forget()
    frame_negocio.pack_forget()
    pantalla_nueva.pack(fill="both", expand=True)
    actualizar_lista_desplegable()
    actualizar_tabla_inventario()

def agregar_producto():
    global total_a_pagar
    producto_nom = combo_productos.get()
    tipo_medida = inventario[producto_nom]["medida"]
    
    try:
        valor_entrada = float(entrada_cantidad.get())
        
        # Validar si es Unidad, no permitir decimales (ej. 1.5 huevos no se puede)
        if tipo_medida == "Unidad" and not valor_entrada.is_integer():
            messagebox.showwarning("Atención", "Este producto se vende por unidades enteras.")
            return
        if valor_entrada <= 0:
            raise ValueError
    except:
        messagebox.showerror("Error", "Ingrese un número válido en cantidad/peso.")
        return

    # Verificar disponibilidad
    if inventario[producto_nom]["stock"] >= valor_entrada:
        inventario[producto_nom]["stock"] -= valor_entrada
        
        precio_unitario = inventario[producto_nom]["precio"]
        subtotal = precio_unitario * valor_entrada
        total_a_pagar += subtotal
        
        lista_carrito.append((producto_nom, valor_entrada, subtotal))
        
        # Mostrar en recibo con su etiqueta (Kg o Und)
        etiqueta = "Kg" if tipo_medida == "Peso" else "Und"
        texto = f"• {valor_entrada} {etiqueta} de {producto_nom}\n"
        texto += f"  Precio: ${precio_unitario:,.0f} | Subtotal: ${subtotal:,.0f}\n"
        texto += "-"*40 + "\n"
        pantalla_texto.insert(tk.END, texto)
        
        entrada_cantidad.delete(0, tk.END)
    else:
        messagebox.showwarning("Sin Stock", "No hay suficiente cantidad disponible.")

def finalizar_venta():
    if not lista_carrito: return
    # IVA Incluido: Extraemos el 19% del total
    base = total_a_pagar / 1.19
    iva = total_a_pagar - base
    
    pantalla_texto.insert(tk.END, f"\n{'='*30}\n")
    pantalla_texto.insert(tk.END, f"SUBTOTAL (Sin IVA): ${base:,.0f}\n")
    pantalla_texto.insert(tk.END, f"IVA (19%):          ${iva:,.0f}\n")
    pantalla_texto.insert(tk.END, f"TOTAL A PAGAR:      ${total_a_pagar:,.0f}\n")
    pantalla_texto.insert(tk.END, f"{'='*30}\n")
    
    btn_sumar.config(state="disabled")
    btn_pagar.config(state="disabled")

def guardar_en_inventario():
    nom = entry_nom_inv.get().upper()
    medida = combo_medida_inv.get()
    try:
        pre = float(entry_pre_inv.get())
        sto = float(entry_sto_inv.get())
        
        inventario[nom] = {"precio": pre, "stock": sto, "medida": medida}
        messagebox.showinfo("Éxito", f"{nom} guardado como {medida}")
        
        # Limpiar
        entry_nom_inv.delete(0, tk.END)
        entry_pre_inv.delete(0, tk.END)
        entry_sto_inv.delete(0, tk.END)
        actualizar_tabla_inventario()
    except:
        messagebox.showerror("Error", "Llene los campos de precio y stock con números.")

# --- ACTUALIZADORES ---
def actualizar_lista_desplegable():
    combo_productos['values'] = list(inventario.keys())

def actualizar_tabla_inventario():
    for f in tabla_inv.get_children(): tabla_inv.delete(f)
    for p, d in inventario.items():
        tabla_inv.insert("", tk.END, values=(p, f"${d['precio']:,.0f}", d['stock'], d['medida']))

# ==========================================
# 3. INTERFAZ GRÁFICA (Paso a Paso)
# ==========================================
root = tk.Tk()
root.title("RIVENTS - Pollo y Charcutería")
root.geometry("480x750")

# PANTALLA: MENÚ
frame_menu = tk.Frame(root)
tk.Label(frame_menu, text="SISTEMA DE VENTAS RAUL", font=("Arial", 14, "bold")).pack(pady=40)
tk.Button(frame_menu, text="🛒 NUEVA VENTA", bg="#AED6F1", width=25, height=2, command=lambda: cambiar_pantalla(frame_factura)).pack(pady=10)
tk.Button(frame_menu, text="📦 GESTIÓN DE NEGOCIO", bg="#ABEBC6", width=25, height=2, command=lambda: cambiar_pantalla(frame_negocio)).pack(pady=10)
tk.Button(frame_menu, text="SALIR", command=root.quit).pack(pady=40)
frame_menu.pack()

# PANTALLA: FACTURACIÓN
frame_factura = tk.Frame(root, padx=20)
tk.Button(frame_factura, text="<- Volver", command=lambda: cambiar_pantalla(frame_menu)).pack(anchor="w", pady=5)
tk.Label(frame_factura, text="PRODUCTO:").pack(anchor="w")
combo_productos = ttk.Combobox(frame_factura, state="readonly", font=("Arial", 11))
combo_productos.pack(fill="x", pady=5)
tk.Label(frame_factura, text="CANTIDAD / PESO:").pack(anchor="w")
entrada_cantidad = tk.Entry(frame_factura, font=("Arial", 12))
entrada_cantidad.pack(fill="x", pady=5)
btn_sumar = tk.Button(frame_factura, text="AGREGAR", bg="#5DADE2", fg="white", command=agregar_producto)
btn_sumar.pack(fill="x", pady=10)
pantalla_texto = tk.Text(frame_factura, height=15, font=("Courier", 10))
pantalla_texto.pack(fill="x")
btn_pagar = tk.Button(frame_factura, text="COBRAR FACTURA", bg="#52BE80", fg="white", font=("Arial", 12, "bold"), command=finalizar_venta)
btn_pagar.pack(fill="x", pady=5)
tk.Button(frame_factura, text="Limpiar", command=lambda: [pantalla_texto.delete(1.0, tk.END), btn_sumar.config(state="normal"), btn_pagar.config(state="normal")]).pack()

# PANTALLA: NEGOCIO
frame_negocio = tk.Frame(root, padx=20)
tk.Button(frame_negocio, text="<- Volver", command=lambda: cambiar_pantalla(frame_menu)).pack(anchor="w", pady=5)
# Tabla
cols = ("Prod", "Precio", "Stock", "Medida")
tabla_inv = ttk.Treeview(frame_negocio, columns=cols, show="headings", height=6)
for c in cols: tabla_inv.heading(c, text=c); tabla_inv.column(c, width=100)
tabla_inv.pack(fill="x", pady=10)
# Entradas
tk.Label(frame_negocio, text="Nombre:").pack(anchor="w")
entry_nom_inv = tk.Entry(frame_negocio); entry_nom_inv.pack(fill="x")
tk.Label(frame_negocio, text="Precio (IVA Inc):").pack(anchor="w")
entry_pre_inv = tk.Entry(frame_negocio); entry_pre_inv.pack(fill="x")
tk.Label(frame_negocio, text="Stock inicial:").pack(anchor="w")
entry_sto_inv = tk.Entry(frame_negocio); entry_sto_inv.pack(fill="x")
tk.Label(frame_negocio, text="Se vende por:").pack(anchor="w")
combo_medida_inv = ttk.Combobox(frame_negocio, values=["Peso", "Unidad"], state="readonly")
combo_medida_inv.current(0); combo_medida_inv.pack(fill="x", pady=5)
tk.Button(frame_negocio, text="GUARDAR CAMBIOS", bg="#F4D03F", font=("Arial", 10, "bold"), command=guardar_en_inventario).pack(fill="x", pady=20)

root.mainloop()