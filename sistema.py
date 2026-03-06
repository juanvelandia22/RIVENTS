
import tkinter as tk
from tkinter import messagebox, ttk

# ==========================================
# 1. DATOS E INVENTARIO (IVA 19% INCLUIDO)
# ==========================================
nombre_local = "POLLO Y CHARCUTERIA RAUL"
porcentaje_iva = 0.19

# Los precios aquí son el valor FINAL que paga el cliente
inventario = {
    "SALCHICHAS ZENU": {"precio": 45000, "stock": 10},
    "QUESO MOZZARELLA": {"precio": 12000, "stock": 5},
    "JAMON AHUMADO": {"precio": 20000, "stock": 15}
}

carrito = []
total_operacion = 0

# ==========================================
# 2. LÓGICA DE NAVEGACIÓN
# ==========================================
def abrir_modulo(frame):
    """Simula la entrada a un módulo del ciclo"""
    frame_menu.pack_forget()
    frame_facturacion.pack_forget()
    frame_inventario.pack_forget()
    frame.pack(fill="both", expand=True)
    
    if frame == frame_facturacion:
        actualizar_opciones_productos()
    elif frame == frame_inventario:
        refrescar_tabla_inventario()

# ==========================================
# 3. MÓDULO: TOMA DE PEDIDOS Y FACTURACIÓN
# ==========================================
def agregar_item():
    global total_operacion
    prod_seleccionado = combo_productos.get()
    
    try:
        cantidad = int(entrada_cantidad.get())
        if cantidad <= 0: raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Ingrese una cantidad válida.")
        return

    if prod_seleccionado in inventario:
        if inventario[prod_seleccionado]["stock"] >= cantidad:
            # Lógica de IVA incluido
            precio_unitario = inventario[prod_seleccionado]["precio"]
            subtotal_item = precio_unitario * cantidad
            
            inventario[prod_seleccionado]["stock"] -= cantidad
            total_operacion += subtotal_item
            carrito.append((prod_seleccionado, cantidad, precio_unitario, subtotal_item))
            
            # Formato solicitado: Cantidad x Producto (Unitario con IVA) = Total
            pantalla_factura.insert(tk.END, f" {cantidad}x {prod_seleccionado}\n")
            pantalla_factura.insert(tk.END, f"   Unit: ${precio_unitario:,.0f} | Sub: ${subtotal_item:,.0f}\n")
            pantalla_factura.insert(tk.END, "-"*30 + "\n")
            
            entrada_cantidad.delete(0, tk.END)
        else:
            messagebox.showwarning("Sin Stock", "No hay suficiente mercancía.")

def finalizar_factura():
    if not carrito: return
    
    # Desglose de IVA (El precio ya lo incluía, así que lo extraemos)
    # Formula: Base = Total / (1 + IVA)
    base_gravable = total_operacion / (1 + porcentaje_iva)
    valor_iva = total_operacion - base_gravable
    
    pantalla_factura.insert(tk.END, "\n" + "="*30 + "\n")
    pantalla_factura.insert(tk.END, f" TOTAL NETO:   ${total_operacion:,.0f}\n")
    pantalla_factura.insert(tk.END, f" (Base: ${base_gravable:,.0f} | IVA 19%: ${valor_iva:,.0f})\n")
    pantalla_factura.insert(tk.END, "="*30 + "\n")
    
    btn_add.config(state="disabled")
    btn_pay.config(state="disabled")

def limpiar_pantalla_venta():
    global total_operacion, carrito
    total_operacion = 0
    carrito = []
    pantalla_factura.delete(1.0, tk.END)
    btn_add.config(state="normal")
    btn_pay.config(state="normal")

def actualizar_opciones_productos():
    combo_productos['values'] = list(inventario.keys())

# ==========================================
# 4. MÓDULO: INTERACCIÓN CON EL NEGOCIO
# ==========================================
def refrescar_tabla_inventario():
    for i in tabla.get_children(): tabla.delete(i)
    for p, d in inventario.items():
        tabla.insert("", tk.END, values=(p, f"${d['precio']:,.0f}", d['stock']))

