import json
import importlib
import inspect
import pkgutil
import random
from pathlib import Path
from typing import Any, Dict, Tuple, Type, List
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from battleship.ai.base_ai import BattleshipAI
from battleship.ai.random_ai import RandomAI
from battleship.ai.go_wrapper import GoWrapperAI
from battleship.plate_state_processor import WellState
from battleship.placement_ai.random_placement_ai import RandomPlacementAI
from battleship.placement_utils import validate_placement_schema, coords_from_schema


def discover_ai_classes() -> Dict[str, Type[BattleshipAI]]:
    """Discover all available AI classes including Go executables."""
    classes: Dict[str, Type[BattleshipAI]] = {"RandomAI": RandomAI}
    ai_module_path = Path(__file__).resolve().parent / "ai"

    for _, module_name, _ in pkgutil.iter_modules([str(ai_module_path)]):
        if module_name in {"base_ai", "go_wrapper"}:
            continue
        module = importlib.import_module(f"battleship.ai.{module_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BattleshipAI) and obj is not BattleshipAI:
                classes[name] = obj

    go_dir = ai_module_path / "go_ais"
    if go_dir.exists():
        for exe in go_dir.glob("*.exe"):
            exe_path = str(exe)
            name = exe.stem

            class _GoExeAI(GoWrapperAI):
                def __init__(self, player_id: str, board_shape: Tuple[int, int], ship_schema: Dict[str, Any], _path: str = exe_path) -> None:
                    super().__init__(player_id, board_shape, ship_schema, go_executable=_path)

            _GoExeAI.__name__ = name
            classes[name] = _GoExeAI

    return classes


def load_config() -> Tuple[Tuple[int, int], Dict[str, Any]]:
    cfg_path = Path(__file__).resolve().parent / "configuration.json"
    with open(cfg_path, "r") as f:
        cfg = json.load(f)
    board_shape = (cfg["plate_schema"]["rows"], cfg["plate_schema"]["columns"])
    ship_schema = cfg["ship_schema"]
    return board_shape, ship_schema


def generate_valid_placement(board_shape: Tuple[int, int], ship_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    placer = RandomPlacementAI(board_shape, ship_schema)
    for _ in range(100):
        placement = placer.generate_placement()
        if validate_placement_schema(placement, board_shape, ship_schema):
            return placement
    raise RuntimeError("Unable to generate valid placement")


def simulate_game(ai1_cls: Type[BattleshipAI], ai2_cls: Type[BattleshipAI], board_shape: Tuple[int, int], ship_schema: Dict[str, Any]) -> str:
    ai1 = ai1_cls("player_1", board_shape, ship_schema)
    ai2 = ai2_cls("player_2", board_shape, ship_schema)

    placement1 = generate_valid_placement(board_shape, ship_schema)
    placement2 = generate_valid_placement(board_shape, ship_schema)

    ship_coords = {
        "player_1": set(coords_from_schema(placement1)),
        "player_2": set(coords_from_schema(placement2)),
    }
    players = {"player_1": ai1, "player_2": ai2}

    current = "player_1"
    while True:
        ai = players[current]
        opponent = "player_2" if current == "player_1" else "player_1"
        move = ai.select_next_move()
        r, c = move
        if not (0 <= r < board_shape[0] and 0 <= c < board_shape[1]) or ai.board_state[r, c] != WellState.UNKNOWN:
            print(f"Invalid move by {ai.__class__.__name__}: {move}. Retrying...")
            if not (0 <= r < board_shape[0] and 0 <= c < board_shape[1]):
                print(f"Move {move} is out of bounds for {current}.")
            if ai.board_state[r, c] != WellState.UNKNOWN:
                print(f"Move {move} has state {ai.board_state[r, c]}, not UNKNOWN.")
            unknowns = [(rr, cc) for rr in range(board_shape[0]) for cc in range(board_shape[1]) if ai.board_state[rr, cc] == WellState.UNKNOWN]
            move = random.choice(unknowns) if unknowns else (0, 0)
        result = WellState.HIT if move in ship_coords[opponent] else WellState.MISS
        ai.record_shot_result(move, result)
        if ai.has_won():
            return current
        current = opponent


def simulate_series(ai1_cls: Type[BattleshipAI], ai2_cls: Type[BattleshipAI], board_shape: Tuple[int, int], ship_schema: Dict[str, Any], games: int = 50) -> Dict[str, float]:
    wins = {ai1_cls.__name__: 0, ai2_cls.__name__: 0}
    for i in range(games):
        if i % 2 == 0:
            winner = simulate_game(ai1_cls, ai2_cls, board_shape, ship_schema)
            winner_name = ai1_cls.__name__ if winner == "player_1" else ai2_cls.__name__
        else:
            winner = simulate_game(ai2_cls, ai1_cls, board_shape, ship_schema)
            winner_name = ai1_cls.__name__ if winner == "player_2" else ai2_cls.__name__
        wins[winner_name] += 1
        print(f"Game {i + 1}: {winner_name} wins!")
    total = sum(wins.values())
    return {k: v / total for k, v in wins.items()}


def simulate_all_vs_all(games: int = 50) -> Dict[Tuple[str, str], Dict[str, float]]:
    board_shape, ship_schema = load_config()
    ai_classes = discover_ai_classes()

    # Uncomment the following lines to investigate specific AI classes
    #from battleship.ai.random_ai import RandomAI
    #from battleship.ai.A5_heatmap_ai import A5_HeatmapBattleshipAI
    #ai_classes = {
    #    "RandomAI": RandomAI,
    #    "A5_HeatmapBattleshipAI": A5_HeatmapBattleshipAI
    #}
    names = list(ai_classes.keys())
    results: Dict[Tuple[str, str], Dict[str, float]] = {}
    for i, name1 in enumerate(names):
        for name2 in names[i + 1:]:
            print(f"Simulating {name1} vs {name2}...")
            wins = simulate_series(ai_classes[name1], ai_classes[name2], board_shape, ship_schema, games=games)
            results[(name1, name2)] = wins
    return results


if __name__ == "__main__":
    res = simulate_all_vs_all(games=500)
    for pair, odds in res.items():
        print(f"{pair[0]} vs {pair[1]}: {odds}")

    # Show a confusion matrix
    import seaborn as sns
    import numpy as np
    import matplotlib.pyplot as plt
    names = list(set(name for pair in res.keys() for name in pair))
    matrix = np.zeros((len(names), len(names)))

    for (name1, name2), odds in res.items():
        i1 = names.index(name1)
        i2 = names.index(name2)
        matrix[i1, i2] = odds.get(name1, 0)
        matrix[i2, i1] = odds.get(name2, 0)

    # Sort the matrix so that the highest average win probability is in the top left
    sorted_indices = np.argsort(-np.mean(matrix, axis=1))
    matrix = matrix[sorted_indices][:, sorted_indices]
    names = [names[i] for i in sorted_indices]

    sns.heatmap(matrix, annot=True, xticklabels=names, yticklabels=names, cmap="Blues")
    plt.title("Confusion Matrix of AI Win Probabilities")
    plt.xlabel("AI Players")
    plt.ylabel("AI Players")
    plt.show()
