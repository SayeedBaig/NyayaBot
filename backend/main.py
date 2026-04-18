from fastapi import FastAPI
from routes.analyze import router as analyze_router
from routes.document import router as document_router
   
app = FastAPI()

app.include_router(analyze_router)
app.include_router(document_router) 

@app.get("/")
def root():
    return {"message": "Welcome to NyayaBot API!"}  

