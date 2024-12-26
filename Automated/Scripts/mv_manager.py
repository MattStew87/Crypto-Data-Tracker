import psycopg2
from dotenv import load_dotenv
import os
from update_registry import UpdateRegistry

class MvManager: 
    """
    Manages creation and maintenence of materialized view. 
    """

    def __init__(self, registry: UpdateRegistry): 
        load_dotenv()
        self.registry = registry
        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB",
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": "5432"
        }
        self.table_name = None

    def connect(self):
        """
        Establishes a connection to the PostgreSQL database.
        :return: A connection object or None if the connection fails.
        """
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None
        
    def create_materialized_view(self, table_name, sql):
        """
        Creates a materialized view in PostgreSQL.
        :param table_name: Name of the materialized view.
        :param sql: SQL query to populate the materialized view.
        """
        self.table_name = table_name

        # Build the CREATE MATERIALIZED VIEW SQL command
        create_mv_sql = f"""
        CREATE MATERIALIZED VIEW {self.table_name} AS
        {sql}
        WITH DATA;
        """
        try:
            # Connect to the database
            conn = self.connect()
            if conn:
                with conn.cursor() as cur:
                    cur.execute(create_mv_sql)
                    conn.commit()
        except Exception as e:
            print(f"Error creating materialized view '{self.table_name}': {e}")
        finally:
            if conn:
                conn.close()


    def add_mv_refresh(self):
        """
        Registers an update query with the centralized registry.
        :param update_query: SQL query to use for updating the table.
        """
        
        self.registry.register_materialized_view(mv_name=self.table_name)
