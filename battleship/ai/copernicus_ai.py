import numpy as np
from typing import Tuple
from battleship.ai.base_ai import BattleshipAI
from battleship.plate_state_processor import WellState

class CopernicusAI(BattleshipAI):
    """
    Mimics Copernicus: begins at the 'sun' (center) and spirals outward,
    ensuring even coverage of the board.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._spiral = self._generate_spiral()

    def _generate_spiral(self):
        rows, cols = self.board_shape
        center = (rows//2, cols//2)
        directions = [(0,1),(1,0),(0,-1),(-1,0)]
        step, idx, pos = 1, 0, list(center)
        spiral = [tuple(pos)]
        while len(spiral) < rows*cols:
            dr, dc = directions[idx % 4]
            for _ in range(step):
                pos[0] += dr; pos[1] += dc
                if 0 <= pos[0] < rows and 0 <= pos[1] < cols:
                    spiral.append(tuple(pos))
            if idx % 2 == 1:
                step += 1
            idx += 1
        return spiral

    def select_next_move(self) -> Tuple[int, int]:
        for r, c in self._spiral:
            if self.board_state[r, c] == WellState.UNKNOWN:
                return (r, c)
        return (0, 0)
