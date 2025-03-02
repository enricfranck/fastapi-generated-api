from typing import Any, Optional, List

from pydantic import BaseModel, EmailStr


class AttributesModel(BaseModel):
    """Represents a column in a database table using Pydantic."""
    name: str
    type: str
    length: Optional[int] = None
    is_primary: bool = False
    is_indexed: bool = False
    is_auto_increment: bool = False
    is_required: bool = True
    is_unique: bool = False
    is_foreign: bool = False
    foreign_key_class: Optional[str] = None
    foreign_key: Optional[str] = None


class ClassModel(BaseModel):
    """Represents a database table model using Pydantic."""

    name: str
    attributes: List[AttributesModel]

    @property
    def column_type_list(self) -> str:
        """Get unique SQLAlchemy column types used in the model."""
        types = set()
        for attr in self.attributes:
            types.add(attr.type)
        return ", ".join(types)


class ConfigSchema(BaseModel):
    domain: str = "localhost"
    stack_name: str = ""
    server_name: str = ""
    server_host: str = ""
    docker_image_backend: str = "backend"
    backend_cors_origins: List[str] = []
    project_name: str = ""
    secret_key: str = ""
    first_superuser: EmailStr
    first_name_superuser: str = ""
    last_name_superuser: str = ""
    first_superuser_password: str
    smtp_tls: bool = False
    smtp_port: str = ""
    smtp_host: str = ""
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_server: str = "smtp.gmail.com"
    emails_from_email: str = ""
    mysql_host: str = "localhost"
    mysql_port: Any = 3306
    mysql_user: str
    mysql_password: str
    mysql_database: str

    @classmethod
    def from_body(cls, body, config):
        # Helper function to get a value from config or use a default
        def get_or_default(key, default):
            if config.get(key) == "" or config.get(key) == []:
                return default
            return config.get(key, default)

        # Dynamically generate default values based on body.name
        default_stack_name = f"{body.name.lower()}-com"
        default_server_name = f"http://{body.name.lower()}-com"
        default_server_host = f"http://{body.name.lower()}-com"
        default_project_name = f"{body.name.title()}"
        default_secret_key = "tzrctxhgdc876guyguv6v"

        return cls(
            domain=get_or_default("domain", "localhost"),
            stack_name=get_or_default("stack_name", default_stack_name),
            server_name=get_or_default("server_name", default_server_name),
            server_host=get_or_default("server_host", default_server_host),
            docker_image_backend=get_or_default("docker_image_backend", "backend"),
            backend_cors_origins=get_or_default("backend_cors_origins", [
                "http://localhost",
                "http://localhost:4200",
            ]),
            project_name=get_or_default("project_name", default_project_name),
            secret_key=get_or_default("secret_key", default_secret_key),
            first_superuser=get_or_default("first_superuser", ""),
            first_name_superuser=get_or_default("first_name_superuser", "string"),
            last_name_superuser=get_or_default("last_name_superuser", "string"),
            first_superuser_password=get_or_default("first_superuser_password", ""),
            smtp_tls=get_or_default("smtp_tls", True),
            smtp_port=get_or_default("smtp_port", "string"),
            smtp_host=get_or_default("smtp_host", "string"),
            smtp_user=get_or_default("smtp_user", "string"),
            smtp_password=get_or_default("smtp_password", "string"),
            smtp_server=get_or_default("smtp_server", "smtp.gmail.com"),
            emails_from_email=get_or_default("emails_from_email", "test@gmail.com"),
            mysql_host=get_or_default("mysql_host", "localhost"),
            mysql_port=get_or_default("mysql_port", 3306),
            mysql_user=get_or_default("mysql_user", ""),
            mysql_password=get_or_default("mysql_password", ""),
            mysql_database=get_or_default("mysql_database", ""),
        )


class ProjectBase(BaseModel):
    name: str
    path: str
    config: ConfigSchema = None
    class_model: Any = None


class ProjectCreate(BaseModel):
    name: str
    path: str
    config: ConfigSchema = None


class ProjectUpdate(BaseModel):
    class_model: List[ClassModel] = None


class ProjectResponse(ProjectBase):
    id: int

    class Config:
        orm_mode = True


class Body(BaseModel):
    name: str
