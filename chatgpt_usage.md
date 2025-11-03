# AI Usage Transparency Note

[cite_start]As encouraged by the assignment guidelines[cite: 50], AI assistance (Google Gemini) was used to support the development of this project.

The primary uses included:

1.  **Initial Planning & Tech Stack:** Brainstorming a rapid development plan to meet the tight deadline. [cite_start]AI helped recommend a suitable, fast-to-implement tech stack (Python, `websockets`, `SQLite`, and `Streamlit`) that would meet all core project requirements[cite: 7, 22, 23].

2.  **Code Generation:** Generating the initial skeleton code for:
    * [cite_start]The `ingest.py` script to connect to the Binance WebSocket and store data in SQLite[cite: 13].
    * [cite_start]The `app.py` Streamlit dashboard, including data loading, resampling logic [cite: 14][cite_start], and UI layout[cite: 22, 24].

3.  **Debugging & Error Resolution:** Assisting in debugging runtime errors encountered during development, specifically:
    * Resolving a `pandas.to_datetime` format error.
    * Fixing a `ValueError: cannot reindex on an axis with duplicate labels` by adding logic to handle duplicate timestamps.
    * [cite_start]Correcting multiple `StreamlitAPIException` and `SchemaValidationError` errors in the Altair charting code to correctly display alert thresholds[cite: 19].

4.  [cite_start]**Documentation:** Generating the templates and content structure for the `README.md` and this usage note, ensuring all deliverables were addressed[cite: 41, 42].