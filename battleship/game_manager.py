import time
from typing import Dict
from string import ascii_uppercase
from battleship.ai.base_ai import BattleshipAI
from battleship.ai.random_ai import RandomAI
from battleship.robot.ot2_utils import OT2Manager
from battleship.plate_state_processor import DualPlateStateProcessor  # A new processor for two plates
from typing import Any, List
import random
from battleship.plate_state_processor import WellState
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

class BattleshipGame:
    """Manages a competitive game of Battleship between two AI players."""

    def __init__(self,
                 player_1_ai: BattleshipAI,
                 player_2_ai: BattleshipAI,
                 plate_processor: DualPlateStateProcessor,
                 robot: OT2Manager):
        self.players = {'player_1': player_1_ai, 'player_2': player_2_ai}
        self.plate_processor = plate_processor
        self.robot = robot
        self.history: List[Dict[str, Any]] = []

        # Track how many times each player's AI attempted an invalid move
        self.invalid_move_counts = {'player_1': 0, 'player_2': 0}

        self.backup_random_ai = RandomAI('backup_random_ai', board_shape=player_1_ai.board_shape, ship_schema=player_1_ai.ship_schema)

    def _recheck_previous_shots(self, player_id: str, count: int = 5) -> None:
        """Reassess the last ``count`` shots for ``player_id`` using the camera."""
        ai = self.players[player_id]
        plate_id = 2 if player_id == 'player_1' else 1
        # Gather all shots for the player
        player_history = [h for h in self.history if h['player'] == player_id]
        if len(player_history) <= 1:
            return
        # Exclude the most recent entry (the current move)
        to_check = player_history[-(count + 1):-1]
        for entry in to_check:
            row = ascii_uppercase.index(entry['move'][0])
            col = int(entry['move'][1:]) - 1
            try:
                new_state = self.plate_processor.determine_well_state(
                    plate_id=plate_id, well=(row, col)
                )
            except RuntimeError:
                continue
            current_state = ai.board_state[row, col]
            if new_state != current_state:
                # Temporarily mark as unknown so AI update method works
                ai.board_state[row, col] = WellState.UNKNOWN
                ai.record_shot_result((row, col), new_state)
                entry['result'] = new_state.name

    def run_game_live(self):
        """
        Main game loop that yields the game state after each individual move.
        This is designed for use with live front-end updates.
        """
        print("--- BATTLESHIP COMPETITION START (LIVE) ---")
        print(f"Player 1: {self.players['player_1'].__class__.__name__}")
        print(f"Player 2: {self.players['player_2'].__class__.__name__}")
        print("------------------------------------")

        turn = 0
        while True:
            turn += 1
            
            for player_id in ['player_1', 'player_2']:
                ai = self.players[player_id]
                
                # 1. Get move from the current player's AI with a 3 second timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(ai.select_next_move)
                    try:
                        move = future.result(timeout=3)
                    except FuturesTimeoutError:
                        print(f"Warning: {player_id} AI timed out. Using backup random AI to select a valid move.")
                        move = None

                # 1b. Validate the move. If it's invalid or missing, use the backup AI
                if (
                    move is None
                    or not isinstance(move, tuple)
                    or len(move) != 2
                    or not (0 <= move[0] < ai.board_shape[0] and 0 <= move[1] < ai.board_shape[1])
                    or self.players[player_id].board_state[move] != WellState.UNKNOWN
                ):
                    if move is not None:
                        print(f"Warning: {player_id} attempted to fire at an invalid well {move}. Using backup random AI to select a valid move.")
                    move = self.backup_random_ai.select_next_move()
                    self.invalid_move_counts[player_id] += 1

                # 2. Fire the missile on the physical plate
                well_name = f"{ascii_uppercase[move[0]]}{move[1] + 1}"
                print(f"Turn {turn}, {player_id}: Firing at {well_name}...")
                self.robot.add_fire_missile_action(plate_idx=2 if player_id == 'player_1' else 1, plate_well=well_name)
                self.robot.execute_actions_on_remote()

                # 2.5 Wait for the chemical reaction to complete
                time.sleep(5)  # Wait for the reaction to complete, adjust as necessary

                # 3. Determine the result from the camera
                try:
                    result = self.plate_processor.determine_well_state(plate_id=2 if player_id == 'player_1' else 1, well=move)
                except RuntimeError:
                    # Probably in virtual mode, return a random result
                    result = random.choice([WellState.MISS, WellState.HIT])
                print(f"Result: {result.name}!")
                
                # 4. Update the AI with the result and log history
                ai.record_shot_result(move, result)
                self.history.append({
                    'turn': turn,
                    'player': player_id,
                    'move': well_name,
                    'result': result.name
                })
                # Re-check the previous shots to account for delayed reactions
                self._recheck_previous_shots(player_id, count=5)

                # 5. Yield the complete current state for the UI
                current_state = {
                    'turn': turn,
                    'active_player': player_id,
                    'move': well_name,
                    'result': result.name,
                    'board_p1': self.players['player_1'].board_state,
                    'board_p2': self.players['player_2'].board_state,
                    'history': self.history,
                    'winner': None,
                    'invalid_move_counts': dict(self.invalid_move_counts)
                }
                yield current_state

                # 6. Check for a winner
                if ai.has_won():
                    print(f"\n--- GAME OVER ---")
                    print(f"🎉 {player_id} ({ai.__class__.__name__}) has sunk all ships and wins in {turn} turns! 🎉")
                    self.robot.add_end_game_action()
                    self.robot.execute_actions_on_remote()
                    current_state['winner'] = player_id
                    yield current_state
                    return # End the generator
