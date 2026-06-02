from pathlib import Path

from fastapi import APIRouter


router = APIRouter()


@router.get("/debug/cloudsql")
def debug_cloudsql():
    return {
        "cloudsql_exists": Path("/cloudsql").exists(),
        "account_db_exists": Path(
            "/cloudsql/ticketing-system-498218:asia-east1:account-db"
        ).exists(),
    }
