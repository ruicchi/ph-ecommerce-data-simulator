# ADR 0001: Decouple Data Orchestration from Generation via Explicit Seams

## Status
Accepted

## Context
The domain generator modules (`orders.py`, `order_items.py`, `events.py`) previously accepted massive, raw `pandas.DataFrame` objects (like `df_events`, `df_sessions`, `df_users`). The modules then performed their own complex `.merge()` operations internally to extract a few necessary columns. 

This resulted in shallow modules with significant leakage across seams:
- **Tight Coupling**: Domain logic was tangled with relational data orchestration. Changing a column name in `users.py` could break four other files.
- **Poor Locality**: To understand the data dependencies of a generation function, one had to read through its internal pandas `.merge()` boilerplate.
- **Hard to Test**: Testing domain logic required passing entire mocked relational tables rather than simple arrays of inputs.

## Decision
We will establish a strict architectural seam between data orchestration and domain generation. 

- **The Orchestrator (`main.py`)**: Responsible for all relational `.merge()` operations and data preparation. It will extract specific columns into typed dictionaries of NumPy arrays. Private adapter functions (e.g., `_prepare_purchases`) will encapsulate this logic.
- **The Domain Generators (`src/*.py`)**: The generator modules will shrink their interfaces to accept *only* a flat `dict[str, np.ndarray]` containing exactly the columns required for their specific business logic. They will not accept raw `DataFrame` objects or perform relational joins.

## Consequences

### Positive
- **Locality**: A module's exact data dependencies are instantly visible in its signature.
- **Leverage**: Testing domain logic becomes trivial as tests only need to provide simple dictionaries of numpy arrays, without mocking complex relational state.
- **Cohesion**: Domain modules are now purely focused on simulation logic, while `main.py` is purely focused on execution orchestration.

### Negative
- **Verbosity in Orchestrator**: `main.py` will grow slightly larger as it absorbs the orchestration adapter functions.
- **Data Conversion Overhead**: There is a small theoretical cost to extracting `numpy` arrays from `pandas` into dictionaries, though this is negligible in the context of the vectorized simulation.