"""
Monte Carlo V3: Street-Aware Strategy

Different decision thresholds for each street (preflop, flop, turn, river)
"""

from pypokerengine.players import BasePokerPlayer


class MonteCarloV3StreetAware(BasePokerPlayer):
    """Monte Carlo agent with street-specific strategy."""

    def __init__(self):
        self.round_history = []
        self.game_history = []

    def declare_action(self, valid_actions, hole_card, round_state):
        try:
            hole_strength = self._evaluate_hole_cards(hole_card)
            community_cards = round_state.get("community_card", [])

            # Determine current street
            street = self._get_street(len(community_cards))

            # Get thresholds for this street
            raise_threshold, call_threshold = self._get_thresholds(street)

            # Board factor depends on street progress
            if street == "PREFLOP":
                board_factor = 0.0
            elif street == "FLOP":
                board_factor = 0.05
            elif street == "TURN":
                board_factor = 0.08
            else:  # RIVER
                board_factor = 0.10

            hand_strength = hole_strength + board_factor

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

    def _get_street(self, num_community_cards):
        """Determine current street based on community card count"""
        if num_community_cards == 0:
            return "PREFLOP"
        elif num_community_cards == 3:
            return "FLOP"
        elif num_community_cards == 4:
            return "TURN"
        else:
            return "RIVER"

    def _get_thresholds(self, street):
        """Get decision thresholds for each street"""
        if street == "PREFLOP":
            # Preflop: be selective
            raise_threshold = 0.75
            call_threshold = 0.50
        elif street == "FLOP":
            # Flop: moderate aggression
            raise_threshold = 0.70
            call_threshold = 0.40
        elif street == "TURN":
            # Turn: more info available, adjust
            raise_threshold = 0.65
            call_threshold = 0.35
        else:  # RIVER
            # River: be more aggressive (last chance)
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
    print("Monte Carlo V3 - Street-Aware Strategy")
    player = MonteCarloV3StreetAware()
    print("✓ Agent initialized")
