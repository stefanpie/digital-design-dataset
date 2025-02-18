import argparse
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Pretty,
    Static,
)


class DigitalDesignDatasetApp(App):
    def __init__(self, dataset_dir: Path) -> None:
        self.dataset_dir = dataset_dir
        super().__init__()

    TITLE = "Digital Design Dataset App"

    CSS_PATH = str((Path(__file__).parent / "style.tcss").resolve())

    @property
    def design_dir(self) -> Path:
        return self.dataset_dir / "designs"

    @property
    def design_names(self) -> list[str]:
        return [design.name for design in self.design_dir.iterdir() if design.is_dir()]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main"):
            with Horizontal(id="dataset_selection"):
                yield Button("Load / Refresh")
                yield Input(placeholder="Dataset Directory", id="dataset_selector")
            with Container(id="dataset_info"):
                yield ListView(
                    *[ListItem(Static(f"{name}")) for name in self.design_names],
                    id="dataset_list",
                )
                with Vertical(id="main_area"):
                    yield Label("Select a design to view its details.", id="design_label")
                    yield Pretty(None, id="design_details")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Digital Design Dataset App")
    parser.add_argument("-d", "--dataset", type=Path, help="Path to the dataset directory")
    args = parser.parse_args()
    app = DigitalDesignDatasetApp(args.dataset)
    app.run()
