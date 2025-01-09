from fastapi import FastAPI
from routes.indexroutes import user
from dotenv import load_dotenv
from config.database import create_tables



app = FastAPI(debug=True)
app.include_router(user)

@app.on_event("startup")
async def startup_event():
    create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
