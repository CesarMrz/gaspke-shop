# GaspKe Shop Panel con Base de Datos

Panel de tienda de streaming con **backend Flask + SQLite**.

## Cómo ejecutar

```bash
cd gaspke-panel/backend
chmod +x start.sh
./start.sh
```

O manualmente:

```bash
cd gaspke-panel/backend
pip3 install -r requirements.txt
python3 app.py
```

Luego abre en el navegador: **http://localhost:5000**

## Qué incluye

- Base de datos SQLite (`gaspke.db`) con tablas:
  - `platforms` (precios y stock)
  - `accounts` (cuentas compradas)
  - `sales` (historial de ventas)
  - `settings` (saldo)
- API REST para todas las operaciones
- Panel web que usa la base de datos (ya no depende de localStorage para los datos principales)
- Admin puede agregar/editar/eliminar plataformas
- Reset de la base de datos desde el panel admin

## Código admin

`gaspke2026`
