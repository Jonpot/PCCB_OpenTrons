import numpy as np
import random
from typing import Tuple
from battleship.ai.base_ai import BattleshipAI
from battleship.plate_state_processor import WellState

class JoshKangasAI(BattleshipAI):
    """
    Follows a two-phase 'education protocol': a broad initial sweep
    (grid sampling) followed by targeted refinement (adjacent hits).
    """
    def select_next_move(self) -> Tuple[int, int]:
        # Phase 1: Broad grid sampling like a 4-row cycle
        rows, cols = self.board_shape
        unknowns = np.argwhere(self.board_state == WellState.UNKNOWN)
        # cycle stride of 4 for balanced coverage
        cycle = [(r + c) % 4 for r, c in unknowns]
        for phase in [0, 1, 2, 3]:
            phase_cells = unknowns[cycle == phase]
            if phase_cells.size:
                # pick random to mimic stochastic lab sampling
                return tuple(phase_cells[random.randrange(len(phase_cells))])
        # If all phases exhausted, fallback
        return tuple(unknowns[0])

