import asyncio
from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ------------------------------------------------------------
# MCP server initialization
# ------------------------------------------------------------
mcp = FastMCP(name="iris-mcp")

# ------------------------------------------------------------
# Database connection setup
# ------------------------------------------------------------
def instantiate_create_engine():
    """
    Creates a SQLAlchemy engine for connecting to the InterSystems IRIS instance.
    """
    username = "SuperUser"
    password = "SYS"
    hostname = "iris"
    port = 1972
    namespace = "CHATFHIR"
    CONNECTION_STRING = f"iris://{username}:{password}@{hostname}:{port}/{namespace}"
    engine = create_engine(CONNECTION_STRING)
    return engine

# Keep a global engine for reuse
engine = instantiate_create_engine()

# ------------------------------------------------------------
# MCP tools
# ------------------------------------------------------------

# === 1. Get patient count ===
@mcp.tool()
async def get_patient_count() -> dict:
    """Return the total number of patients in ChatFHIR.Patient."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) AS patient_count FROM ChatFHIR.Patient"))
            return {"patient_count": result.scalar()}
    except SQLAlchemyError as e:
        return {"error": f"Failed to retrieve patient count: {str(e)}"}

# === 1. Get conditions list ===
@mcp.tool()
async def get_conditions() -> list:
    """
    Returns a list of available conditions with their Snomed Code.
    """
    try:
        query = text(f"""
            SELECT DISTINCT SnomedCode, Description
            FROM ChatFHIR.Condition
        """)

        with engine.connect() as conn:
            result = conn.execute(query).mappings()
            return [dict(row) for row in result]
    except SQLAlchemyError as e:
        return {"error": f"Failed to get available conditions: {str(e)}"}
    
# === 1. Get patient list ===
@mcp.tool()
async def get_patient_list() -> list:
    """
    Returns a list of all patients and their demographics
    """
    try:
        query = text(f"""
            SELECT Key AS patient_id, BirthDate, BirthPlaceCity, BirthPlaceCountry, City, Country, FamilyName, Gender, GivenName, PostalCode
            FROM ChatFHIR.Patient
        """)

        with engine.connect() as conn:
            result = conn.execute(query).mappings()
            return [dict(row) for row in result]
    except SQLAlchemyError as e:
        return {"error": f"Failed to get available conditions: {str(e)}"}    

# === 2. Get patients for a condition ===
@mcp.tool()
async def get_patients_for_condition(snomed_code: str) -> list:
    """
    Return a list of patient IDs with a specific condition snomed_code and the status of the condition.
    """
    try:
        query = text("""
            SELECT Patient AS patient_id, status
            FROM ChatFHIR.Condition
            WHERE SnomedCode = :snomed_code
        """)
        with engine.connect() as conn:
            result = conn.execute(query, {"snomed_code": snomed_code}).mappings()
            return [dict(row) for row in result]
    except SQLAlchemyError as e:
        return {"error": f"Failed to get patients for condition: {str(e)}"}


# === 3. Get patient demographics ===
@mcp.tool()
async def get_patients_demographics(patient_ids: list) -> list:
    """
    Return demographic info (JSON) for a list of patient IDs.
    Provides access to patient demographic data.
    The patient IDs need to include the prefix "Patient/".
    """
    if not patient_ids:
        return {"error": "No patient IDs provided."}

    try:
        # Create unique parameter names
        placeholders = ", ".join([f"'{i}'" for i in patient_ids])

        query = text(f"""
            SELECT ID, BirthDate, BirthPlaceCity, BirthPlaceCountry, City, Country,
                   FamilyName, Gender, GivenName, Key, PostalCode, RowNum
            FROM "ChatFHIR"."Patient"
            WHERE Key IN ({placeholders})
        """)

        with engine.connect() as conn:
            result = conn.execute(query).mappings()
            return [dict(row) for row in result]
    except SQLAlchemyError as e:
        return {"error": f"Failed to get patient demographics: {str(e)}"}

'''
# === 4. Get patient medications ===
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
'''

# === 4. Get patient observations ===
@mcp.tool()
async def get_patients_observations(patient_ids: list) -> list:
    """
    Return each patient's observations (ID + JSON of observation rows).
    """
    if not patient_ids:
        return {"error": "No patient IDs provided."}

    try:
        # Build placeholders (IRIS-safe)
        placeholders = ", ".join([f"'{i}'" for i in patient_ids])
        query = text(f"""
            SELECT Patient AS patient_id, CategoryCode, Code, Description, IssueDateTime, ValueQuantity, ValueUOM
            FROM ChatFHIR.Observation
            WHERE Patient IN ({placeholders})
        """)
        params = {f"id_{i}": val for i, val in enumerate(patient_ids)}

        with engine.connect() as conn:
            result = conn.execute(query, params).mappings()
            return [dict(row) for row in result]

    except SQLAlchemyError as e:
        return {"error": f"Failed to get observations: {str(e)}"}
    

# === 5. Get patient BMI ===
@mcp.tool()
async def get_patients_current_bmi(patient_ids: list) -> list:
    """
    Return each patient's current BMI from ChatFHIR.Observation
    (Code or Description containing 'BMI').
    """
    if not patient_ids:
        return {"error": "No patient IDs provided."}

    try:
        placeholders = ", ".join([f"'{i}'" for i in patient_ids])
        query = text(f"""
            SELECT o.Patient AS patient_id,
                o.ValueQuantity AS BMI,
                o.ValueUOM,
                o.IssueDateTime
            FROM ChatFHIR.Observation o
            WHERE o.Description LIKE 'Body Mass Index'
            AND o.Patient IN ({placeholders})
            AND o.IssueDateTime = (
                SELECT MAX(IssueDateTime)
                FROM ChatFHIR.Observation
                WHERE Patient = o.Patient
                    AND Description LIKE 'Body Mass Index'
            )
            ORDER BY o.IssueDateTime DESC
                """)

        params = {f"id_{i}": val for i, val in enumerate(patient_ids)}

        with engine.connect() as conn:
            result = conn.execute(query, params).mappings()
            return [dict(row) for row in result]
    except SQLAlchemyError as e:
        return {"error": f"Failed to get BMI: {str(e)}"}

# === 7. Get patient conditions ===
@mcp.tool()
async def get_patients_conditions(patient_ids: list) -> list:
    """
    Return each patient's conditions and diagnosis (ID + JSON of condition rows).
    """
    if not patient_ids:
        return {"error": "No patient IDs provided."}

    try:
        # Build placeholders (IRIS-safe)
        placeholders = ", ".join([f"'{i}'" for i in patient_ids])
        query = text(f"""
            SELECT Patient AS patient_id, SnomedCode, Description, Status
            FROM ChatFHIR.Condition
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
