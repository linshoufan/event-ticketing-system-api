import uvicorn
import os

if __name__ == "__main__":
    # 支援 reload 功能
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
