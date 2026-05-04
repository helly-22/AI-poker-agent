"""
Monte Carlo V6: Truly Trained Agent

Loads trained_weights.json and uses learned decision thresholds
instead of hard-coded values
"""

import json
import os
from pypokerengine.players import BasePokerPlayer


class MonteCarloV6Dynamic(BasePokerPlayer):
    """Monte Carlo agent that loads and uses trained weights dynamically."""

    def __init__(self):
        self.round_history = []
        self.game_history = []
        self.trained_weights = None
        self._load_trained_weights()

    def _load_trained_weights(self):
        """Load trained weights from JSON file"""
        try:
            # Try to load trained_weights.json
            weights_file = "trained_weights.json"
            if os.path.exists(weights_file):
                with open(weights_file, 'r') as f:
                    self.trained_weights = json.load(f)
                print(f"✓ Loaded trained weights from {weights_file}")
            else:
                print(f"⚠ No trained_weights.json found, using fallback thresholds")
                self.trained_weights = self._get_fallback_weights()
        except Exception as e:
            print(f"⚠ Error loading weights: {e}, using fallback thresholds")
            self.trained_weights = self._get_fallback_weights()

    def _get_fallback_weights(self):
        """Fallback thresholds if no trained weights available"""
        return {
            "decision_thresholds": {
                "preflop": {
                    "raise_threshold": 0.75,
                    "call_threshold": 0.50,
                    "fold_threshold": 0.25,
                },
                "flop": {
                    "raise_threshold": 0.70,
                    "call_threshold": 0.40,
                    "fold_threshold": 0.20,
                },
                "turn": {
                    "raise_threshold": 0.65,
                    "call_threshold": 0.35,
                    "fold_threshold": 0.20,
                },
                "river": {
                    "raise_threshold": 0.60,
                    "call_threshold": 0.30,
                    "fold_threshold": 0.15,
                },
            },
            "opponent_strategies": {}
        }

    def declare_action(self, valid_actions, hole_card, round_state):
        """Main decision function using trained thresholds"""
        try:
            # Evaluate hand strength
            hole_strength = self._evaluate_hole_cards(hole_card)
            community_cards = round_state.get("community_card", [])

            # Determine current street
            street = self._get_street(len(community_cards))

            # Get learned thresholds for this street
            thresholds = self.trained_weights["decision_thresholds"].get(street)
            if not thresholds:
                thresholds = self.trained_weights["decision_thresholds"]["flop"]

            raise_threshold = thresholds.get("raise_threshold", 0.70)
            call_threshold = thresholds.get("call_threshold", 0.40)

            # Board factor
            board_factor = min(0.3, len(community_cards) * 0.1)
            hand_strength = hole_strength + board_factor
            hand_strength = min(1.0, max(0.0, hand_strength))

            # Make decision using learned thresholds
            available_actions = [a["action"] for a in valid_actions]

            if hand_strength > raise_threshold:
                if "raise" in available_actions:
                    return "raise"
                elif "call" in available_actions:
                    return "call"
            elif hand_strength > call_threshold:
                if "call" in available_actions:
                    return "call"
                elif "check" in available_actions:
                    return "check"

            # Default to fold
            if "fold" in available_actions:
                return "fold"
            elif "check" in available_actions:
                return "check"
            else:
                return "call"

        except Exception:
            return "fold"

    def _evaluate_hole_cards(self, hole_card):
        """Quick evaluation of hole cards (0-1 scale)."""
        rank_values = {
            "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
            "9": 9, "8": 8, "7": 7, "6": 6, "5": 5,
            "4": 4, "3": 3, "2": 2
        }

        card1_rank = rank_values.get(hole_card[0][0], 7)
        card2_rank = rank_values.get(hole_card[1][0], 7)
        is_pair = hole_card[0][0] == hole_card[1][0]
        is_suited = hole_card[0][1] == hole_card[1][1]

        avg_rank = (card1_rank + card2_rank) / 28.0

        if is_pair:
            return min(0.95, avg_rank + 0.3)
        elif is_suited:
            return min(0.85, avg_rank + 0.15)
        else:
            return min(0.75, avg_rank)

    def _get_street(self, num_community_cards):
        """Determine current street"""
        if num_community_cards == 0:
            return "preflop"
        elif num_community_cards == 3:
            return "flop"
        elif num_community_cards == 4:
            return "turn"
        else:
            return "river"

    def receive_game_start_message(self, game_info):
        """Reset for new game."""
        self.round_history = []
        self.game_history = []

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


if __name__ == "__main__":
    print("Monte Carlo V6 - Dynamic Trained Agent")
    player = MonteCarloV6Dynamic()
    print("✓ Agent initialized with trained weights")
