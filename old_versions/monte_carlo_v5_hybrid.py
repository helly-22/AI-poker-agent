"""
Monte Carlo V5: Hybrid Approach

Baseline agent + simple board texture + street awareness
Combines the best of multiple abstractions
"""

from pypokerengine.players import BasePokerPlayer


class MonteCarloV5Hybrid(BasePokerPlayer):
    """Monte Carlo agent with hybrid abstraction strategy."""

    def __init__(self):
        self.round_history = []
        self.game_history = []

    def declare_action(self, valid_actions, hole_card, round_state):
        try:
            # Step 1: Basic hand strength
            hole_strength = self._evaluate_hole_cards(hole_card)
            community_cards = round_state.get("community_card", [])

            # Step 2: Board texture adjustment
            board_texture = self._get_board_texture(community_cards)
            texture_bonus = self._get_texture_bonus(board_texture)

            # Step 3: Street-aware adjustment
            street = self._get_street(len(community_cards))
            street_bonus = self._get_street_bonus(street)

            # Step 4: Combine all factors
            board_factor = min(0.3, len(community_cards) * 0.1)
            hand_strength = hole_strength + board_factor + texture_bonus + street_bonus
            hand_strength = min(1.0, max(0.0, hand_strength))

            # Step 5: Make decision with street-aware thresholds
            raise_threshold, call_threshold = self._get_thresholds(street)

            if hand_strength > raise_threshold:
                action_name = "raise" if "raise" in [a["action"] for a in valid_actions] else "call"
            elif hand_strength > call_threshold:
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

        wet_score = high_cards + (pairs * 2)

        if wet_score >= 3:
            return "WET"
        elif wet_score >= 1:
            return "MEDIUM"
        else:
            return "DRY"

    def _get_texture_bonus(self, texture):
        """Bonus/penalty based on board texture"""
        if texture == "PREFLOP":
            return 0.0
        elif texture == "WET":
            return 0.05  # More confident with draws available
        elif texture == "MEDIUM":
            return 0.02
        else:  # DRY
            return -0.02

    def _get_street(self, num_community_cards):
        """Determine current street"""
        if num_community_cards == 0:
            return "PREFLOP"
        elif num_community_cards == 3:
            return "FLOP"
        elif num_community_cards == 4:
            return "TURN"
        else:
            return "RIVER"

    def _get_street_bonus(self, street):
        """Bonus based on street progress"""
        if street == "PREFLOP":
            return 0.0
        elif street == "FLOP":
            return 0.02
        elif street == "TURN":
            return 0.03
        else:  # RIVER
            return 0.05

    def _get_thresholds(self, street):
        """Street-aware decision thresholds"""
        if street == "PREFLOP":
            raise_threshold = 0.75
            call_threshold = 0.50
        elif street == "FLOP":
            raise_threshold = 0.70
            call_threshold = 0.40
        elif street == "TURN":
            raise_threshold = 0.65
            call_threshold = 0.35
        else:  # RIVER
            raise_threshold = 0.60
            call_threshold = 0.30

        return raise_threshold, call_threshold

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
    print("Monte Carlo V5 - Hybrid Strategy")
    player = MonteCarloV5Hybrid()
    print("✓ Agent initialized")
