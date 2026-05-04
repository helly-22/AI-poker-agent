"""
Monte Carlo V2: Board Texture Abstraction

Adjusts strategy based on board wetness (high card, pair, flush draw potential)
"""

import random
from pypokerengine.players import BasePokerPlayer


class MonteCarloV2BoardTexture(BasePokerPlayer):
    """Monte Carlo agent with board texture adaptation."""

    def __init__(self):
        self.round_history = []
        self.game_history = []

    def declare_action(self, valid_actions, hole_card, round_state):
        try:
            hole_strength = self._evaluate_hole_cards(hole_card)
            community_cards = round_state.get("community_card", [])

            # Detect board texture and adjust strategy
            board_texture = self._get_board_texture(community_cards)
            texture_adjustment = self._get_texture_adjustment(board_texture)

            # Combine strength with texture adjustment
            hand_strength = hole_strength + (0.1 * texture_adjustment)
            hand_strength = min(1.0, max(0.0, hand_strength))

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
        is_pair = hole_card[0][0] == hole_card[1][0]
        is_suited = hole_card[0][1] == hole_card[1][1]

        avg_rank = (card1_rank + card2_rank) / 28.0

        if is_pair:
            return min(0.95, avg_rank + 0.3)
        elif is_suited:
            return min(0.85, avg_rank + 0.15)
        else:
            return min(0.75, avg_rank)

    def _get_board_texture(self, community_cards):
        """Classify board as WET, MEDIUM, or DRY"""
        if not community_cards:
            return "PREFLOP"

        ranks = [card[0] for card in community_cards]
        suits = [card[1] for card in community_cards]

        rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
                      '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        rank_vals = [rank_order.get(r, 7) for r in ranks]

        high_cards = sum(1 for r in rank_vals if r >= 10)
        pairs = len(rank_vals) - len(set(rank_vals))
        max_suit_count = max([suits.count(s) for s in suits])

        wet_score = high_cards + (pairs * 2) + (max_suit_count - 1)

        if wet_score >= 3:
            return "WET"
        elif wet_score >= 1:
            return "MEDIUM"
        else:
            return "DRY"

    def _get_texture_adjustment(self, texture):
        """Adjust aggression based on board texture"""
        if texture == "PREFLOP":
            return 0.0
        elif texture == "WET":
            return 0.05  # Slightly more aggressive on wet boards
        elif texture == "MEDIUM":
            return 0.0   # Neutral
        else:  # DRY
            return -0.05  # Slightly more conservative on dry boards

    def receive_game_start_message(self, game_info):
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
    print("Monte Carlo V2 - Board Texture Abstraction")
    player = MonteCarloV2BoardTexture()
    print("✓ Agent initialized")
