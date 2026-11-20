# Agenda FastAPI — Modular, SQLModel, JWT y Jinja2

## Ejecución
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
- API / Swagger: http://127.0.0.1:8000/docs
- Panel web: http://127.0.0.1:8000/views/agenda

Variables de entorno opcionales (`src/config.py`): `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

## Reto 1 — Probar OAuth2 desde Swagger
1. En `/docs`, abrir `POST /auth/register` → *Try it out* → enviar
   `{"username": "ana", "email": "ana@example.com", "password": "1234"}` (respuesta 201).
2. Clic en el botón **Authorize** (candado, arriba a la derecha).
3. Escribir `username` y `password` y pulsar *Authorize*. Swagger llama a `POST /auth/token`
   (definido en `OAuth2PasswordBearer(tokenUrl="/auth/token")`), guarda el JWT y desde entonces
   envía `Authorization: Bearer <token>` en cada petición.
4. Probar `POST /agenda`, `PUT /agenda/{id}`, `DELETE /agenda/{id}`: responden 201/200 en lugar de 401.
   Con *Logout* en el mismo diálogo vuelven a dar 401.

Con curl:
```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/token -d "username=ana&password=1234" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -X POST localhost:8000/agenda -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"nombre":"Luis","telefono":"5551234","mail":"luis@example.com"}'
```

## Reto 2 — Relación Usuario → Contacto
`Contacto.user_id` es una Foreign Key a `usuario.id`. Todos los endpoints de `/agenda`
(incluidos los GET) requieren JWT y filtran por `current_user.id`; un contacto ajeno responde 404.
> Si tenías un `agenda.db` de antes de este cambio, bórralo: `create_all` no altera tablas existentes.

## Reto 3 — Formulario HTML con Jinja2
`/views/login` inicia sesión y guarda el JWT en una cookie HttpOnly. `/views/agenda` muestra
solo los contactos del usuario, con formulario para agregarlos (validado con `ContactoCreate`,
errores mostrados en la página) y botón para eliminar. Patrón Post/Redirect/Get.

## Diferencias respecto a la guía
- `bcrypt==4.0.1` fijado: `passlib 1.7.4` falla con `bcrypt>=4.1`.
- `telefono` usa `Field(schema_extra={"pattern": ...})`: con SQLModel actual + Pydantic v2,
  `Field(regex=...)` **se ignora sin avisar** y acepta cualquier teléfono.
- `/auth/register` responde con `UsuarioPublic` para no exponer `hashed_password`.
- `TemplateResponse(request, nombre, contexto)`: firma actual de Starlette (la de la guía está obsoleta).
- `src/config.py` centraliza las llaves (la guía lo lista pero no lo define).
