"""
Tool for sql.query action
Connects to a real PostgreSQL database.
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

class ToolError(Exception):
    def __init__(self, code, summary, detail, hint=None, retriable=False):
        self.code = code; self.summary = summary; self.detail = detail
        self.hint = hint; self.retriable = retriable
    def to_dict(self): return vars(self)

def get_pg_conn():
    print("--- Attempting to get PostgreSQL connection ---")
    dsn = os.getenv("POSTGRES_DSN") or (
        f"host={os.getenv('POSTGRES_HOST')} port={os.getenv('POSTGRES_PORT','5432')} "
        f"dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')}"
    )
    if not dsn:
        raise ToolError("NO_DSN", "missing_connection", "No PostgreSQL DSN/credentials provided",
                        hint="Set POSTGRES_DSN or POSTGRES_HOST/DB/USER/PASSWORD", retriable=True)
    try:
        return psycopg2.connect(dsn, connect_timeout=5)
    except Exception as e:
        raise ToolError("CONN_FAIL", "connection_failed", str(e), retriable=True)

def query_postgres(query: str, params: tuple = None) -> dict:
    """
    Executes a read-only SQL query against a Postgres database, with support for query parameters.
    """
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        if not all([host, db, user, password]):
            raise ValueError("POSTGRES_DSN must be set or POSTGRES_HOST/PORT/DB/USER/PASSWORD must be provided in .env")
        dsn = f"host={host} port={port} dbname={db} user={user} password={password} sslmode=prefer"

    conn = None
    try:
        conn = psycopg2.connect(dsn)
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            print(f"Executing SQL Query: {query} with params: {params}")
            
            if not query.strip().upper().startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed.")

            cursor.execute(query, params)
            
            rows = [dict(row) for row in cursor.fetchall()]
            count = len(rows)
            
            return {"rows": rows, "count": count}
    except psycopg2.Error as e:
        error_details = {
            "error_type": "PostgreSQL Error",
            "pgcode": e.pgcode,
            "pgerror": e.pgerror,
            "details": str(e)
        }
        print(f"A database error occurred: {error_details}")
        return {"error": f"Database Error: {e.pgerror} (Code: {e.pgcode})", "count": 0, "rows": []}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}", "count": 0, "rows": []}
    finally:
        if conn:
            conn.close()

def get_schema() -> dict:
    """
    Retrieves the schema of the PostgreSQL database.
    """
    query = """
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'public';
    """
    return query_postgres(query)

def list_tables(schemas=None, include_system=False):
    print(f"--- Calling list_tables with schemas={schemas}, include_system={include_system} ---")
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if include_system:
                sql = """SELECT schemaname, tablename
                         FROM pg_catalog.pg_tables
                         ORDER BY schemaname, tablename"""
                cur.execute(sql)
            elif schemas:
                sql = """SELECT schemaname, tablename
                         FROM pg_catalog.pg_tables
                         WHERE schemaname = ANY(%s)
                         ORDER BY schemaname, tablename"""
                cur.execute(sql, (schemas,))
            else:
                sql = """SELECT schemaname, tablename
                         FROM pg_catalog.pg_tables
                         WHERE schemaname NOT IN ('pg_catalog','information_schema')
                         ORDER BY schemaname, tablename"""
                cur.execute(sql)
            rows = cur.fetchall()
            return {
                "ok": True,
                "tables": [{"schema": r["schemaname"], "table": r["tablename"]} for r in rows],
                "count": len(rows)
            }
    except psycopg2.Error as e:
        # Chuẩn hoá lỗi để agent “auto-repair/clarify”
        code = getattr(e, "pgcode", "PG_ERR")
        msg = getattr(e, "pgerror", str(e))
        # ví dụ: permission denied for schema → gợi ý dùng list_schemas trước
        hint = "Try specifying allowed schemas or run list_schemas" if code else None
        raise ToolError(code, "sql_error", msg, hint=hint, retriable=False)
    finally:
        conn.close()

def describe_table(table_name: str) -> dict:
    """
    Describes the structure of a specific table by fetching column names from a LIMIT 0 query.
    This is a robust method that avoids issues with information_schema permissions.
    """
    # Use a LIMIT 0 query to get column headers without fetching data.
    query = f"SELECT * FROM {table_name} LIMIT 0;"
    
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        if not all([host, db, user, password]):
            raise ValueError("Database connection details must be set in .env")
        dsn = f"host={host} port={port} dbname={db} user={user} password={password} sslmode=prefer"

    conn = None
    try:
        conn = psycopg2.connect(dsn)
        with conn.cursor() as cursor:
            print(f"Executing robust schema discovery query: {query}")
            cursor.execute(query)
            
            # Even with 0 rows, cursor.description will contain column info
            if cursor.description is None:
                return {"error": f"Could not get description for table {table_name}. It might not exist or you may lack permissions.", "rows": [], "count": 0}

            columns = [{'column_name': col.name, 'data_type': psycopg2.extensions.string_types.get(col.type_code, 'unknown')} for col in cursor.description]
            
            return {"rows": columns, "count": len(columns)}

    except psycopg2.Error as e:
        error_details = {
            "error_type": "PostgreSQL Error",
            "pgcode": e.pgcode,
            "pgerror": e.pgerror,
            "details": str(e)
        }
        print(f"A database error occurred during schema discovery: {error_details}")
        return {"error": f"Database Error: {e.pgerror} (Code: {e.pgcode})", "count": 0, "rows": []}
    except Exception as e:
        print(f"An unexpected error occurred during schema discovery: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}", "count": 0, "rows": []}
    finally:
        if conn:
            conn.close()

def get_table_info(table_name: str) -> dict:
    """
    Gets detailed information about a table including row count and sample data.
    """
    # Note: We can't parameterize table names, so we use them directly here.
    # This is generally safe if table names are coming from a controlled source like list_tables.
    count_query = f"SELECT COUNT(*) as row_count FROM {table_name};"
    count_result = query_postgres(count_query)
    
    sample_query = f"SELECT * FROM {table_name} LIMIT 5;"
    sample_result = query_postgres(sample_query)
    
    column_query = """
    SELECT 
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns 
    WHERE table_name = %s
    ORDER BY ordinal_position;
    """
    column_result = query_postgres(column_query, (table_name,))
    
    return {
        "table_name": table_name,
        "row_count": count_result.get("rows", [{}])[0].get("row_count", 0) if count_result.get("rows") else 0,
        "columns": column_result.get("rows", []),
        "sample_data": sample_result.get("rows", []),
        "sample_count": len(sample_result.get("rows", []))
    }

def search_in_table(table_name: str, column_name: str, search_term: str, limit: int = 10) -> dict:
    """
    Searches for data in a specific column of a table.
    """
    # Note: Table and column names cannot be parameterized in standard SQL.
    # We must be careful to validate these inputs if they come from an external user.
    query = f"""SELECT * FROM {table_name} WHERE {column_name} ILIKE %s LIMIT %s;"""
    return query_postgres(query, (f"%{search_term}%", limit))

def get_distinct_values(table_name: str, column_name: str, limit: int = 50) -> dict:
    """
    Gets distinct values from a specific column.
    """
    query = f"""SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL ORDER BY {column_name} LIMIT %s;"""
    return query_postgres(query, (limit,))

def get_table_statistics(table_name: str) -> dict:
    """
    Gets statistical information about a table.
    """
    query = """SELECT schemaname, tablename, attname, n_distinct, correlation FROM pg_stats WHERE tablename = %s;"""
    return query_postgres(query, (table_name,))

def find_related_tables(table_name: str) -> dict:
    """
    Finds tables that might be related through foreign keys.
    """
    query = """
    SELECT 
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND (tc.table_name = %s OR ccu.table_name = %s);
    """
    return query_postgres(query, (table_name, table_name))

def execute_custom_query(query: str) -> dict:
    """
    Executes a custom SQL query with safety checks.
    """
    # Additional safety checks
    query_upper = query.strip().upper()
    
    # Block dangerous operations
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {
                "error": f"Operation '{keyword}' is not allowed for safety reasons",
                "count": 0,
                "rows": []
            }
    
    # Ensure it's a SELECT query
    if not query_upper.startswith('SELECT'):
        return {
            "error": "Only SELECT queries are allowed",
            "count": 0,
            "rows": []
        }
    
    return query_postgres(query)