# src/routers/views.py
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import Session, select
from src.database import get_session
from src.models.agenda import Contacto, ContactoCreate
from src.models.user import Usuario
from src.auth.security import verify_password, create_access_token
from src.auth.dependencies import get_optional_user_from_cookie, COOKIE_NAME
from src.config import ACCESS_TOKEN_EXPIRE_MINUTES

templates = Jinja2Templates(directory="src/templates")

MENSAJES_ERROR = {
    "nombre": "El nombre debe tener entre 2 y 50 caracteres.",
    "telefono": "El teléfono debe tener solo dígitos (de 7 a 15).",
    "mail": "El correo electrónico no es válido.",
}
router = APIRouter(prefix="/views", tags=["Vistas Web (Jinja2)"])


def _render_agenda(request, session, user, errores=None, form=None, status_code=200):
    contactos = session.exec(select(Contacto).where(Contacto.user_id == user.id)).all()
    return templates.TemplateResponse(
        request,
        "agenda.html",
        {"contactos": contactos, "user": user, "errores": errores or [], "form": form or {}},
        status_code=status_code,
    )


@router.get("/agenda")
def render_agenda_view(
    request: Request,
    session: Session = Depends(get_session),
    user: Optional[Usuario] = Depends(get_optional_user_from_cookie),
):
    if user is None:
        return RedirectResponse("/views/login", status_code=status.HTTP_303_SEE_OTHER)
    return _render_agenda(request, session, user)


# Reto 3: formulario HTML para crear contactos
@router.post("/agenda")
def crear_contacto_form(
    request: Request,
    nombre: str = Form(...),
    telefono: str = Form(...),
    mail: str = Form(...),
    session: Session = Depends(get_session),
    user: Optional[Usuario] = Depends(get_optional_user_from_cookie),
):
    if user is None:
        return RedirectResponse("/views/login", status_code=status.HTTP_303_SEE_OTHER)
    form = {"nombre": nombre, "telefono": telefono, "mail": mail}
    try:
        data = ContactoCreate.model_validate(form)
    except ValidationError as e:
        campos = {str(err["loc"][0]) for err in e.errors() if err["loc"]}
        errores = [msg for campo, msg in MENSAJES_ERROR.items() if campo in campos]
        return _render_agenda(request, session, user, errores, form, status_code=422)
    session.add(Contacto.model_validate(data, update={"user_id": user.id}))
    session.commit()
    # Patrón Post/Redirect/Get
    return RedirectResponse("/views/agenda", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/agenda/{id}/eliminar")
def eliminar_contacto_form(
    id: int,
    session: Session = Depends(get_session),
    user: Optional[Usuario] = Depends(get_optional_user_from_cookie),
):
    if user is None:
        return RedirectResponse("/views/login", status_code=status.HTTP_303_SEE_OTHER)
    contacto = session.get(Contacto, id)
    if contacto and contacto.user_id == user.id:
        session.delete(contacto)
        session.commit()
    return RedirectResponse("/views/agenda", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_view(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(Usuario).where(Usuario.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Usuario o contraseña incorrectos"}, status_code=401
        )
    token = create_access_token({"sub": user.username})
    response = RedirectResponse("/views/agenda", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        COOKIE_NAME, token, httponly=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/views/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response
