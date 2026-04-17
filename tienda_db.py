import sqlite3

class TiendaDB:
    def __init__(self, db_name='tienda.sqlite3'):
        self.db_name = db_name
        self.inicializar_db()

    def ejecutar_consulta(self, consulta, parametros=()):
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(consulta, parametros)
            conn.commit()
            return cursor

    def inicializar_db(self):
        """Crea todas las tablas si no existen e inserta productos por defecto."""
        with sqlite3.connect(self.db_name) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS productos (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre      TEXT    NOT NULL,
                    descripcion TEXT,
                    precio      REAL    NOT NULL,
                    stock       INTEGER NOT NULL DEFAULT 0,
                    imagen      TEXT
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre     TEXT    NOT NULL,
                    email      TEXT    UNIQUE NOT NULL,
                    contrasena TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pedidos (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_nombre  TEXT,
                    cliente_email   TEXT,
                    usuario_id      INTEGER,
                    total           REAL,
                    estado          TEXT DEFAULT 'pendiente',
                    creado_en       DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                );

                CREATE TABLE IF NOT EXISTS pedido_items (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id   INTEGER,
                    producto_id INTEGER,
                    cantidad    INTEGER,
                    precio_unit REAL,
                    FOREIGN KEY (pedido_id)   REFERENCES pedidos(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                );

                CREATE TABLE IF NOT EXISTS avisos (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo     TEXT NOT NULL,
                    mensaje    TEXT NOT NULL,
                    activo     INTEGER DEFAULT 1,
                    creado_en  DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

            # Insertar 10 productos por defecto si la tabla está vacía
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM productos")
            if cursor.fetchone()[0] == 0:
                productos_default = [
                    # (nombre, descripcion, precio, stock, imagen, costo_compra)
                    ("Anillo Stardust",      "Anillo de plata con cristal brillante",        450.00, 15, "anillo_stardust.jpg",  180.00),
                    ("Pulsera Nova Oro",     "Pulsera chapada en oro de 18k",                380.00, 10, "pulsera_nova_oro.jpg",  140.00),
                    ("Pulsera Nova Plata",   "Pulsera de plata italiana",                    280.00, 12, "pulsera_nova_plata.jpg", 95.00),
                    ("Aretes Astro Oro",     "Aretes con motivo estelar bañados en oro",     320.00,  8, "aretes_astro_oro.jpg",  110.00),
                    ("Aretes Astro Plata",   "Aretes con motivo estelar en plata 925",       220.00, 20, "aretes_astro_plata.jpg",  75.00),
                    ("Collar Luna",          "Collar delicado con dije de luna en plata",    350.00, 14, None,                   130.00),
                    ("Brazalete Infinity",   "Brazalete dorado con símbolo infinito",        410.00,  6, None,                   155.00),
                    ("Anillo Rosette",       "Anillo floral en oro rosa",                    490.00,  9, None,                   200.00),
                    ("Pendientes Celeste",   "Pendientes de perla natural con montura plata",560.00,  5, None,                   230.00),
                    ("Collar Constellation", "Collar con constelación personalizable",       620.00,  7, None,                   260.00),
                ]
                conn.executemany(
                    "INSERT INTO productos (nombre, descripcion, precio, stock, imagen, costo_compra) VALUES (?,?,?,?,?,?)",
                    productos_default
                )
                conn.commit()

        self.agregar_costo_compra()

    # ── PRODUCTOS ──────────────────────────────────────
    def obtener_productos(self):
        cursor = self.ejecutar_consulta("SELECT * FROM productos")
        return [dict(row) for row in cursor.fetchall()]

    def obtener_producto(self, producto_id):
        cursor = self.ejecutar_consulta("SELECT * FROM productos WHERE id = ?", (producto_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def agregar_producto(self, nombre, descripcion, precio, stock, imagen=None):
        self.ejecutar_consulta(
            "INSERT INTO productos (nombre, descripcion, precio, stock, imagen) VALUES (?, ?, ?, ?, ?)",
            (nombre, descripcion, precio, stock, imagen)
        )

    def editar_producto(self, producto_id, nombre, descripcion, precio, stock, imagen=None):
        if imagen:
            self.ejecutar_consulta(
                "UPDATE productos SET nombre=?, descripcion=?, precio=?, stock=?, imagen=? WHERE id=?",
                (nombre, descripcion, precio, stock, imagen, producto_id)
            )
        else:
            self.ejecutar_consulta(
                "UPDATE productos SET nombre=?, descripcion=?, precio=?, stock=? WHERE id=?",
                (nombre, descripcion, precio, stock, producto_id)
            )

    def eliminar_producto(self, producto_id):
        self.ejecutar_consulta("DELETE FROM productos WHERE id = ?", (producto_id,))

    def descontar_stock(self, producto_id, cantidad):
        self.ejecutar_consulta(
            "UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?",
            (cantidad, producto_id, cantidad)
        )

    def agregar_costo_compra(self):
        """Agrega columna costo_compra si no existe."""
        try:
            self.ejecutar_consulta("ALTER TABLE productos ADD COLUMN costo_compra REAL DEFAULT 0")
        except:
            pass  # Ya existe

    def actualizar_costo_proveedor(self, producto_id, costo):
        self.ejecutar_consulta(
            "UPDATE productos SET costo_compra=? WHERE id=?",
            (costo, producto_id)
        )

    def obtener_ganancia_hoy(self):
        cursor = self.ejecutar_consulta(
            """SELECT 
                   SUM((pi.precio_unit - COALESCE(p.costo_compra, 0)) * pi.cantidad) as ganancia
               FROM pedido_items pi
               JOIN productos p ON p.id = pi.producto_id
               JOIN pedidos ped ON ped.id = pi.pedido_id
               WHERE DATE(ped.creado_en) = DATE('now')"""
        )
        row = cursor.fetchone()
        return row['ganancia'] or 0

    # ── USUARIOS ────────────────────────────────────────
    def registrar_usuario(self, nombre, email, contrasena):
        self.ejecutar_consulta(
            "INSERT INTO usuarios (nombre, email, contrasena) VALUES (?, ?, ?)",
            (nombre, email, contrasena)
        )

    def obtener_usuario_por_email(self, email):
        cursor = self.ejecutar_consulta(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ── PEDIDOS ────────────────────────────────────────
    def obtener_pedidos(self):
        cursor = self.ejecutar_consulta(
            "SELECT * FROM pedidos ORDER BY creado_en DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def guardar_pedido(self, nombre, email, total, items, usuario_id=None):
        cursor = self.ejecutar_consulta(
            "INSERT INTO pedidos (cliente_nombre, cliente_email, total, usuario_id) VALUES (?, ?, ?, ?)",
            (nombre, email, total, usuario_id)
        )
        pedido_id = cursor.lastrowid
        for item in items:
            self.ejecutar_consulta(
                "INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unit) VALUES (?, ?, ?, ?)",
                (pedido_id, item['p']['id'], item['qty'], item['p']['precio'])
            )
            # Descontar stock automáticamente
            self.descontar_stock(item['p']['id'], item['qty'])
        return pedido_id

    def actualizar_estado_pedido(self, pedido_id, estado):
        self.ejecutar_consulta(
            "UPDATE pedidos SET estado=? WHERE id=?",
            (estado, pedido_id)
        )

    def obtener_items_pedido(self, pedido_id):
        cursor = self.ejecutar_consulta(
            """SELECT pi.cantidad, pi.precio_unit, p.nombre
               FROM pedido_items pi
               JOIN productos p ON p.id = pi.producto_id
               WHERE pi.pedido_id = ?""",
            (pedido_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def obtener_ventas_hoy(self):
        cursor = self.ejecutar_consulta(
            """SELECT p.id, p.cliente_nombre, p.cliente_email, p.total, p.estado, p.creado_en
               FROM pedidos p
               WHERE DATE(p.creado_en) = DATE('now')
               ORDER BY p.creado_en DESC"""
        )
        return [dict(row) for row in cursor.fetchall()]

    # ── AVISOS ────────────────────────────────────────
    def obtener_avisos_activos(self):
        cursor = self.ejecutar_consulta(
            "SELECT * FROM avisos WHERE activo=1 ORDER BY creado_en DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def obtener_todos_avisos(self):
        cursor = self.ejecutar_consulta(
            "SELECT * FROM avisos ORDER BY creado_en DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def agregar_aviso(self, titulo, mensaje):
        self.ejecutar_consulta(
            "INSERT INTO avisos (titulo, mensaje) VALUES (?, ?)",
            (titulo, mensaje)
        )

    def eliminar_aviso(self, aviso_id):
        self.ejecutar_consulta("DELETE FROM avisos WHERE id=?", (aviso_id,))
