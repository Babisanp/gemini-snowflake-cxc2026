from snowflake.snowpark import Session
from snowflake.snowpark.functions import (
    array_except,
    array_size,
    parse_json,
    lit
)
from dotenv import load_dotenv
import os

load_dotenv()

connection_parameters = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA")
}

def snowflake_table(fridge_ingredients):
    session = Session.builder.configs(connection_parameters).create()

    df = (
        session
        .table("BABI_DB.CXC.RECIPE_TABLE")
        .filter(
            array_size(
                array_except(parse_json('"ingredients"'), lit(fridge_ingredients))
            ) == 0
        )
    )

    json_table = df.to_pandas().to_json(orient="records")
    session.close()
    return json_table