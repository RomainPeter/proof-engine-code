import typer
from .ambition import ambition_app

app = typer.Typer(help="Proof Engine Companion CLI (Ambition Intake v0)")
app.add_typer(ambition_app, name="ambition", help="Gérer l'ambition: init, validate, compile")

if __name__ == "__main__":
    app()

