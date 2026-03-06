# 1. IDENTIFICACIÓN
# Estudiante: [Tu Nombre Aquí]
# Proyecto: RIVENT (Sistema de facturación e inventario)
# 2. VARIABLES INICIALES
nombre_local = "POLLO Y CHARCUTERIA RAUL"
nombre_producto = "SALCHICHAS ZENU"
precio_venta = 45000.0  # float
cant_vendida = 3        # int
porcentaje_Iva = 0.19   # float
# 3. OPERACIONES BÁSICAS
# Saco el subtotal multiplicando el precio por lo que compraron
subtotal = precio_venta * cant_vendida
# Calculo de cuánto es el IVA de esa compra
valor_iva = subtotal * porcentaje_Iva
# Sumo todo para saber cuánto tiene que pagar el cliente
total_pagar = subtotal + valor_iva
# 4. SALUDO Y RESULTADOS
print("-------------------------------------------------")
print(" Bienvenido al sistema de facturación RIVENT ")
print(" Local:", nombre_local)
print("-------------------------------------------------")
print("Producto:", nombre_producto)
print("Cantidad que lleva:", cant_vendida)
print("Precio unidad: $", precio_venta)
print(".................................................")
print("Subtotal: $", subtotal)
print("IVA (19%): $", valor_iva)
print("TOTAL A COBRAR: $", total_pagar)
print("-------------------------------------------------")



