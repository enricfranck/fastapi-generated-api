# -*- coding: utf-8 -*-
"""test_api_generator.py – v2

Generate FastAPI integration tests (CRUD via HTTP) for every SQLAlchemy
``ClassModel``.  Fully FK‑aware, supports optional JWT auth, and avoids
string/dict concatenation errors.
"""
from __future__ import annotations

import os
import logging
from typing import List, Dict, Optional

import schemas
from schemas import ClassModel, AttributesModel
from model_type import preserve_custom_sections, camel_to_snake
from utils.generate_data_test import generate_column

# ---------------------------------------------------------------------------
# Configuration & logging
# ---------------------------------------------------------------------------
OUTPUT_DIR = "/tests"
TEST_LIST = ["create", "update", "get", "get_by_id", "delete"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper generators (imports / auth / headers)
# ---------------------------------------------------------------------------

def _gen_imports(other_cfg: schemas.OtherConfigSchema) -> str:
    """Return the import block inserted at top of every generated file."""
    lines = [
        "from fastapi import status",
        "from app import crud, schemas",
        "import datetime",
    ]
    if other_cfg.use_authentication:
        lines.append("from app.core import security")
    return "\n".join(lines)


def _gen_headers(other_cfg: schemas.OtherConfigSchema) -> str:
    """Literal for the *headers=...* kwarg or an empty string."""
    return 'headers={"Authorization": f"Bearer {token}"}' if other_cfg.use_authentication else ""


def _gen_auth_setup(other_cfg: schemas.OtherConfigSchema) -> List[str]:
    """Emit lines that create a user + JWT token if auth is enabled."""
    if not other_cfg.use_authentication:
        return []
    return [
        "    # Auth setup",
        "    user_data = {",
        "        'email': 'admin@example.com',",
        "        'password': 'securepassword',",
        "        'is_active': True,",
        "        'is_superuser': False,",
        "    }",
        "    user = crud.user.create(db, obj_in=schemas.UserCreate(**user_data))",
        "    db.commit()",
        "    token = security.create_access_token(sub={'id': str(user.id), 'email': user.email})",
        "",
    ]

# ---------------------------------------------------------------------------
# Dependency builder – recursively POST parent FK resources
# ---------------------------------------------------------------------------

def _build_api_dependencies(
    model: ClassModel,
    all_models: Dict[str, ClassModel],
    other_cfg: schemas.OtherConfigSchema,
    indent: str = "    ",
    created: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Return code lines that POST parent resources once each."""
    if created is None:
        created = {}

    lines: List[str] = []
    hdrs = _gen_headers(other_cfg)

    for attr in model.attributes:
        if attr.is_foreign and attr.foreign_key_class:
            parent_cls = all_models[attr.foreign_key_class]
            if parent_cls.name in created:
                continue  # already done

            # Recurse first (grand‑parents ..)
            lines.extend(
                _build_api_dependencies(parent_cls, all_models, other_cfg, indent, created)
            )

            parent_var = camel_to_snake(parent_cls.name)  # ex: "user"
            parent_endpoint = f"/api/v1/{camel_to_snake(parent_cls.name)}s"
            parent_payload = generate_column(parent_cls.attributes)
            # ensure we have a literal string
            if not isinstance(parent_payload, str):
                parent_payload = repr(parent_payload)

            lines += [
                f"{indent}# Create parent {parent_cls.name}",
                f"{indent}{parent_var}_payload = {parent_payload}",
                f"{indent}resp_{parent_var} = client.post(",
                f"{indent}    '{parent_endpoint}/',",
                f"{indent}    json={parent_var}_payload,",
                f"{indent}    {hdrs}",
                f"{indent})",
                f"{indent}assert resp_{parent_var}.status_code == status.HTTP_200_OK",
                f"{indent}{parent_var} = resp_{parent_var}.json()",
                "",
            ]
            created[parent_cls.name] = parent_var

    return lines

# ---------------------------------------------------------------------------
# Test generation for a single model
# ---------------------------------------------------------------------------

def _gen_test_api(
    model: ClassModel,
    table_name: str,
    all_models: Dict[str, ClassModel],
    other_cfg: schemas.OtherConfigSchema,
) -> str:
    """Return the full set of CRUD test functions for one model."""

    base_ep = f"/api/v1/{table_name}s"
    code_lines: List[str] = []

    # Literal payload template
    payload_template = generate_column(model.attributes)
    if not isinstance(payload_template, str):
        payload_template = repr(payload_template)

    fk_fields = [attr.name for attr in model.attributes if attr.is_foreign]
    fk_fields_literal = repr(fk_fields)

    hdrs_kwarg = _gen_headers(other_cfg)

    for op in TEST_LIST:
        tl: List[str] = [f"\n\ndef test_{op}_{table_name}_api(client, db):"]
        tl.append(f'    """{op.capitalize()} {model.name} via API."""')

        # Auth (optional)
        tl.extend(_gen_auth_setup(other_cfg))

        # Parent creation
        tl.extend(_build_api_dependencies(model, all_models, other_cfg))

        # Payload with FK ids injected
        tl.append(f"    payload = {payload_template}")
        for attr in model.attributes:
            if attr.is_foreign and attr.foreign_key_class:
                parent_var = camel_to_snake(attr.foreign_key_class)
                tl.append(f"    payload['{attr.name}'] = {parent_var}['id']")
        tl.append("")

        # -------------------------------- specific operations -----------------------------
        if op == "create":
            tl += [
                f"    resp = client.post('{base_ep}/', json=payload, {hdrs_kwarg})",
                "    assert resp.status_code == status.HTTP_200_OK, resp.text",
                "    created = resp.json()",
                "    assert created['id'] is not None",
            ] + [
                f"    assert created['{a.name}'] == payload['{a.name}']"
                for a in model.attributes if a.name not in ("id", "hashed_password")
            ]

        elif op == "update":
            tl += [
                f"    resp_c = client.post('{base_ep}/', json=payload, {hdrs_kwarg})",
                "    assert resp_c.status_code == status.HTTP_200_OK",
                "    created = resp_c.json()",
                f"    fk_fields = {fk_fields_literal}",
                "    update_data = {",
                "        k: (not v) if isinstance(v, bool) else",
                "           (v + 1) if isinstance(v, (int, float)) else",
                "           f'updated_{v}'",
                "        for k, v in payload.items()",
                "        if k not in ('id',) and k not in fk_fields",
                "    }",
                f"    data = schemas.{model.name}Update(**update_data)",
                f"    resp_u = client.put(f'{base_ep}/{{created[\"id\"]}}', json=update_data, {hdrs_kwarg})",
                "    assert resp_u.status_code == status.HTTP_200_OK",
                "    updated = resp_u.json()",
                "    assert updated['id'] == created['id']",
            ] + [
                f"    assert updated['{a.name}'] == update_data['{a.name}']"
                for a in model.attributes if a.name not in ("id", "hashed_password") and not a.is_foreign
            ]

        elif op == "get":
            tl += [
                f"    client.post('{base_ep}/', json=payload, {hdrs_kwarg})",
                f"    resp_g = client.get('{base_ep}/', {hdrs_kwarg})",
                "    assert resp_g.status_code == status.HTTP_200_OK",
                "    items = resp_g.json()['data']",
                "    assert any(item.get('id') for item in items)",
            ]

        elif op == "get_by_id":
            tl += [
                f"    resp_c = client.post('{base_ep}/', json=payload, {hdrs_kwarg})",
                "    created = resp_c.json()",
                f"    resp_g = client.get(f'{base_ep}/{{created[\"id\"]}}', {hdrs_kwarg})",
                "    assert resp_g.status_code == status.HTTP_200_OK",
                "    retrieved = resp_g.json()",
                "    assert retrieved['id'] == created['id']",
            ]

        elif op == "delete":
            tl += [
                f"    resp_c = client.post('{base_ep}/', json=payload, {hdrs_kwarg})",
                "    created = resp_c.json()",
                f"    resp_d = client.delete(f'{base_ep}/{{created[\"id\"]}}', {hdrs_kwarg})",
                "    assert resp_d.status_code == status.HTTP_200_OK",
                "    deleted = resp_d.json()",
                f"    assert deleted['msg'] == '{model.name} deleted successfully'",
                f"    resp_chk = client.get(f'{base_ep}/{{created[\"id\"]}}', {hdrs_kwarg})",
                "    assert resp_chk.status_code == status.HTTP_404_NOT_FOUND",
            ]

        code_lines.extend(tl)

    return "\n".join(code_lines)

# ---------------------------------------------------------------------------
# File‑level scaffold
# ---------------------------------------------------------------------------

def _gen_file(model: ClassModel, table_name: str, all_models: Dict[str, ClassModel], other_cfg: schemas.OtherConfigSchema) -> str:
    return "\n".join([
        _gen_imports(other_cfg),
        _gen_test_api(model, table_name, all_models, other_cfg),
    ])

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_test_apis(models: List[ClassModel], output_dir: str, other_cfg: schemas.OtherConfigSchema) -> None:
    out_dir = os.path.join(output_dir, OUTPUT_DIR.lstrip("/"))
    os.makedirs(out_dir, exist_ok=True)

    normalised = [m if isinstance(m, ClassModel) else ClassModel(**m) for m in models]
    all_models: Dict[str, ClassModel] = {m.name: m for m in normalised}

    for mdl in normalised:
        tbl = camel_to_snake(mdl.name)
        content = _gen_file(mdl, tbl, all_models, other_cfg)
        fname = f"test_{tbl}_api.py"
        fpath = os.path.join(out_dir, fname)
        final = preserve_custom_sections(fpath, content)
        with open(fpath, "w", encoding="utf-8") as fp:
            fp.write(final)
        logger.info("Generated test API for %s", tbl)


def main(models: List[ClassModel], other_cfg: schemas.OtherConfigSchema, output_dir: Optional[str] = None) -> None:
    if output_dir is None:
        output_dir = os.getcwd()
    write_test_apis(models, output_dir, other_cfg)


if __name__ == "__main__":
    # Example usage:
    # main(models, other_cfg)
    pass