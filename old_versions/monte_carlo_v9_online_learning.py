"""
Monte Carlo V9: V6 + Online Learning (Last 20 Rounds) + Hand Abstraction

Combines:
- V6 base (hard-coded hand strength + learned JSON thresholds)
- Hand abstraction (5 strength buckets)
- Online learning from last 20 rounds
- Adaptive threshold adjustment (bounded)
"""

import json
import os
from pypokerengine.players import BasePokerPlayer


class MonteCarloV9OnlineLearning(BasePokerPlayer):
    """V6 with online learning and hand abstraction."""

    def __init__(self):
        self.round_history = []
        self.game_history = []
        self.trained_weights = None
        self.current_thresholds = None

        # Online learning tracking
        self.last_20_rounds = []  # Track last 20 rounds for online learning
        self.current_round_result = None

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

        # Initialize current thresholds from loaded weights
        self.current_thresholds = self._get_current_thresholds("flop")

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

    def _get_current_thresholds(self, street):
        """Get thresholds for street (either from online learning or JSON)"""
        if self.trained_weights is None:
            self.trained_weights = self._get_fallback_weights()

        thresholds = self.trained_weights["decision_thresholds"].get(street,
                                                    self.trained_weights["decision_thresholds"]["flop"])
        return {
            "raise_threshold": thresholds.get("raise_threshold", 0.70),
            "call_threshold": thresholds.get("call_threshold", 0.40)
        }

    def _classify_hand_strength(self, hand_strength):
        """Classify hand into strength bucket (hand abstraction)"""
        if hand_strength >= 0.8:
            return "ultra_strong"  # 0.8-1.0
        elif hand_strength >= 0.6:
            return "strong"        # 0.6-0.8
        elif hand_strength >= 0.4:
            return "medium"        # 0.4-0.6
        elif hand_strength >= 0.2:
            return "weak"          # 0.2-0.4
        else:
            return "very_weak"     # 0-0.2

    def declare_action(self, valid_actions, hole_card, round_state):
        """Decision with online learning and hand abstraction"""
        try:
            # Step 1: Base hand strength (from V6)
            hand_strength = self._evaluate_hand(hole_card, round_state)

            # Step 2: Hand abstraction (classify into bucket)
            hand_bucket = self._classify_hand_strength(hand_strength)

            # Step 3: Get street-specific thresholds
            street = self._get_street(len(round_state.get("community_card", [])))
            thresholds = self._get_current_thresholds(street)

            raise_threshold = thresholds.get("raise_threshold", 0.70)
            call_threshold = thresholds.get("call_threshold", 0.40)

            # Step 4: Apply online learning adjustment (bounded)
            raise_threshold, call_threshold = self._apply_online_adjustment(
                raise_threshold, call_threshold, hand_bucket
            )

            # Make decision
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

    def _apply_online_adjustment(self, raise_threshold, call_threshold, hand_bucket):
        """Adjust thresholds based on recent performance (last 20 rounds)"""
        if len(self.last_20_rounds) < 5:
            # Not enough data, use original thresholds
            return raise_threshold, call_threshold

        # Calculate recent win rate
        recent_wins = sum(1 for r in self.last_20_rounds if r.get("result") == "win")
        recent_losses = sum(1 for r in self.last_20_rounds if r.get("result") == "loss")
        total_recent = recent_wins + recent_losses

        if total_recent == 0:
            return raise_threshold, call_threshold

        win_rate = recent_wins / total_recent

        # Adjustment logic (bounded to ±0.03)
        if win_rate > 0.6:
            # Winning: be slightly more aggressive
            adjustment = 0.02
            raise_threshold = max(0.50, raise_threshold - adjustment)
            call_threshold = max(0.20, call_threshold - adjustment)
        elif win_rate < 0.4:
            # Losing: be slightly more conservative
            adjustment = 0.02
            raise_threshold = min(0.85, raise_threshold + adjustment)
            call_threshold = min(0.60, call_threshold + adjustment)

        return raise_threshold, call_threshold

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
        """Start tracking new round"""
        self.current_round_result = {
            "round": round_count,
            "hole_card": hole_card,
            "result": None
        }

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        """Track round result for online learning"""
        try:
            # Determine if we won this round
            if self.current_round_result:
                # Check if our player (assumed name "Agent" or "TestAgent") is in winners
                our_win = any("Agent" in str(w.get("name", "")) for w in winners)
                self.current_round_result["result"] = "win" if our_win else "loss"

                # Add to last 20 rounds
                self.last_20_rounds.append(self.current_round_result)

                # Keep only last 20
                if len(self.last_20_rounds) > 20:
                    self.last_20_rounds.pop(0)
        except Exception:
            pass


if __name__ == "__main__":
    print("Monte Carlo V9 - V6 + Online Learning + Hand Abstraction")
    player = MonteCarloV9OnlineLearning()
    print("✓ Agent initialized with online learning")
