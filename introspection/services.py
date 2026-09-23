import os
from contextlib import closing

import MySQLdb


class SourceDatabaseUnavailable(Exception):
    pass


def _settings():
    required = ["SOURCE_DB_NAME", "SOURCE_DB_USER", "SOURCE_DB_PASSWORD"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SourceDatabaseUnavailable("The source database connection is not fully configured.")
    return {
        "host": os.getenv("SOURCE_DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("SOURCE_DB_PORT", "3306")),
        "user": os.environ["SOURCE_DB_USER"],
        "passwd": os.environ["SOURCE_DB_PASSWORD"],
        "db": os.environ["SOURCE_DB_NAME"],
        "charset": "utf8mb4",
        "connect_timeout": 5,
    }


def _rows(cursor, query, params):
    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def inspect_mysql():
    config = _settings()
    schema = config["db"]
    try:
        with closing(MySQLdb.connect(**config)) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
                cursor.execute(
                    "SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_VARIABLES "
                    "WHERE VARIABLE_NAME = 'VERSION'"
                )
                version = str(cursor.fetchone()[0])
                tables = _rows(
                    cursor,
                    """
                    SELECT TABLE_SCHEMA AS `schema`, TABLE_NAME AS `table`,
                           COALESCE(TABLE_ROWS, 0) AS `rows`, TABLE_TYPE AS `type`,
                           COALESCE(ENGINE, '') AS engine, COALESCE(TABLE_COLLATION, '') AS collation,
                           COALESCE(TABLE_COMMENT, '') AS comment
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """,
                    [schema],
                )
                columns = _rows(
                    cursor,
                    """
                    SELECT TABLE_SCHEMA AS `schema`, TABLE_NAME AS `table`, COLUMN_NAME AS name,
                           LOWER(DATA_TYPE) AS type, ORDINAL_POSITION AS ordinal_position,
                           (IS_NULLABLE = 'YES') AS nullable,
                           CAST(CHARACTER_MAXIMUM_LENGTH AS CHAR) AS character_maximum_length,
                           NUMERIC_PRECISION AS numeric_precision, NUMERIC_SCALE AS numeric_scale,
                           COLUMN_DEFAULT AS `default`, COLLATION_NAME AS collation,
                           (EXTRA LIKE '%%auto_increment%%') AS is_identity,
                           COALESCE(COLUMN_COMMENT, '') AS comment
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                    [schema],
                )
                for column in columns:
                    precision = column.pop("numeric_precision")
                    scale = column.pop("numeric_scale")
                    column["nullable"] = bool(column["nullable"])
                    column["is_identity"] = bool(column["is_identity"])
                    column["precision"] = (
                        {
                            "precision": int(precision) if precision is not None else None,
                            "scale": int(scale) if scale is not None else None,
                        }
                        if precision is not None or scale is not None
                        else None
                    )
                pk_rows = _rows(
                    cursor,
                    """
                    SELECT TABLE_SCHEMA AS `schema`, TABLE_NAME AS `table`, COLUMN_NAME AS `column`,
                           ORDINAL_POSITION
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s AND CONSTRAINT_NAME = 'PRIMARY'
                    ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                    [schema],
                )
                pk_groups = {}
                for row in pk_rows:
                    pk_groups.setdefault(row["table"], []).append(row["column"])
                pk_info = [
                    {
                        "schema": row["schema"],
                        "table": row["table"],
                        "column": row["column"],
                        "pk_def": f"PRIMARY KEY ({', '.join(pk_groups[row['table']])})",
                    }
                    for row in pk_rows
                ]
                fk_info = _rows(
                    cursor,
                    """
                    SELECT k.TABLE_SCHEMA AS `schema`, k.TABLE_NAME AS `table`, k.COLUMN_NAME AS `column`,
                           k.CONSTRAINT_NAME AS foreign_key_name,
                           k.REFERENCED_TABLE_SCHEMA AS reference_schema,
                           k.REFERENCED_TABLE_NAME AS reference_table,
                           k.REFERENCED_COLUMN_NAME AS reference_column,
                           CONCAT('FOREIGN KEY (', k.COLUMN_NAME, ') REFERENCES ',
                                  k.REFERENCED_TABLE_NAME, '(', k.REFERENCED_COLUMN_NAME, ') ON UPDATE ',
                                  r.UPDATE_RULE, ' ON DELETE ', r.DELETE_RULE) AS fk_def
                    FROM information_schema.KEY_COLUMN_USAGE k
                    JOIN information_schema.REFERENTIAL_CONSTRAINTS r
                      ON r.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
                     AND r.TABLE_NAME = k.TABLE_NAME AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
                    WHERE k.TABLE_SCHEMA = %s AND k.REFERENCED_TABLE_NAME IS NOT NULL
                    ORDER BY k.TABLE_NAME, k.CONSTRAINT_NAME, k.ORDINAL_POSITION
                """,
                    [schema],
                )
                indexes = _rows(
                    cursor,
                    """
                    SELECT TABLE_SCHEMA AS `schema`, TABLE_NAME AS `table`, INDEX_NAME AS name,
                           COLUMN_NAME AS `column`, LOWER(INDEX_TYPE) AS index_type,
                           CARDINALITY AS cardinality, NULL AS size,
                           (NON_UNIQUE = 0) AS `unique`,
                           IF(COLLATION = 'D', 'desc', 'asc') AS direction,
                           SEQ_IN_INDEX AS column_position
                    FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
                """,
                    [schema],
                )
                for index in indexes:
                    index["unique"] = bool(index["unique"])
                views = _rows(
                    cursor,
                    """
                    SELECT TABLE_SCHEMA AS `schema`, TABLE_NAME AS view_name,
                           COALESCE(VIEW_DEFINITION, '') AS view_definition
                    FROM information_schema.VIEWS WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME
                """,
                    [schema],
                )
                checks = _rows(
                    cursor,
                    """
                    SELECT tc.CONSTRAINT_SCHEMA AS `schema`, tc.TABLE_NAME AS `table`,
                           cc.CHECK_CLAUSE AS expression
                    FROM information_schema.TABLE_CONSTRAINTS tc
                    JOIN information_schema.CHECK_CONSTRAINTS cc
                      ON cc.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
                     AND cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
                    WHERE tc.CONSTRAINT_SCHEMA = %s AND tc.CONSTRAINT_TYPE = 'CHECK'
                    ORDER BY tc.TABLE_NAME, tc.CONSTRAINT_NAME
                """,
                    [schema],
                )
                connection.rollback()
    except MySQLdb.Error as exc:
        raise SourceDatabaseUnavailable(
            f"Unable to inspect configured MySQL source ({exc.__class__.__name__})."
        ) from exc

    return {
        "fk_info": fk_info,
        "pk_info": pk_info,
        "columns": columns,
        "indexes": indexes,
        "tables": tables,
        "views": views,
        "check_constraints": checks,
        "database_name": schema,
        "version": version,
    }
