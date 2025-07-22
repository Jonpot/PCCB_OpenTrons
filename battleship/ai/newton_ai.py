import numpy as np
from typing import Tuple
from battleship.ai.base_ai import BattleshipAI
from battleship.plate_state_processor import WellState

class IsaacNewtonAI(BattleshipAI):
    """
    Applies a 'gravitational' model: past hits attract future shots
    with force ∝ 1/distance^2.
    """
    def select_next_move(self) -> Tuple[int, int]:
        rows, cols = self.board_shape
        prob = np.zeros((rows, cols), dtype=float)
        hits = np.argwhere(self.board_state == WellState.HIT)
        for r in range(rows):
            for c in range(cols):
                if self.board_state[r, c] != WellState.UNKNOWN:
                    continue
                # Sum inverse-square attraction from each hit
                prob[r, c] = sum(1.0 / ((r - hr)**2 + (c - hc)**2 + 1)
                                 for hr, hc in hits)
        # Select the highest 'gravitational' cell
        max_idx = np.unravel_index(np.argmax(prob), prob.shape)
        return tuple(max_idx if prob.max() > 0 else np.argwhere(self.board_state==WellState.UNKNOWN)[0])
