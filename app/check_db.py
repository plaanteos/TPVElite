from database import DatabaseManager
db = DatabaseManager()
tablas = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
print('Tablas:', [t['name'] for t in tablas])
cols_dp = [c['name'] for c in db.fetch_all("PRAGMA table_info(detalles_pedido)")]
cols_p  = [c['name'] for c in db.fetch_all("PRAGMA table_info(pedidos)")]
cols_mi = [c['name'] for c in db.fetch_all("PRAGMA table_info(movimientos_inventario)")]
print('detalles_pedido:', cols_dp)
print('pedidos:', cols_p)
print('movimientos_inventario:', cols_mi)
print('Schema OK')
