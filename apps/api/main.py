from fastapi import FastAPI

app = FastAPI(title="ORACLE-Omega")


@app.get("/health")
def health():
    return {"ok": True}
