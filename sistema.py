
# 1. IDENTIFICACIÓN Y CONFIGURACIÓN INICIAL
# 1. IDENTIFICACIÓN
# Estudiante: [Tu Nombre Aquí]
# Proyecto: RIVENT (Sistema de facturación e inventario)

print("-------------------------------------------------")
print(" Bienvenido al sistema de facturación RIVENT ")
print("-------------------------------------------------\n")

# 2. ENTRADA DE DATOS (INTERACTIVIDAD)
# Usamos input() para preguntar y float()/int() para convertir ese texto en números.
nombre_local = input("Ingresa el nombre del local: ")
nombre_producto = input("Ingresa el nombre del producto: ")
precio_venta = float(input("Ingresa el precio por unidad (Ej. 45000): "))
cant_vendida = int(input("Ingresa la cantidad que lleva el cliente: "))
porcentaje_Iva = 0.19   # Mantenemos el IVA fijo en 19%

# 3. OPERACIONES BÁSICAS
# Saco el subtotal multiplicando el precio por lo que compraron
subtotal = precio_venta * cant_vendida

# Calculo de cuánto es el IVA de esa compra
valor_iva = subtotal * porcentaje_Iva

# Sumo todo para saber cuánto tiene que pagar el cliente
total_pagar = subtotal + valor_iva

# 4. RESULTADOS (TICKET DE COMPRA)
# Usamos la letra 'f' antes de las comillas para poder inyectar las variables directamente con {}
print("\n=================================================")
print(f" FACTURA - {nombre_local.upper()} ")
print("=================================================")
print(f"Producto:           {nombre_producto.upper()}")
print(f"Cantidad:           {cant_vendida}")
print(f"Precio unidad:      ${precio_venta:,.0f}")
print(".................................................")
print(f"Subtotal:           ${subtotal:,.0f}")
print(f"IVA (19%):          ${valor_iva:,.0f}")
print(f"TOTAL A COBRAR:     ${total_pagar:,.0f}")
print("=================================================")
print(" ¡Gracias por su compra! ")
print("=================================================")