import numpy as np
import random
from battleship.ai.base_ai import BattleshipAI
from battleship.plate_state_processor import WellState
import math

class AlanTuringAI(BattleshipAI):
    """
    Emulates Turing's logic: minimizes uncertainty by checking parity and
    selecting the cell that maximizes expected information gain.
    """
    def select_next_move(self):
        rows, cols = self.board_shape
        # Precompute Shannon entropy for each UNKNOWN cell based on possible ship fits
        scores = np.zeros((rows, cols))
        for r in range(rows):
            for c in range(cols):
                if self.board_state[r, c] != WellState.UNKNOWN:
                    scores[r, c] = -1
                    continue
                # Estimate probability distribution of hit/miss given neighbor states
                neighbors = self._get_neighbors(r, c)
                p_hit = sum(1 for nr,nc in neighbors if self.board_state[nr,nc]==WellState.HIT) / max(1, len(neighbors))
                # Shannon entropy
                scores[r, c] = -(p_hit * math.log2(p_hit+1e-6) + (1-p_hit)*math.log2((1-p_hit)+1e-6))
        # Choose max entropy cell (most uncertain)
        max_idx = np.unravel_index(np.argmax(scores), scores.shape)
        return tuple(max_idx)

    def _get_neighbors(self, r, c):
        return [(r+dr, c+dc) for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]
                if 0<=r+dr<self.board_shape[0] and 0<=c+dc<self.board_shape[1]]
