import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"=================================================================")
    print(f" Intelligent Land Record Digitization & Validation System")
    print(f" Smart India Hackathon (SIH 2026) Prototype")
    print(f" Server starting on http://{host}:{port}")
    print(f" Open in browser: http://localhost:{port}")
    print(f" Presentation:    http://localhost:{port}/presentation")
    print(f"=================================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
