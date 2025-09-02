# schema_extractor.py
import json
from datetime import datetime, timezone
import pyodbc
import pandas as pd


# ---------------------------
# Catalog / DMV fetch helpers
# ---------------------------
def fetch_tables_and_views(conn_str: str) -> pd.DataFrame:
    sql = """
    SELECT 
        o.object_id,
        s.name AS schema_name,
        o.name AS object_name,
        CASE WHEN o.type = 'U' THEN 'TABLE'
             WHEN o.type = 'V' THEN 'VIEW'
             ELSE o.type_desc END AS object_type
    FROM sys.objects AS o
    INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
    WHERE o.type IN ('U','V') AND ISNULL(o.is_ms_shipped, 0) = 0
    ORDER BY s.name, o.name;
    """
    with pyodbc.connect(conn_str, timeout=30) as cxn:
        return pd.read_sql(sql, cxn)


def fetch_columns(conn_str: str) -> pd.DataFrame:
    sql = """
    SELECT 
        c.object_id,
        c.column_id AS ordinal_position,
        c.name AS column_name,
        t.name AS data_type,
        c.max_length,
        c.is_nullable,
        c.is_computed,
        dc.definition AS default_definition
    FROM sys.columns AS c
    INNER JOIN sys.types AS t
        ON t.user_type_id = c.user_type_id
    INNER JOIN sys.objects AS o
        ON o.object_id = c.object_id
    LEFT JOIN sys.default_constraints AS dc
        ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
    WHERE o.type IN ('U','V')
    ORDER BY c.object_id, c.column_id;
    """
    with pyodbc.connect(conn_str, timeout=30) as cxn:
        return pd.read_sql(sql, cxn)


def fetch_primary_keys(conn_str: str) -> pd.DataFrame:
    sql = """
    SELECT 
        k.parent_object_id AS object_id,
        k.name AS constraint_name,
        ic.column_id,
        ic.key_ordinal
    FROM sys.key_constraints AS k
    INNER JOIN sys.index_columns AS ic
        ON ic.object_id = k.parent_object_id
       AND ic.index_id = k.unique_index_id
    WHERE k.type = 'PK'
    ORDER BY k.parent_object_id, ic.key_ordinal;
    """
    with pyodbc.connect(conn_str, timeout=30) as cxn:
        return pd.read_sql(sql, cxn)


def fetch_unique_constraints(conn_str: str) -> pd.DataFrame:
    sql = """
    SELECT 
        k.parent_object_id AS object_id,
        k.name AS constraint_name,
        ic.column_id,
        ic.key_ordinal
    FROM sys.key_constraints AS k
    INNER JOIN sys.index_columns AS ic
        ON ic.object_id = k.parent_object_id
       AND ic.index_id = k.unique_index_id
    WHERE k.type = 'UQ'
    ORDER BY k.parent_object_id, k.name, ic.key_ordinal;
    """
    with pyodbc.connect(conn_str, timeout=30) as cxn:
        return pd.read_sql(sql, cxn)


def fetch_foreign_keys(conn_str: str) -> pd.DataFrame:
    sql = """
    SELECT 
        fk.name AS constraint_name,
        fk.parent_object_id AS parent_id,
        fkc.parent_column_id,
        fk.referenced_object_id AS ref_id,
        fkc.referenced_column_id,
        fkc.constraint_column_id
    FROM sys.foreign_keys AS fk
    INNER JOIN sys.foreign_key_columns AS fkc
        ON fkc.constraint_object_id = fk.object_id
    ORDER BY fk.parent_object_id, fk.name, fkc.constraint_column_id;
    """
    with pyodbc.connect(conn_str, timeout=30) as cxn:
        return pd.read_sql(sql, cxn)


def fetch_row_counts(conn_str: str):
    """
    Try to fetch approximate row counts via sys.dm_db_partition_stats.
    Returns (row_counts_df, warning_or_none)
    """
    sql = """
    SELECT 
        p.object_id,
        SUM(CASE WHEN p.index_id IN (0,1) THEN p.row_count ELSE 0 END) AS row_count
    FROM sys.dm_db_partition_stats AS p
    GROUP BY p.object_id;
    """
    try:
        with pyodbc.connect(conn_str, timeout=30) as cxn:
            df = pd.read_sql(sql, cxn)
        return df, None
    except Exception as e:
        warn = f"Row counts unavailable via sys.dm_db_partition_stats: {e}"
        return pd.DataFrame(columns=["object_id", "row_count"]), warn


