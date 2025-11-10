from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Magento AI Assistant API is up!"}
