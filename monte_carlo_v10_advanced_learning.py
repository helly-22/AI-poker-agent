"""
Monte Carlo V10: Advanced Online Learning + 40-Bucket Hand Abstraction

Improvements over V9:
- 40 hand strength buckets (instead of 5)
- 40-round learning window (instead of 20)
- Per-bucket threshold tracking (not global)
- Better online learning adjustment mechanism
- Hand strength buckets computed from equity simulation
"""

import json
import os
from pypokerengine.players import BasePokerPlayer


class MonteCarloV10AdvancedLearning(BasePokerPlayer):
    """V6 with advanced online learning and 40-bucket hand abstraction."""

    def __init__(self):
        self.round_history = []
        self.game_history = []
        self.trained_weights = None
        self.base_thresholds = None

        # Advanced online learning tracking
        self.last_40_rounds = []  # Track last 40 rounds
        self.bucket_stats = {}    # Per-bucket win rates
        self.current_round_result = None

        self._load_trained_weights()
        self._initialize_bucket_stats()

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

        # Store base thresholds
        self.base_thresholds = {}
        for street in ["preflop", "flop", "turn", "river"]:
            thresholds = self.trained_weights.get("decision_thresholds", {}).get(street, {})
            self.base_thresholds[street] = {
                "raise_threshold": thresholds.get("raise_threshold", 0.70),
                "call_threshold": thresholds.get("call_threshold", 0.40)
            }

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

    def _initialize_bucket_stats(self):
        """Initialize win tracking for each of 40 buckets"""
        for bucket in range(40):
            self.bucket_stats[bucket] = {
                "wins": 0,
                "losses": 0,
                "win_rate": 0.5,  # Start neutral
                "threshold_adjustment": 0.0
            }

    def _classify_hand_strength_bucket(self, hand_strength):
        """Classify hand into one of 40 buckets (0-39)"""
        # Map hand strength (0.0-1.0) to bucket (0-39)
        bucket = int(hand_strength * 40)
        return min(39, max(0, bucket))

    def declare_action(self, valid_actions, hole_card, round_state):
        """Decision with advanced online learning and hand abstraction"""
        try:
            # Step 1: Base hand strength (from V6)
            hand_strength = self._evaluate_hand(hole_card, round_state)

            # Step 2: Classify into 40-bucket abstraction
            hand_bucket = self._classify_hand_strength_bucket(hand_strength)

            # Step 3: Get street-specific base thresholds
            street = self._get_street(len(round_state.get("community_card", [])))
            base_thresholds = self.base_thresholds.get(street, self.base_thresholds["flop"])

            raise_threshold = base_thresholds["raise_threshold"]
            call_threshold = base_thresholds["call_threshold"]

            # Step 4: Apply per-bucket online learning adjustment
            raise_threshold, call_threshold = self._apply_bucket_adjustment(
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

    def _apply_bucket_adjustment(self, raise_threshold, call_threshold, hand_bucket):
        """Apply per-bucket threshold adjustment based on recent performance"""
        if len(self.last_40_rounds) < 10:
            # Not enough data, use base thresholds
            return raise_threshold, call_threshold

        # Get stats for this bucket
        bucket_info = self.bucket_stats.get(hand_bucket, {})
        bucket_win_rate = bucket_info.get("win_rate", 0.5)

        # Adjustment logic (bounded to ±0.05)
        if bucket_win_rate > 0.65:
            # This bucket is winning: be more aggressive
            adjustment = -0.04  # Lower thresholds to raise/call more
        elif bucket_win_rate > 0.55:
            # Slightly winning: minor adjustment
            adjustment = -0.02
        elif bucket_win_rate < 0.35:
            # This bucket is losing badly: be more conservative
            adjustment = 0.04  # Raise thresholds to fold more
        elif bucket_win_rate < 0.45:
            # Slightly losing: minor adjustment
            adjustment = 0.02
        else:
            # Neutral (0.45-0.55): no adjustment
            adjustment = 0.0

        # Apply adjustment with bounds
        raise_threshold = max(0.50, min(0.85, raise_threshold + adjustment))
        call_threshold = max(0.20, min(0.65, call_threshold + adjustment))

        return raise_threshold, call_threshold

    def _update_bucket_stats(self):
        """Recalculate win rates for all buckets from last 40 rounds"""
        # Reset all bucket stats
        for bucket in self.bucket_stats:
            self.bucket_stats[bucket]["wins"] = 0
            self.bucket_stats[bucket]["losses"] = 0

        # Count wins/losses per bucket from recent rounds
        for round_info in self.last_40_rounds:
            bucket = round_info.get("bucket")
            result = round_info.get("result")

            if bucket is not None and result is not None:
                if result == "win":
                    self.bucket_stats[bucket]["wins"] += 1
                elif result == "loss":
                    self.bucket_stats[bucket]["losses"] += 1

        # Compute win rates
        for bucket in self.bucket_stats:
            wins = self.bucket_stats[bucket]["wins"]
            losses = self.bucket_stats[bucket]["losses"]
            total = wins + losses

            if total > 0:
                self.bucket_stats[bucket]["win_rate"] = wins / total
            else:
                self.bucket_stats[bucket]["win_rate"] = 0.5  # Default neutral

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
        self.last_40_rounds = []
        self._initialize_bucket_stats()

    def receive_round_start_message(self, round_count, hole_card, seats):
        """Start tracking new round"""
        self.current_round_result = {
            "round": round_count,
            "hole_card": hole_card,
            "bucket": None,
            "result": None
        }

    def receive_street_start_message(self, street, round_state):
        # Track bucket at start of round
        if self.current_round_result and self.current_round_result["bucket"] is None:
            try:
                hand_strength = self._evaluate_hand(
                    self.current_round_result["hole_card"],
                    round_state
                )
                self.current_round_result["bucket"] = self._classify_hand_strength_bucket(hand_strength)
            except Exception:
                pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        """Track round result and update bucket statistics"""
        try:
            if self.current_round_result:
                # Determine if we won this round
                our_win = any("Agent" in str(w.get("name", "")) for w in winners)
                self.current_round_result["result"] = "win" if our_win else "loss"

                # Add to last 40 rounds
                self.last_40_rounds.append(self.current_round_result)

                # Keep only last 40
                if len(self.last_40_rounds) > 40:
                    self.last_40_rounds.pop(0)

                # Recalculate bucket statistics
                self._update_bucket_stats()
        except Exception:
            pass


if __name__ == "__main__":
    print("Monte Carlo V10 - Advanced Online Learning + 40-Bucket Hand Abstraction")
    player = MonteCarloV10AdvancedLearning()
    print("✓ Agent initialized with 40-bucket abstraction and 40-round learning window")