# ---------------------------
# Assembly
# ---------------------------
def assemble_model(
    server: str,
    database: str,
    tables_views: pd.DataFrame,
    columns: pd.DataFrame,
    pks: pd.DataFrame,
    uqs: pd.DataFrame,
    fks: pd.DataFrame,
    row_counts: pd.DataFrame,
    warnings: list
) -> dict:
    objects = tables_views.copy().rename(columns={"object_name": "table_name"})
    obj_map = {
        int(r.object_id): {
            "schema_name": r.schema_name,
            "table_name": r.table_name,
            "object_type": r.object_type,
        }
        for _, r in objects.iterrows()
    }

    col_name_map = {
        (int(r.object_id), int(r.ordinal_position)): r.column_name
        for _, r in columns.iterrows()
    }

    # Primary Keys
    pk_map, pk_col_set = {}, set()
    if not pks.empty:
        for oid, grp in pks.groupby("object_id", sort=True):
            grp_sorted = grp.sort_values("key_ordinal")
            pk_cols = [col_name_map.get((int(oid), int(x.column_id))) for _, x in grp_sorted.iterrows()]
            pk_map[int(oid)] = [c for c in pk_cols if c is not None]
            for _, x in grp_sorted.iterrows():
                pk_col_set.add((int(oid), int(x.column_id)))

    # Unique Constraints
    uq_constraints_map, uq_col_set = {}, set()
    if not uqs.empty:
        for (oid, cname), grp in uqs.groupby(["object_id", "constraint_name"], sort=True):
            grp_sorted = grp.sort_values("key_ordinal")
            uq_cols = [col_name_map.get((int(oid), int(x.column_id))) for _, x in grp_sorted.iterrows()]
            uq_constraints_map.setdefault(int(oid), []).append([c for c in uq_cols if c is not None])
            for _, x in grp_sorted.iterrows():
                uq_col_set.add((int(oid), int(x.column_id)))

    # Foreign Keys
    fk_map = {}
    if not fks.empty:
        for (parent_id, cname), grp in fks.groupby(["parent_id", "constraint_name"], sort=True):
            grp_sorted = grp.sort_values("constraint_column_id")
            parent_cols = [col_name_map.get((int(parent_id), int(x.parent_column_id))) for _, x in grp_sorted.iterrows()]
            ref_id = int(grp_sorted.iloc[0]["ref_id"]) if not grp_sorted.empty else None
            ref_obj = obj_map.get(ref_id)
            ref_schema = ref_obj["schema_name"] if ref_obj else None
            ref_table = ref_obj["table_name"] if ref_obj else None
            ref_cols = [col_name_map.get((ref_id, int(x.referenced_column_id))) for _, x in grp_sorted.iterrows()]
            fk_map.setdefault(int(parent_id), []).append({
                "constraint_name": cname,
                "column_names": [c for c in parent_cols if c is not None],
                "references": {
                    "schema": ref_schema,
                    "table": ref_table,
                    "columns": [c for c in ref_cols if c is not None]
                }
            })

    # Row counts
    row_count_map = {int(r.object_id): int(r.row_count) for _, r in row_counts.iterrows() if pd.notna(r.row_count)}

    # Build schema -> tables
    schemas_order = sorted(objects["schema_name"].unique().tolist())
    schema_objs = []
    for sname in schemas_order:
        objs = objects[objects["schema_name"] == sname].sort_values("table_name", kind="mergesort")
        table_list = []
        for _, o in objs.iterrows():
            oid = int(o.object_id)
            otype = o.object_type

            cold = columns[columns["object_id"] == oid].sort_values("ordinal_position", kind="mergesort")
            cols_payload = []
            for _, c in cold.iterrows():
                col_id = int(c.ordinal_position)
                cols_payload.append({
                    "column_name": c.column_name,
                    "data_type": c.data_type,
                    "max_length": int(c.max_length) if pd.notna(c.max_length) else None,
                    "is_nullable": bool(c.is_nullable),
                    "ordinal_position": int(c.ordinal_position),
                    "is_primary_key": (oid, col_id) in pk_col_set,
                    "is_unique": (oid, col_id) in uq_col_set,
                    "is_computed": bool(c.is_computed),
                    "default_definition": str(c.default_definition) if pd.notna(c.default_definition) else None
                })

            rc_val = None if otype == "VIEW" else row_count_map.get(oid)
            table_list.append({
                "table_name": o.table_name,
                "object_type": otype,
                "row_count": rc_val,
                "columns": cols_payload,
                "primary_key": pk_map.get(oid, []),
                "unique_constraints": uq_constraints_map.get(oid, []),
                "foreign_keys": fk_map.get(oid, [])
            })

        schema_objs.append({"schema_name": sname, "tables": table_list})

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "generated_at_utc": generated,
        "server": server or "",
        "database": database or "",
        "incomplete": len(warnings) > 0,
        "warnings": warnings,
        "schemas": schema_objs
    }