def modificar_inventario():
    nom = ent_inv_nom.get().upper().strip()
    try:
        pre = float(ent_inv_pre.get())
        can = int(ent_inv_can.get())
    except:
        messagebox.showerror("Error", "Datos numéricos incorrectos.")
        return

    if nom:
        inventario[nom] = {"precio": pre, "stock": can}
        messagebox.showinfo("Éxito", "Inventario actualizado.")
        ent_inv_nom.delete(0, tk.END); ent_inv_pre.delete(0, tk.END); ent_inv_can.delete(0, tk.END)
        refrescar_tabla_inventario()

# ==========================================
# 5. VENTANA PRINCIPAL Y DISEÑO
# ==========================================
root = tk.Tk()
root.title(f"SISTEMA {nombre_local}")
root.geometry("480x700")

# --- MENÚ PRINCIPAL ---
frame_menu = tk.Frame(root, pady=50)
tk.Label(frame_menu, text=nombre_local, font=("Arial", 14, "bold")).pack(pady=20)
tk.Button(frame_menu, text="1. TOMA DE PEDIDO", width=25, height=2, bg="#D5F5E3", command=lambda: abrir_modulo(frame_facturacion)).pack(pady=10)
tk.Button(frame_menu, text="2. INTERACTUAR CON NEGOCIO", width=25, height=2, bg="#D6EAF8", command=lambda: abrir_modulo(frame_inventario)).pack(pady=10)
tk.Button(frame_menu, text="3. SALIR", width=10, command=root.quit).pack(pady=50)
frame_menu.pack()

# --- INTERFAZ DE FACTURACIÓN ---
frame_facturacion = tk.Frame(root, padx=20)
tk.Button(frame_facturacion, text="Volver al Menú", command=lambda: abrir_modulo(frame_menu)).pack(anchor="w", pady=5)
tk.Label(frame_facturacion, text="PRODUCTO:").pack(anchor="w")
combo_productos = ttk.Combobox(frame_facturacion, state="readonly")
combo_productos.pack(fill="x", pady=5)
tk.Label(frame_facturacion, text="CANTIDAD:").pack(anchor="w")
entrada_cantidad = tk.Entry(frame_facturacion)
entrada_cantidad.pack(fill="x", pady=5)
btn_add = tk.Button(frame_facturacion, text="Agregar", bg="lightblue", command=agregar_item)
btn_add.pack(fill="x", pady=5)
pantalla_factura = tk.Text(frame_facturacion, height=15, font=("Courier", 9))
pantalla_factura.pack(fill="x", pady=5)
btn_pay = tk.Button(frame_facturacion, text="FACTURAR", bg="lightgreen", command=finalizar_factura)
btn_pay.pack(fill="x", pady=2)
tk.Button(frame_facturacion, text="NUEVA VENTA", command=limpiar_pantalla_venta).pack(fill="x", pady=2)

# --- INTERFAZ DE NEGOCIO ---
frame_inventario = tk.Frame(root, padx=20)
tk.Button(frame_inventario, text="Volver al Menú", command=lambda: abrir_modulo(frame_menu)).pack(anchor="w", pady=5)
cols = ("Prod", "Precio (IVA inc)", "Stock")
tabla = ttk.Treeview(frame_inventario, columns=cols, show="headings", height=8)
for c in cols: tabla.heading(c, text=c); tabla.column(c, width=100)
tabla.pack(fill="x", pady=10)
tk.Label(frame_inventario, text="Producto:").pack(anchor="w")
ent_inv_nom = tk.Entry(frame_inventario); ent_inv_nom.pack(fill="x")
tk.Label(frame_inventario, text="Precio con IVA:").pack(anchor="w")
ent_inv_pre = tk.Entry(frame_inventario); ent_inv_pre.pack(fill="x")
tk.Label(frame_inventario, text="Stock:").pack(anchor="w")
ent_inv_can = tk.Entry(frame_inventario); ent_inv_can.pack(fill="x")
tk.Button(frame_inventario, text="GUARDAR CAMBIOS", bg="orange", command=modificar_inventario).pack(fill="x", pady=20)

root.mainloop()