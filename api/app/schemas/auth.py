from pydantic import BaseModel, Field, field_validator


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Lozinka ne smije biti duža od 72 bajta")
        return value


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)
