# Domain Context

## Glossary

- **Orchestration Adapter**: A private function in `main.py` (e.g., `_prepare_purchases`) responsible for joining relational DataFrames and flattening them into dictionaries of NumPy arrays before passing them across a seam.
- **Generator Seam**: The architectural boundary between data preparation (in `main.py`) and domain logic (in `src/*.py`). Data crossing this seam must be a flat `dict[str, np.ndarray]`, never a `pandas.DataFrame`.