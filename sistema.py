import tkinter as tk
from tkinter import messagebox

# 1. DATOS E INVENTARIO INICIAL
nombre_local = "POLLO Y CHARCUTERIA RAUL"
porcentaje_iva = 0.19

inventario = {
    "SALCHICHAS ZENU": {"precio": 45000.0, "stock": 10},
    "QUESO MOZZARELLA": {"precio": 12000.0, "stock": 5},
    "JAMON AHUMADO": {"precio": 20000.0, "stock": 15}
}

carrito = []
subtotal_compra = 0

# 2. FUNCIONES DE LOS BOTONES
def agregar_al_carrito():
    global subtotal_compra # Usamos la variable global para ir sumando
    
    producto = var_producto.get()
    
    # Intentamos convertir la cantidad a número
    try:
        cantidad = int(entrada_cantidad.get())
    except ValueError:
        messagebox.showerror("Error", "La cantidad debe ser un número entero.")
        return

    if cantidad <= 0:
        messagebox.showerror("Error", "La cantidad debe ser mayor a 0.")
        return
        
    # Verificamos stock
    if cantidad <= inventario[producto]["stock"]:
        # Descontamos stock y calculamos
        inventario[producto]["stock"] -= cantidad
        costo = inventario[producto]["precio"] * cantidad
        subtotal_compra += costo
        carrito.append((producto, cantidad, costo))
        
        # Mostramos en el recibo de la pantalla
        pantalla_recibo.insert(tk.END, f" + {cantidad}x {producto} : ${costo:,.0f}\n")
        
        # Limpiamos la caja de cantidad
        entrada_cantidad.delete(0, tk.END)
    else:
        messagebox.showwarning("Stock", f"Solo quedan {inventario[producto]['stock']} unidades.")

def generar_factura():
    cedula = entrada_cedula.get()
    
    if not cedula:
        messagebox.showwarning("Faltan Datos", "Por favor ingresa la cédula del cliente.")
        return
    if not carrito:
        messagebox.showwarning("Carrito Vacío", "No has agregado ningún producto a la cuenta.")
        return
        
    iva = subtotal_compra * porcentaje_iva
    total = subtotal_compra + iva
    
    # Imprimimos los totales en la pantalla
    pantalla_recibo.insert(tk.END, "\n================================\n")
    pantalla_recibo.insert(tk.END, f"Cédula Cliente: {cedula}\n")
    pantalla_recibo.insert(tk.END, "................................\n")
    pantalla_recibo.insert(tk.END, f"Subtotal:       ${subtotal_compra:,.0f}\n")
    pantalla_recibo.insert(tk.END, f"IVA (19%):      ${iva:,.0f}\n")
    pantalla_recibo.insert(tk.END, f"TOTAL A PAGAR:  ${total:,.0f}\n")
    pantalla_recibo.insert(tk.END, "================================\n")
    pantalla_recibo.insert(tk.END, "      ¡GRACIAS POR SU COMPRA!   \n")
    
    # Desactivamos los botones para terminar la venta
    boton_agregar.config(state=tk.DISABLED)
    boton_facturar.config(state=tk.DISABLED)

# 3. CREACIÓN DE LA VENTANA (INTERFAZ)
ventana = tk.Tk()
ventana.title(f"RIVENT - {nombre_local}")
ventana.geometry("400x600") # Ancho x Alto
ventana.config(padx=20, pady=20)

# --- Elementos visuales (Widgets) ---

# Título
tk.Label(ventana, text="SISTEMA DE FACTURACIÓN", font=("Arial", 14, "bold")).pack(pady=5)

# Cédula
tk.Label(ventana, text="Cédula del Cliente:").pack(anchor="w")
entrada_cedula = tk.Entry(ventana, width=20)
entrada_cedula.pack(anchor="w", pady=5)

# Selección de Producto (Menú desplegable)
tk.Label(ventana, text="Seleccione el Producto:").pack(anchor="w")
opciones_productos = list(inventario.keys())
var_producto = tk.StringVar(ventana)
var_producto.set(opciones_productos[0]) # Valor por defecto
menu_productos = tk.OptionMenu(ventana, var_producto, *opciones_productos)
menu_productos.pack(anchor="w", fill="x", pady=5)

# Cantidad
tk.Label(ventana, text="Cantidad:").pack(anchor="w")
entrada_cantidad = tk.Entry(ventana, width=10)
entrada_cantidad.pack(anchor="w", pady=5)

# Botón Agregar
boton_agregar = tk.Button(ventana, text="Agregar al Carrito", bg="lightblue", command=agregar_al_carrito)
boton_agregar.pack(fill="x", pady=10)

# Pantalla del recibo (Caja de texto grande)
tk.Label(ventana, text="Detalle de la cuenta:").pack(anchor="w")
pantalla_recibo = tk.Text(ventana, height=12, width=40)
pantalla_recibo.pack(pady=5)

# Botón Pagar
boton_facturar = tk.Button(ventana, text="PAGAR Y GENERAR FACTURA", bg="lightgreen", font=("Arial", 10, "bold"), command=generar_factura)
boton_facturar.pack(fill="x", pady=10)

# 4. INICIAR EL PROGRAMA
ventana.mainloop()