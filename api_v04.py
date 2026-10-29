
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="PHON v0.4 Surrogate API")
model = joblib.load("v04_surrogate.pkl")

class DesignRequest(BaseModel):
    ratio: float
    bandwidth: float

class DesignResponse(BaseModel):
    transmission_speed: float
    compressed_freq: float

@app.post("/predict", response_model=DesignResponse)
def predict(req: DesignRequest):
    features = np.array([[req.ratio, req.bandwidth]])
    speed = float(model.predict(features)[0])
    # Физика: оригиналната честота е 5 GHz, компресията я дели на ratio
    compressed_freq = 5.0 / req.ratio
    return DesignResponse(transmission_speed=speed, compressed_freq=compressed_freq)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
