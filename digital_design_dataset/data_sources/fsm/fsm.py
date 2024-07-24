class State:
    def __init__(self, name: str, output_assignments: dict):
        self.name = name

    def __repr__(self) -> str:
        return f"State({self.name})"


class Alphabet:
    def __init__(self, symbols: list[str]):
        self.symbols = symbols

    def __repr__(self):
        return f"Alphabet({self.symbols})"


class Transistion:
    def __init__(self, source: str, target: str, symbol: str):
        self.source = source
        self.target = target
        self.symbol = symbol

    def __repr__(self):
        return f"Transistion({self.source}, {self.target}, {self.symbol})"


class Transitions:
    def __init__(self, transitions: list[Transistion]):
        self.transitions = transitions

    def __repr__(self):
        return f"Transitions({self.transitions})"


class Output:
    def __init__(self, name: str, size: int, inital_value: str | None = None): ...


class FSM:
    def __init__(
        self,
        states: list[State],
        start_state: State,
        input_alphabet: Alphabet,
        output_alphabet: Alphabet,
        transitions: Transitions,
        outputs: list[Output],
    ): ...
