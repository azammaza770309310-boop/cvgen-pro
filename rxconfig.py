import reflex as rx

config = rx.Config(
    app_name="reflex_app",
    backend_port=int(__import__("os").environ.get("PORT", "10000")),
    frontend_port=int(__import__("os").environ.get("PORT", "10000")),
    api_url="",
)
