#!/usr/bin/env python3
import iris
import os
import subprocess
import sys

IRIS_HOST = "localhost"
IRIS_PORT = 1973
NAMESPACE = "READYAI"


def _afhir_table_count(cursor) -> int:
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='AFHIRData'")
    return cursor.fetchone()[0]


def seed_wallet(irispy):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("WARNING: OPENAI_API_KEY not set — skipping Wallet seed. LLM calls will fail.")
        return
    sc = irispy.classMethodValue("ReadyAI.ConfigStoreSetup", "SetupWithAPIKey", api_key)
    if sc == 1:
        print("API key stored in IRIS Wallet and ConfigStore updated.")
    else:
        print(f"WARNING: SetupWithAPIKey returned sc={sc}")


def main():
    print("Connecting to IRIS...")
    conn = iris.connect(IRIS_HOST, IRIS_PORT, NAMESPACE, "SuperUser", "SYS")
    try:
        irispy = iris.createIRIS(conn)
        seed_wallet(irispy)

        cur = conn.cursor()
        count = _afhir_table_count(cur)
        if count > 0:
            print(f"AFHIRData already has {count} tables. FHIR setup skipped.")
            return

        # subprocess.run(
        #     [
        #         "docker",
        #         "cp",
        #         "ReadyAI-demo/iris/projects/ObjectScript/ReadyAI/FSBSetup.cls",
        #         "readyai-demo-iris-1:/tmp/FSBSetup.cls",
        #     ],
        #     check=True,
        # )
        # irispy.classMethodValue("%SYSTEM.OBJ", "Load", "/tmp/FSBSetup.cls", "ck")
        print("Running FSBSetup.RunAll() — this takes 5-10 minutes...")

        sc = irispy.classMethodValue("ReadyAI.Setup.FSBSetup", "RunAll")
        print(f"RunAll completed: sc={sc}")

        print(f"AFHIRData tables created: {_afhir_table_count(cur)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
