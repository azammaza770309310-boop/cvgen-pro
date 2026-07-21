import os
import reflex as rx

_port = os.environ.get("PORT", "10000")

config = rx.Config(
    app_name="reflex_app",
    backend_port=int(_port),
    frontend_port=int(_port),
    api_url=f"http://0.0.0.0:{_port}",
)
