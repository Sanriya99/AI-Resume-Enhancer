# AI Career Copilot (fixed project copy)

## Run in VS Code on Windows

1. Open this `resume` folder in VS Code.
2. In the terminal, create a fresh virtual environment (do not copy the old `venv`):

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your own `OPENAI_API_KEY`. The app uses local SQLite by default, so you can test signup/login and page navigation before configuring TiDB.
4. Run:

   ```powershell
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

## TiDB Cloud

Set `DATABASE_URL` in `.env` to a SQLAlchemy URL beginning with `mysql+pymysql://` and use your TiDB Cloud host, username, password, database, and required TLS settings. Do not share `.env` or put credentials directly in source code. If your password contains URL-special characters, URL-encode it. The app falls back to local `resume.db` when `DATABASE_URL` is not set.

## Important

This is a learning project. Passwords are currently stored as plain text for compatibility with the original database model; do not deploy it publicly until password hashing, CSRF protection, upload limits, and production configuration are added.
