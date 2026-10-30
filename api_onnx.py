from fastapi import FastAPI
from pydantic import BaseModel
import onnxruntime as ort
import numpy as np
import os

app = FastAPI(title="PHON v0.5 ONNX API")

# Зареждаме ONNX модела (намира се в integration_artifacts/)
MODEL_PATH = os.path.join("integration_artifacts", "phon_model.onnx")
session = ort.InferenceSession(MODEL_PATH)

class DesignRequest(BaseModel):
    ratio: float
    bandwidth: float

class DesignResponse(BaseModel):
    transmission_speed: float
    compressed_freq: float

@app.post("/predict", response_model=DesignResponse)
def predict(req: DesignRequest):
    # 1. Подготовка на входа: ONNX моделът очаква 2D float32 масив [1, 2]
    input_data = np.array([[req.ratio, req.bandwidth]], dtype=np.float32)
    
    # 2. Изпълнение на модела (input name e 'float_input')
    inputs = {"float_input": input_data}
    outputs = session.run(None, inputs)
    
    # 3. Извличане на резултата
    speed = float(outputs[0][0][0])
    
    # 4. Изчисляване на компресираната честота (физика)
    compressed_freq = 5.0 / req.ratio
    
    return DesignResponse(
        transmission_speed=speed,
        compressed_freq=compressed_freq
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)