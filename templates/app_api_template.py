from pathlib import Path
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from notebook_converter import NotebookConverter
import os

NOTEBOOKS_PATH = Path("notebooks")
CONVERTER = NotebookConverter()

description = """
Notebook2Rest

Modify it, Execute it, Export it.
"""

app = FastAPI(
    title="Notebook2Rest API",
    description=description,
    summary="An app to convert Notebook to REST API",
    version="0.0.1"
)

@app.get("/api/notebooks", summary="Gets all available notebooks")
def get_notebooks():
    with open("file_mapping.json", 'r') as file:
        data = json.load(file)
    return {"notebooks": list(data.keys())}

def get_notebook_file_path(notebook_name: str):
    file_path = NOTEBOOKS_PATH.joinpath(f'{notebook_name}.ipynb')

    if not file_path.is_file():
        raise APIException(f"Notebook [{notebook_name}] file cannot be found.", None, status_code=404)

    return file_path

@app.get("/api/notebooks/{notebook_name}/execute", summary="Executes a notebook",
         responses={
             200: {
                 "content": {
                     "application/x-ipynb+json": {},
                     "application/test": {}
                 }
             }}
         )
def get_results(notebook_name: str, request: Request):
    file_path = get_notebook_file_path(notebook_name)

    accept_header = request.headers.get("Accept", "")

    try:
        if "application/x-ipynb+json" in accept_header:
            out_path = CONVERTER.convert_notebook_to_ipynb(file_path)

            return FileResponse(
                path=out_path,
                filename=out_path.name,
                media_type="application/x-ipynb+json"
            )
        else:
            result = CONVERTER.convert_notebook_to_json(file_path)
            return JSONResponse(content=result)
    except Exception as e:
        raise APIException(
            f"An error occured while executing the [{notebook_name}] notebook.",
            str(e)
        )

@app.get("/api/notebooks/{notebook_name}/cells/{cell_index}/execute", summary="Executes a notebook's cell")
def get_cell_results(notebook_name: str, cell_index:int, request: Request):
    try:
        file_path = get_notebook_file_path(notebook_name)
        return CONVERTER.convert_notebook_cell_to_json(file_path, cell_index)
    except Exception as e:
        raise APIException(
            f"An error occured while executing the [{cell_index}] cell of [{notebook_name}] notebook.",
            str(e)
        )

@app.get("/api/version")
def version():
    return {
        "version": os.getenv("APP_VERSION"),
        "build": os.getenv("BUILD_NUMBER"),
        "date": os.getenv("BUILD_DATE")
    }

class APIException(HTTPException):
    def __init__(self, message: str, details: str, status_code: int = 500):
        self.message = message
        self.details = details
        super().__init__(status_code=status_code)

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error" : {
            "message": exc.message,
            "details": exc.details}
        },
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)