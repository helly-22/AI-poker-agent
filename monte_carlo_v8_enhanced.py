"""
Monte Carlo V8: V6 Enhanced with Pot Odds and SPR

Minimal enhancement to V6:
- Adds pot odds adjustment (fundamental poker concept)
- Adds SPR (Stack-to-Pot Ratio) adjustment
- Still loads trained_weights.json for thresholds
- Keeps everything else simple
"""

import json
import os
from pypokerengine.players import BasePokerPlayer


class MonteCarloV8Enhanced(BasePokerPlayer):
    """V6 enhanced with pot odds and SPR adjustments."""

    def __init__(self):
        self.round_history = []
        self.game_history = []
        self.trained_weights = None
        self._load_trained_weights()

    def _load_trained_weights(self):
        """Load trained weights from JSON file"""
        try:
            weights_file = "trained_weights.json"
            if os.path.exists(weights_file):
                with open(weights_file, 'r') as f:
                    self.trained_weights = json.load(f)
            else:
                self.trained_weights = self._get_fallback_weights()
        except Exception:
            self.trained_weights = self._get_fallback_weights()

    def _get_fallback_weights(self):
        """Fallback thresholds if no trained weights available"""
        return {
            "decision_thresholds": {
                "preflop": {"raise_threshold": 0.75, "call_threshold": 0.50},
                "flop": {"raise_threshold": 0.70, "call_threshold": 0.40},
                "turn": {"raise_threshold": 0.65, "call_threshold": 0.35},
                "river": {"raise_threshold": 0.60, "call_threshold": 0.30},
            }
        }

    def declare_action(self, valid_actions, hole_card, round_state):
        """Decision with pot odds and SPR adjustments"""
        try:
            # Step 1: Base hand strength (from V6)
            hand_strength = self._evaluate_hand(hole_card, round_state)

            # Step 2: Pot odds adjustment
            pot_odds_adjustment = self._calculate_pot_odds_adjustment(round_state, valid_actions)

            # Step 3: SPR adjustment
            spr_adjustment = self._calculate_spr_adjustment(round_state)

            # Combine: hand strength + adjustments
            # Pot odds and SPR are relatively minor adjustments
            adjusted_strength = hand_strength + (pot_odds_adjustment * 0.10) + (spr_adjustment * 0.08)
            adjusted_strength = min(1.0, max(0.0, adjusted_strength))

            # Get street-specific thresholds from trained weights
            street = self._get_street(len(round_state.get("community_card", [])))
            thresholds = self.trained_weights["decision_thresholds"].get(street,
                                                    self.trained_weights["decision_thresholds"]["flop"])

            raise_threshold = thresholds.get("raise_threshold", 0.70)
            call_threshold = thresholds.get("call_threshold", 0.40)

            # Make decision
            available_actions = [a["action"] for a in valid_actions]

            if adjusted_strength > raise_threshold:
                if "raise" in available_actions:
                    return "raise"
                elif "call" in available_actions:
                    return "call"
            elif adjusted_strength > call_threshold:
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

    def _evaluate_hand(self, hole_card, round_state):
        """Hand strength evaluation (from V6)"""
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
            base_strength = min(0.95, avg_rank + 0.3)
        elif is_suited:
            base_strength = min(0.85, avg_rank + 0.15)
        else:
            base_strength = min(0.75, avg_rank)

        # Board progression bonus
        community_cards = round_state.get("community_card", [])
        board_bonus = min(0.3, len(community_cards) * 0.1)

        return min(1.0, base_strength + board_bonus)

    def _calculate_pot_odds_adjustment(self, round_state, valid_actions):
        """
        Pot odds adjustment: -0.1 to +0.1

        Good pot odds (cheap to call) = positive adjustment (more likely to call/raise)
        Bad pot odds (expensive to call) = negative adjustment (more likely to fold)

        Simplified: pot_odds_ratio = pot_size / bet_amount
        High ratio = good odds = +adjustment
        Low ratio = bad odds = -adjustment
        """
        try:
            pot_amount = round_state.get("pot", {}).get("main", {}).get("amount", 100)

            # Find bet amount
            bet_amount = 0
            for action in valid_actions:
                if action["action"] == "call":
                    bet_amount = action.get("amount", 0)
                    break

            if bet_amount == 0:
                return 0.0  # No bet, no adjustment

            # Pot odds ratio: high ratio is good odds
            pot_odds_ratio = pot_amount / max(bet_amount, 1)

            # Convert ratio to adjustment (-0.1 to +0.1 range)
            # Ratio 1:1 = 0.0, Ratio 3:1 = +0.08, Ratio 0.5:1 = -0.05
            if pot_odds_ratio >= 3:
                adjustment = 0.10  # Excellent odds
            elif pot_odds_ratio >= 2:
                adjustment = 0.08  # Good odds
            elif pot_odds_ratio >= 1.5:
                adjustment = 0.05  # Decent odds
            elif pot_odds_ratio >= 1:
                adjustment = 0.02  # Fair odds
            elif pot_odds_ratio >= 0.67:
                adjustment = -0.02  # Poor odds
            elif pot_odds_ratio >= 0.5:
                adjustment = -0.05  # Bad odds
            else:
                adjustment = -0.10  # Terrible odds

            return adjustment

        except Exception:
            return 0.0

    def _calculate_spr_adjustment(self, round_state):
        """
        SPR (Stack-to-Pot Ratio) adjustment: -0.08 to +0.08

        SPR = effective_stack / pot
        High SPR (>10) = deep stacks = play looser = +adjustment
        Low SPR (<3) = short stacks = play tighter = -adjustment
        """
        try:
            pot_amount = round_state.get("pot", {}).get("main", {}).get("amount", 100)
            # Approximate stack (simplified)
            estimated_stack = 1000

            spr = estimated_stack / max(pot_amount, 1)

            if spr > 15:
                adjustment = 0.08  # Very deep stacks - play wide
            elif spr > 10:
                adjustment = 0.05  # Deep stacks - play looser
            elif spr > 6:
                adjustment = 0.02  # Medium stacks - slightly looser
            elif spr >= 3:
                adjustment = 0.0   # Standard stacks - neutral
            elif spr >= 2:
                adjustment = -0.03 # Short stacks - tighter
            elif spr >= 1:
                adjustment = -0.06 # Very short stacks - much tighter
            else:
                adjustment = -0.08 # All-in range - very tight

            return adjustment

        except Exception:
            return 0.0

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
        """Reset for new game"""
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
    print("Monte Carlo V8 - V6 Enhanced with Pot Odds and SPR")
    player = MonteCarloV8Enhanced()
    print("✓ Agent initialized with minimal enhancements")
