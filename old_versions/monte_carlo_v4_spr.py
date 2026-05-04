"""
Monte Carlo V4: Stack-to-Pot Ratio (SPR) Strategy

Adjusts decisions based on effective stack depth relative to pot
"""

from pypokerengine.players import BasePokerPlayer


class MonteCarloV4SPR(BasePokerPlayer):
    """Monte Carlo agent with SPR-based strategy."""

    def __init__(self):
        self.round_history = []
        self.game_history = []

    def declare_action(self, valid_actions, hole_card, round_state):
        try:
            hole_strength = self._evaluate_hole_cards(hole_card)
            community_cards = round_state.get("community_card", [])

            # Calculate SPR (Stack-to-Pot Ratio)
            spr = self._calculate_spr(round_state)

            # Adjust thresholds based on SPR
            raise_threshold, call_threshold = self._get_spr_adjusted_thresholds(spr)

            # Board factor
            board_factor = min(0.3, len(community_cards) * 0.1)
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

    def _calculate_spr(self, round_state):
        """
        Calculate Stack-to-Pot Ratio
        SPR = effective_stack / pot
        """
        try:
            # Get pot size
            pot = round_state.get("pot", {}).get("main", {}).get("amount", 100)

            # Get your stack (approximate - this is simplified)
            # In a real implementation, you'd track your actual stack
            effective_stack = 1000  # Default assumption

            spr = effective_stack / max(pot, 1)
            return spr

        except Exception:
            return 10.0  # Default: deep stacks

    def _get_spr_adjusted_thresholds(self, spr):
        """
        Adjust thresholds based on SPR:
        - High SPR (>10): Deep stacks, can be selective
        - Medium SPR (3-10): Balanced play
        - Low SPR (<3): Short stacks, play wide
        """
        if spr > 10:
            # Deep stacks: be tight preflop, looser postflop
            raise_threshold = 0.75
            call_threshold = 0.50
        elif spr > 5:
            # Medium-deep: balanced
            raise_threshold = 0.70
            call_threshold = 0.40
        elif spr > 3:
            # Medium-short: start playing more
            raise_threshold = 0.65
            call_threshold = 0.35
        else:
            # Short stacks: play very wide
            raise_threshold = 0.50
            call_threshold = 0.25

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
    print("Monte Carlo V4 - SPR Strategy")
    player = MonteCarloV4SPR()
    print("✓ Agent initialized")
