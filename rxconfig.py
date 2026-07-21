import reflex as rx

config = rx.Config(
    app_name="reflex_app",
    backend_port=8000,
    frontend_port=3001,  # avoid conflict with FastAPI on 3000
    api_url="http://localhost:8000",
)
