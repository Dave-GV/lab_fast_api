# src/models/agenda.py
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr

# Nota: en SQLModel >=0.0.2x con Pydantic v2, Field(regex=...) se ignora en silencio.
# Se usa schema_extra={"pattern": ...} para que la validación sí se aplique.
TELEFONO_PATTERN = r"^\d{7,15}$"


class ContactoBase(SQLModel):
    nombre: str = Field(min_length=2, max_length=50)
    telefono: str = Field(schema_extra={"pattern": TELEFONO_PATTERN})
    mail: EmailStr


class Contacto(ContactoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Reto 2: cada contacto pertenece a un usuario (Foreign Key)
    user_id: Optional[int] = Field(default=None, foreign_key="usuario.id", index=True)


class ContactoCreate(ContactoBase):
    pass


class ContactoUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=50)
    telefono: Optional[str] = Field(default=None, schema_extra={"pattern": TELEFONO_PATTERN})
    mail: Optional[EmailStr] = None