# ---------------------------
# Public API
# ---------------------------
def generate_schema(conn_str: str, server: str = "", database: str = ""):
    """
    Extract full schema using only system catalogs/DMVs.
    Returns: (model_dict, columns_inventory_df, warnings_list)
    """
    warnings = []

    tv = fetch_tables_and_views(conn_str)
    cols = fetch_columns(conn_str)
    pks = fetch_primary_keys(conn_str)
    uqs = fetch_unique_constraints(conn_str)
    fks = fetch_foreign_keys(conn_str)
    rc_df, warn = fetch_row_counts(conn_str)
    if warn:
        warnings.append(warn)

    model = assemble_model(
        server=server,
        database=database,
        tables_views=tv,
        columns=cols,
        pks=pks,
        uqs=uqs,
        fks=fks,
        row_counts=rc_df,
        warnings=warnings
    )

    # Build a simple columns inventory DF for UI/debug
    obj_lookup = tv.set_index("object_id")[["schema_name", "object_name", "object_type"]].rename(
        columns={"object_name": "table_name"}
    )
    merged = cols.merge(obj_lookup, left_on="object_id", right_index=True, how="left")
    col_inv = merged[["schema_name", "table_name", "column_name", "data_type", "is_nullable"]].copy()
    col_inv = col_inv.rename(columns={
        "schema_name": "schema",
        "table_name": "table",
        "column_name": "column",
        "data_type": "type",
        "is_nullable": "nullable"
    })
    col_inv["nullable"] = col_inv["nullable"].astype(bool)
    col_inv = col_inv.sort_values(["schema", "table", "column"], kind="mergesort").reset_index(drop=True)

    return model, col_inv, warnings


# def save_schema_artifacts(model: dict, json_path: str = "lakehouse_schema.json", md_path: str = "lakehouse_schema.md"):
#     write_json(json_path, model)
#     write_markdown(md_path, model)
def save_schema_artifacts(model: dict, json_path: str = None, md_path: str = None):
    """
    Return JSON string (and optionally still write to disk).
    """
    schema_json = json.dumps(model, ensure_ascii=False, indent=2)

    # Only write files if paths are provided
    if json_path:
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(schema_json)
    if md_path:
        write_markdown(md_path, model)

    return schema_json


# ---------------------------
# Writers
# ---------------------------
def write_json(path: str, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_markdown(path: str, model: dict):
    lines = []
    lines.append("# Database Schema Inventory\n")
    lines.append(f"- **Server:** `{model.get('server')}`")
    lines.append(f"- **Database:** `{model.get('database')}`")
    lines.append(f"- **Generated (UTC):** {model.get('generated_at_utc')}")
    lines.append(f"- **Incomplete:** {model.get('incomplete')}\n")
    if model.get("warnings"):
        lines.append("> **Warnings:**")
        for w in model["warnings"]:
            lines.append(f"> - {w}")
        lines.append("")

    # Index
    lines.append("## Schema Index\n")
    for sch in model["schemas"]:
        lines.append(f"### `{sch['schema_name']}`")
        if not sch["tables"]:
            lines.append("- _No objects_")
        else:
            for obj in sch["tables"]:
                lines.append(f"- `{obj['table_name']}` ({obj['object_type']})")
        lines.append("")

    # Details
    for sch in model["schemas"]:
        lines.append(f"## Schema: `{sch['schema_name']}`")
        for obj in sch["tables"]:
            fq = f"{sch['schema_name']}.{obj['table_name']}"
            lines.append(f"\n### `{fq}` — {obj['object_type']}")
            rc = obj.get("row_count")
            lines.append(f"- **Approx Row Count:** {rc if rc is not None else 'N/A'}")
            pk = obj.get("primary_key") or []
            lines.append(f"- **Primary Key:** {', '.join(pk) if pk else 'None'}")
            uqs = obj.get("unique_constraints") or []
            lines.append(f"- **Unique Constraints:** {('; '.join([', '.join(x) for x in uqs])) if uqs else 'None'}")
            fks = obj.get("foreign_keys") or []
            if fks:
                lines.append("- **Foreign Keys:**")
                for fk in fks:
                    ref = fk["references"]
                    ref_cols = ", ".join(ref["columns"]) if ref["columns"] else ""
                    lines.append(
                        f"  - `{fk['constraint_name']}`: ({', '.join(fk['column_names'])}) "
                        f"→ `{ref.get('schema')}.{ref.get('table')}` ({ref_cols})"
                    )
            else:
                lines.append("- **Foreign Keys:** None")

            # Columns
            lines.append("\n| # | Column | Type | MaxLen | Nullable | PK | Unique | Computed | Default |")
            lines.append("|---:|---|---|---:|:--:|:--:|:--:|:--:|---|")
            for col in sorted(obj["columns"], key=lambda c: c["ordinal_position"]):
                lines.append(
                    f"| {col['ordinal_position']} "
                    f"| `{col['column_name']}` "
                    f"| `{col['data_type']}` "
                    f"| {col['max_length'] if col['max_length'] is not None else ''} "
                    f"| {'YES' if col['is_nullable'] else 'NO'} "
                    f"| {'✓' if col['is_primary_key'] else ''} "
                    f"| {'✓' if col['is_unique'] else ''} "
                    f"| {'✓' if col['is_computed'] else ''} "
                    f"| {('`'+str(col['default_definition'])+'`') if col['default_definition'] else ''} |"
                )
            lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
