import asyncio
from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from db_connection import instantiate_create_engine

# MCP server initialization
mcp = FastMCP(name="medications-mcp")

# Database connection setup
engine = instantiate_create_engine()


# MCP tools
# === Get patient medications ===
@mcp.tool()
async def get_patients_medications(patient_ids: list) -> list:
    """
    Return each patient's medications (ID + JSON of medication rows).
    """
    if not patient_ids:
        return {"error": "No patient IDs provided."}

    try:
        # Build placeholders (IRIS-safe)
        placeholders = ", ".join([f"'{i}'" for i in patient_ids])
        query = text(f"""
            SELECT Patient AS patient_id, ID AS MedicationID, Code, Description
            FROM ChatFHIR.MedicationRequest
            WHERE Patient IN ({placeholders})
        """)
        params = {f"id_{i}": val for i, val in enumerate(patient_ids)}

        with engine.connect() as conn:
            result = conn.execute(query, params).mappings()
            return [dict(row) for row in result]

    except SQLAlchemyError as e:
        return {"error": f"Failed to get medications: {str(e)}"}

# ------------------------------------------------------------
# Run the server
# ------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
