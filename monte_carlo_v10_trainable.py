"""
Monte Carlo V10 Trainable: Ready for training with persistent bucket learning

Improvements:
- Loads pre-trained per-bucket adjustments from v10_trained_buckets.json
- Tracks bucket performance during play
- Can save learned adjustments back to JSON for future use
- Uses 40-bucket hand abstraction with learned thresholds per bucket
"""

import json
import os
from pypokerengine.players import BasePokerPlayer


class MonteCarloV10Trainable(BasePokerPlayer):
    """V10 with persistent training capability."""

    def __init__(self):
        self.round_history = []
        self.game_history = []
        self.trained_weights = None
        self.base_thresholds = None
        self.bucket_adjustments = {}  # Learned per-bucket adjustments

        # Online learning tracking
        self.last_40_rounds = []
        self.bucket_stats = {}
        self.current_round_result = None

        self._load_trained_weights()
        self._load_bucket_adjustments()
        self._initialize_bucket_stats()

    def _load_trained_weights(self):
        """Load base thresholds from JSON"""
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

    def _load_bucket_adjustments(self):
        """Load per-bucket learned adjustments (if available)"""
        try:
            bucket_file = "v10_trained_buckets.json"
            if os.path.exists(bucket_file):
                with open(bucket_file, 'r') as f:
                    data = json.load(f)
                    self.bucket_adjustments = data.get("bucket_adjustments", {})
                    print(f"✓ Loaded V10 bucket adjustments from {bucket_file}")
            else:
                self.bucket_adjustments = {}
        except Exception:
            self.bucket_adjustments = {}

    def _get_fallback_weights(self):
        """Fallback thresholds"""
        return {
            "decision_thresholds": {
                "preflop": {"raise_threshold": 0.75, "call_threshold": 0.50},
                "flop": {"raise_threshold": 0.70, "call_threshold": 0.40},
                "turn": {"raise_threshold": 0.65, "call_threshold": 0.35},
                "river": {"raise_threshold": 0.60, "call_threshold": 0.30},
            }
        }

    def _initialize_bucket_stats(self):
        """Initialize tracking for all 40 buckets"""
        for bucket in range(40):
            self.bucket_stats[bucket] = {
                "wins": 0,
                "losses": 0,
                "win_rate": 0.5,
                "learned_adjustment": self.bucket_adjustments.get(str(bucket), 0.0)
            }

    def _classify_hand_strength_bucket(self, hand_strength):
        """Classify hand into one of 40 buckets"""
        bucket = int(hand_strength * 40)
        return min(39, max(0, bucket))

    def declare_action(self, valid_actions, hole_card, round_state):
        """Decision with bucket-based thresholds"""
        try:
            # Hand strength
            hand_strength = self._evaluate_hand(hole_card, round_state)

            # Classify into bucket
            hand_bucket = self._classify_hand_strength_bucket(hand_strength)

            # Get street-specific base thresholds
            street = self._get_street(len(round_state.get("community_card", [])))
            base_thresholds = self.base_thresholds.get(street, self.base_thresholds["flop"])

            raise_threshold = base_thresholds["raise_threshold"]
            call_threshold = base_thresholds["call_threshold"]

            # Apply bucket adjustment (from training or recent 40 rounds)
            raise_threshold, call_threshold = self._apply_bucket_adjustment(
                raise_threshold, call_threshold, hand_bucket
            )

            # Decision
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

            if "fold" in available_actions:
                return "fold"
            elif "check" in available_actions:
                return "check"
            else:
                return "call"

        except Exception:
            return "fold"

    def _apply_bucket_adjustment(self, raise_threshold, call_threshold, hand_bucket):
        """Apply learned or recent bucket adjustment"""
        bucket_info = self.bucket_stats.get(hand_bucket, {})

        # Priority 1: Use recent performance if enough data
        if len(self.last_40_rounds) >= 10:
            bucket_win_rate = bucket_info.get("win_rate", 0.5)

            if bucket_win_rate > 0.65:
                adjustment = -0.04
            elif bucket_win_rate > 0.55:
                adjustment = -0.02
            elif bucket_win_rate < 0.35:
                adjustment = 0.04
            elif bucket_win_rate < 0.45:
                adjustment = 0.02
            else:
                adjustment = 0.0
        else:
            # Priority 2: Use learned adjustment from training
            adjustment = bucket_info.get("learned_adjustment", 0.0)

        raise_threshold = max(0.50, min(0.85, raise_threshold + adjustment))
        call_threshold = max(0.20, min(0.65, call_threshold + adjustment))

        return raise_threshold, call_threshold

    def _update_bucket_stats(self):
        """Recalculate win rates for all buckets from last 40 rounds"""
        for bucket in self.bucket_stats:
            self.bucket_stats[bucket]["wins"] = 0
            self.bucket_stats[bucket]["losses"] = 0

        for round_info in self.last_40_rounds:
            bucket = round_info.get("bucket")
            result = round_info.get("result")

            if bucket is not None and result is not None:
                if result == "win":
                    self.bucket_stats[bucket]["wins"] += 1
                elif result == "loss":
                    self.bucket_stats[bucket]["losses"] += 1

        for bucket in self.bucket_stats:
            wins = self.bucket_stats[bucket]["wins"]
            losses = self.bucket_stats[bucket]["losses"]
            total = wins + losses

            if total > 0:
                self.bucket_stats[bucket]["win_rate"] = wins / total
            else:
                self.bucket_stats[bucket]["win_rate"] = 0.5

    def _evaluate_hand(self, hole_card, round_state):
        """Hand strength evaluation"""
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
        """Track new round"""
        self.current_round_result = {
            "round": round_count,
            "hole_card": hole_card,
            "bucket": None,
            "result": None
        }

    def receive_street_start_message(self, street, round_state):
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
        """Track round result and update statistics"""
        try:
            if self.current_round_result:
                our_win = any("Agent" in str(w.get("name", "")) for w in winners)
                self.current_round_result["result"] = "win" if our_win else "loss"

                self.last_40_rounds.append(self.current_round_result)

                if len(self.last_40_rounds) > 40:
                    self.last_40_rounds.pop(0)

                self._update_bucket_stats()
        except Exception:
            pass

    def save_bucket_adjustments(self, filename="v10_trained_buckets.json"):
        """Save learned bucket adjustments to JSON"""
        try:
            # Compute final adjustments from bucket stats
            bucket_data = {}
            for bucket in range(40):
                wins = self.bucket_stats[bucket]["wins"]
                losses = self.bucket_stats[bucket]["losses"]
                total = wins + losses

                if total > 0:
                    win_rate = wins / total
                    # Convert win rate to adjustment
                    if win_rate > 0.65:
                        adjustment = -0.04
                    elif win_rate > 0.55:
                        adjustment = -0.02
                    elif win_rate < 0.35:
                        adjustment = 0.04
                    elif win_rate < 0.45:
                        adjustment = 0.02
                    else:
                        adjustment = 0.0
                else:
                    adjustment = 0.0

                bucket_data[str(bucket)] = {
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate if total > 0 else 0.5,
                    "adjustment": adjustment
                }

            output = {
                "bucket_adjustments": {str(b): bucket_data[str(b)]["adjustment"] for b in range(40)},
                "bucket_stats": bucket_data,
                "training_timestamp": str(self.game_history[-1] if self.game_history else "N/A")
            }

            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)

            print(f"✓ Saved V10 bucket adjustments to {filename}")

        except Exception as e:
            print(f"✗ Failed to save bucket adjustments: {e}")


if __name__ == "__main__":
    print("Monte Carlo V10 Trainable - Ready for training")
    player = MonteCarloV10Trainable()
    print("✓ Agent initialized and ready for training")
