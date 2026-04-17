# Camila Domínguez Joyería — CRM E-Commerce

Sistema de gestión de ventas desarrollado con Python, Flask, SQLite, SCSS y Gulp.

## Requisitos
- Python 3.x
- Node.js

## Instalación

### 1. Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### 2. Instalar dependencias Node.js
```bash
npm install
```

### 3. Compilar SCSS
```bash
npm run build
```
O para modo desarrollo (vigila cambios automáticamente):
```bash
npx gulp
```

### 4. Correr la app
```bash
python app.py
```

Abre tu navegador en: http://localhost:5000

## Credenciales Admin
- Usuario: `camila`
- Contraseña: `joyeria2026`

## Funcionalidades
- Catálogo con 10 productos por defecto
- Registro e inicio de sesión de clientes
- Carrito de compras con verificación de pedido
- Descuento automático de stock al confirmar pedido
- Panel administrador: agregar, editar, eliminar productos
- Gestión de pedidos con estados (pendiente, enviado, entregado, cancelado)
- Avisos al cliente desde el admin
- Reporte de ventas diarias con opción de impresión
