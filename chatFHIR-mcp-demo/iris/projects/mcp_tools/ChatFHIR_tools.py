from iris_llm import ToolSet, tool
import iris

class FHIRTools(ToolSet):
    """
    A collection of tools for interacting with FHIR data in InterSystems IRIS.
    """
    def __init__(self):
        super().__init__()

    @tool
    def get_patient_count(self) -> dict:
        """Return the total number of patients in ChatFHIR.Patient."""
        # Implementation will be provided in the server code where we have access to the database engine
        try:
            rs = iris.sql.exec("SELECT COUNT(*) AS patient_count FROM ChatFHIR.Patient")
            patient_count = [x for x in rs][0]
            return {"patient_count": patient_count}
        except Exception as e:
            return {"error": f"Failed to retrieve patient count: {str(e)}"}
        
    @tool
    def get_conditions(self) -> list:
        """
        Returns a list of available conditions with their Snomed Code.
        """
        try:
            query = "SELECT DISTINCT SnomedCode, Description FROM ChatFHIR.Condition"
            rs = iris.sql.exec(query)
            df = rs.dataframe()
            return df.to_dict(orient='records')
        except Exception as e:
            return {"error": f"Failed to get available conditions: {str(e)}"}
        
    @tool
    def get_patient_list(self) -> list:
        """
        Returns a list of all patients and their demographics
        """
        try:
            query = """
                SELECT Key AS patient_id, BirthDate, BirthPlaceCity, BirthPlaceCountry, City, Country, 
                FamilyName, Gender, GivenName, PostalCode
                FROM ChatFHIR.Patient
                """
            rs = iris.sql.exec(query)
            df = rs.dataframe()
            return df.to_dict(orient='records')
        except Exception as e:
            return {"error": f"Failed to get available conditions: {str(e)}"}
        

    @tool
    def get_patients_for_condition(self, snomed_code: str) -> list:
        """
        Return a list of patient IDs with a specific condition snomed_code and the status of the condition.
        """
        try:
            query = f"""
                SELECT Patient AS patient_id, status
                FROM ChatFHIR.Condition
                WHERE SnomedCode = ?
                """
            stmt = iris.sql.prepare(query)
            rs = stmt.execute(snomed_code)
            df = rs.dataframe()
            return df.to_dict(orient='records')
        except Exception as e:
            return {"error": f"Failed to get patients for condition {snomed_code}: {str(e)}"}
        
    
    @tool
    def get_patient_demographics(self, patient_ids: list) -> dict:
        """
            Return demographic info (JSON) for a list of patient IDs.
    Provides access to patient demographic data.
    The patient IDs need to include the prefix "Patient/".
        """
        try:
            # Create unique parameter names
            placeholders = ", ".join(["?"] * len(patient_ids))

            query = f"""
                SELECT ID, BirthDate, BirthPlaceCity, BirthPlaceCountry, City, Country,
                    FamilyName, Gender, GivenName, Key, PostalCode, RowNum
                FROM "ChatFHIR"."Patient"
                WHERE Key IN ({placeholders})
            """
            stmt = iris.sql.prepare(query)
            rs = stmt.execute(*patient_ids)
            df = rs.dataframe()
            return df.to_dict(orient='records')

        except Exception as e:
            return {"error": f"Failed to get patient demographics: {str(e)}"}
    
    @tool
    def get_patient_current_bmi(self, patient_ids: list) -> list:
        """
        Return the most recent BMI for a list of patient IDs.
        The patient IDs need to include the prefix "Patient/".
        """
        if not patient_ids:
            return {"error": "No patient IDs provided."}
        try:
            # Create unique parameter names
            # placeholders = ", ".join([f"'{i}'" for i in patient_ids])
            placeholders = ", ".join(["?"] * len(patient_ids))
            query = f"""
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
                """
            stmt = iris.sql.prepare(query)
            rs = stmt.execute(*patient_ids)
            df = rs.dataframe()
            return df.to_dict(orient='records')

        except Exception as e:
            return {"error": f"Failed to get patient BMI: {str(e)}"}
        
    

if __name__=="__main__":
    fhirtools = FHIRTools()

    print(fhirtools.get_catalog())
    print(fhirtools.execute("get_patient_count", {}))
    print(fhirtools.execute("get_conditions", {}))
    print(fhirtools.execute("get_patient_list", {}))
    print(fhirtools.execute("get_patients_for_condition", {"snomed_code": "44054006"}))
    print(fhirtools.execute("get_patient_demographics", {"patient_ids": ["Patient/70048", "Patient/70409"]}))
    print(fhirtools.execute("get_patient_current_bmi", {"patient_ids": ["Patient/70048", "Patient/70409"]}))