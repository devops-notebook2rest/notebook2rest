#!/usr/bin/env python3
"""
Executed a Jupyter notebook and
    saves the executed notebook as a new file
    or returns it as a JSON string.
"""
from pathlib import Path

import nbclient
from nbconvert.preprocessors import ExecutePreprocessor, Preprocessor
import nbformat
import json

class NotebookConverter(Preprocessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.preprocessor = ExecutePreprocessor(timeout=600, kernel_name="python3")

    def get_executed_file_path(self, file_path: Path):
        executed_file_name = f"{file_path.stem}-executed{file_path.suffix}"
        return file_path.with_name(executed_file_name)

    def read_notebook(self, path: Path) -> nbformat.NotebookNode:
        with open(path, "r", encoding="utf-8") as f:
            return nbformat.read(f, as_version=4)

    def check_index_validity(self, cell_index: int, notebook: nbformat.NotebookNode):
        notebook_cells_length = len(notebook.cells)
        if cell_index < 0 or cell_index >= notebook_cells_length:
            raise IndexError(f"Cell index [{cell_index}] is out of bounds. This notebook consists of [{notebook_cells_length - 1}] cells.")

    def execute(self, file_path: Path) -> tuple[nbformat.NotebookNode, Path]:
        out_path = self.get_executed_file_path(file_path)

        if out_path.is_file():
            executed_np = self.read_notebook(file_path)
        else:
            notebook_content = self.read_notebook(file_path)
            executed_np, out_resources = self.preprocessor.preprocess(notebook_content)
            nbformat.write(executed_np, out_path)

        return executed_np, out_path

    def execute_cell(self, file_path: Path, cell_index):
        out_path = self.get_executed_file_path(file_path)

        if out_path.is_file():
            executed_np = self.read_notebook(out_path)
            self.check_index_validity(cell_index, executed_np)
            return executed_np.cells[cell_index]
        else:
            notebook_content = self.read_notebook(file_path)
            self.check_index_validity(cell_index, notebook_content)
            notebook_cell = notebook_content.cells[cell_index]
            client = nbclient.NotebookClient(notebook_content, kernel_name="python3")

            with client.setup_kernel():
                executed_cell = client.execute_cell(notebook_cell, cell_index)

            return executed_cell

    def convert_notebook_to_json(self, file_path: Path):
        executed_np = self.execute(file_path)[0]
        executed_np_str = nbformat.writes(executed_np, version=4)
        return json.loads(executed_np_str)

    def convert_notebook_to_ipynb(self, file_path: Path) -> Path:
        return self.execute(file_path)[1]

    def convert_notebook_cell_to_json(self, file_path: Path, cell_index: int):
        executed_cell = self.execute_cell(file_path, cell_index)
        return dict(executed_cell)