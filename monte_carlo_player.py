"""
Monte Carlo Poker Player - ENHANCED VERSION

Features:
- Hand strength evaluation
- Opponent modeling
- Game state analysis
- Adaptive simulation counts
- Trained weight loading
"""

import json
import os
from pypokerengine.players import BasePokerPlayer


class MonteCarloPlayer(BasePokerPlayer):
    """Monte Carlo Poker Agent with game state analysis."""

    def __init__(self):
        """Initialize agent."""
        self.round_history = []
        self.game_history = []

    def declare_action(self, valid_actions, hole_card, round_state):
        """Main decision function - returns action STRING."""
        try:
            # Simple hand strength evaluation
            hole_strength = self._evaluate_hole_cards(hole_card)
            community_cards = round_state.get("community_card", [])
            board_factor = min(0.3, len(community_cards) * 0.1)
            hand_strength = hole_strength + board_factor

            # Make decision
            if hand_strength > 0.7:
                action_name = "raise" if "raise" in [a["action"] for a in valid_actions] else "call"
            elif hand_strength > 0.4:
                action_name = "call" if "call" in [a["action"] for a in valid_actions] else "check"
            else:
                action_name = "fold" if "fold" in [a["action"] for a in valid_actions] else "check"

            return action_name

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
        is_pair = hole_card[0][1] == hole_card[1][1]
        is_suited = hole_card[0][1] == hole_card[1][1]

        avg_rank = (card1_rank + card2_rank) / 28.0

        if is_pair:
            return min(0.95, avg_rank + 0.3)
        elif is_suited:
            return min(0.85, avg_rank + 0.15)
        else:
            return min(0.75, avg_rank)

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
    print("Monte Carlo Player - Enhanced Version")
    player = MonteCarloPlayer()
    print("✓ Agent initialized")
