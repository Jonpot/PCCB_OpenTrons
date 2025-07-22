import numpy as np
import random
from typing import Tuple, List
from battleship.ai.base_ai import BattleshipAI
from battleship.plate_state_processor import WellState
from sklearn.cluster import DBSCAN

class SunTzuAI(BattleshipAI):
    """
    Employs a hunt-and-ambush strategy: targets adjacent to hits first (ambush),
    then softly weights the rest, reflecting Sun Tzu's emphasis on surprise.
    """
    def select_next_move(self) -> Tuple[int, int]:
        # Ambush: clusters of hits
        hits = np.argwhere(self.board_state == WellState.HIT)
        if hits.any():
            clustering = DBSCAN(eps=1.1, min_samples=1).fit(hits)
            targets = set()
            for label in set(clustering.labels_):
                cluster = hits[clustering.labels_ == label]
                for r, c in cluster:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0<=nr<self.board_shape[0] and 0<=nc<self.board_shape[1] \
                           and self.board_state[nr, nc] == WellState.UNKNOWN:
                            targets.add((nr, nc))
            if targets:
                return random.choice(list(targets))

        # Else: softened probability map
        prob = self._calculate_probability_map()
        # invert to reflect 'stealth'—lower prob is more unexpected
        prob[prob >= 0] = prob.max() - prob[prob >= 0]
        idx = np.unravel_index(np.argmax(prob), prob.shape)
        return tuple(idx)

    def _calculate_probability_map(self) -> np.ndarray:
        rows, cols = self.board_shape
        pm = np.zeros((rows, cols), dtype=int)
        lengths = [ship["length"] for ship in self.ship_schema.values()
                   for _ in range(ship["count"])]
        for L in lengths:
            for r in range(rows):
                for c in range(cols - L + 1):
                    if all(self.board_state[r, c+i] != WellState.MISS for i in range(L)):
                        for i in range(L): pm[r, c+i] += 1
            for r in range(rows - L + 1):
                for c in range(cols):
                    if all(self.board_state[r+i, c] != WellState.MISS for i in range(L)):
                        for i in range(L): pm[r+i, c] += 1
        pm[self.board_state != WellState.UNKNOWN] = -1
        return pm
