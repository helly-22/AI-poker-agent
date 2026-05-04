"""
Monte Carlo V7: Advanced Heads-Up Strategy

Incorporates:
- Pot odds and pot size
- Bet sizing analysis
- Opponent tendencies tracking
- Stack-to-Pot Ratio (SPR)
- Previous actions
- Game dynamics
"""

import json
import os
from pypokerengine.players import BasePokerPlayer


class MonteCarloV7Advanced(BasePokerPlayer):
    """Advanced agent with multi-factor decision making for heads-up poker."""

    def __init__(self):
        self.round_history = []
        self.game_history = []
        self.trained_weights = None
        self.opponent_stats = {
            "raises": 0,
            "calls": 0,
            "folds": 0,
            "total_actions": 0
        }
        self.current_round_actions = []
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
        """Fallback thresholds"""
        return {
            "decision_thresholds": {
                "preflop": {"raise_threshold": 0.75, "call_threshold": 0.50},
                "flop": {"raise_threshold": 0.70, "call_threshold": 0.40},
                "turn": {"raise_threshold": 0.65, "call_threshold": 0.35},
                "river": {"raise_threshold": 0.60, "call_threshold": 0.30},
            }
        }

    def declare_action(self, valid_actions, hole_card, round_state):
        """Multi-factor decision making"""
        try:
            # Step 1: Base hand strength
            hand_strength = self._evaluate_hand(hole_card, round_state)

            # Step 2: Pot odds analysis
            pot_odds_factor = self._analyze_pot_odds(round_state, valid_actions)

            # Step 3: Bet sizing analysis
            bet_sizing_factor = self._analyze_bet_sizing(round_state, valid_actions)

            # Step 4: SPR analysis
            spr_factor = self._analyze_spr(round_state)

            # Step 5: Opponent tendencies
            opponent_factor = self._analyze_opponent_tendencies()

            # Step 6: Game dynamics
            dynamics_factor = self._analyze_game_dynamics(round_state)

            # Combine all factors (weighted)
            final_strength = (
                hand_strength * 0.40 +      # Base hand strength
                pot_odds_factor * 0.20 +    # Pot odds adjustment
                bet_sizing_factor * 0.15 +  # Bet sizing adjustment
                spr_factor * 0.10 +         # Stack depth adjustment
                opponent_factor * 0.10 +    # Opponent tendency adjustment
                dynamics_factor * 0.05      # Game dynamics adjustment
            )

            final_strength = min(1.0, max(0.0, final_strength))

            # Get street-specific thresholds
            street = self._get_street(len(round_state.get("community_card", [])))
            thresholds = self.trained_weights["decision_thresholds"].get(street,
                                                    self.trained_weights["decision_thresholds"]["flop"])

            raise_threshold = thresholds.get("raise_threshold", 0.70)
            call_threshold = thresholds.get("call_threshold", 0.40)

            # Make decision
            available_actions = [a["action"] for a in valid_actions]

            if final_strength > raise_threshold:
                if "raise" in available_actions:
                    return "raise"
                elif "call" in available_actions:
                    return "call"
            elif final_strength > call_threshold:
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
        """Evaluate hand strength"""
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

    def _analyze_pot_odds(self, round_state, valid_actions):
        """
        Analyze pot odds: adjust based on pot size vs required bet
        Higher pot odds = more likely to call/raise
        """
        try:
            pot_amount = round_state.get("pot", {}).get("main", {}).get("amount", 100)

            # Find current bet amount (if any raise action available)
            bet_amount = 0
            for action in valid_actions:
                if action["action"] == "raise":
                    bet_amount = action.get("amount", {}).get("max", 0) - action.get("amount", {}).get("min", 0)
                elif action["action"] == "call":
                    bet_amount = action.get("amount", 0)

            # Calculate pot odds (pot size vs bet required)
            if bet_amount > 0:
                odds = pot_amount / max(bet_amount, 1)
                # Good odds = higher factor (1:1 odds = 0.5 factor, 3:1 odds = 0.75 factor)
                pot_odds_factor = min(1.0, odds / (odds + 1))
            else:
                pot_odds_factor = 0.5  # Neutral if no bet

            return pot_odds_factor

        except Exception:
            return 0.5

    def _analyze_bet_sizing(self, round_state, valid_actions):
        """
        Analyze bet sizing: large bets suggest strength, small bets suggest weakness
        Adjust our aggression accordingly
        """
        try:
            pot_amount = round_state.get("pot", {}).get("main", {}).get("amount", 100)
            bet_amount = 0

            for action in valid_actions:
                if action["action"] == "call":
                    bet_amount = action.get("amount", 0)

            if bet_amount == 0:
                return 0.5  # No bet, neutral

            # Bet size ratio (bet as % of pot)
            bet_ratio = bet_amount / max(pot_amount, 1)

            if bet_ratio > 0.75:  # Large bet = opponent strong
                return 0.3  # Reduce aggression
            elif bet_ratio > 0.4:  # Medium bet = normal
                return 0.5  # Neutral
            else:  # Small bet = opponent weak
                return 0.7  # Increase aggression

        except Exception:
            return 0.5

    def _analyze_spr(self, round_state):
        """
        Stack-to-Pot Ratio: adjust based on effective stack depth
        Deep stacks (>10:1) = can play more hands
        Short stacks (<3:1) = must play tighter
        """
        try:
            pot = round_state.get("pot", {}).get("main", {}).get("amount", 100)
            # Approximate stack (would need to track actual stack in real scenario)
            estimated_stack = 1000

            spr = estimated_stack / max(pot, 1)

            if spr > 10:
                return 0.6  # Deep stacks: slightly looser
            elif spr > 5:
                return 0.5  # Medium: neutral
            elif spr > 3:
                return 0.4  # Short: tighter
            else:
                return 0.3  # Very short: much tighter

        except Exception:
            return 0.5

    def _analyze_opponent_tendencies(self):
        """
        Track opponent behavior and adjust:
        - If opponent raises a lot: fold more, call less
        - If opponent calls a lot: raise more, fold less
        - If opponent folds a lot: bluff more
        """
        try:
            total = self.opponent_stats["total_actions"]
            if total == 0:
                return 0.5  # No data yet

            raise_freq = self.opponent_stats["raises"] / total
            call_freq = self.opponent_stats["calls"] / total
            fold_freq = self.opponent_stats["folds"] / total

            # Adjust based on tendencies
            if raise_freq > 0.5:  # Aggressive opponent
                return 0.4  # Play tighter
            elif call_freq > 0.5:  # Loose-passive
                return 0.6  # Exploit with raises
            elif fold_freq > 0.4:  # Folds too much
                return 0.7  # Bluff more
            else:
                return 0.5  # Balanced opponent

        except Exception:
            return 0.5

    def _analyze_game_dynamics(self, round_state):
        """
        Game dynamics: position, aggression level, etc.
        Heads-up specific: button is small blind, has positional advantage
        """
        try:
            # In our simplified version, we track action count
            street = self._get_street(len(round_state.get("community_card", [])))

            # Early streets = play tighter
            if street == "preflop":
                return 0.5  # Preflop: neutral (balanced)
            elif street == "flop":
                return 0.55  # Flop: slightly more aggressive
            elif street == "turn":
                return 0.60  # Turn: more aggressive
            else:  # River
                return 0.65  # River: most aggressive (last chance)

        except Exception:
            return 0.5

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
        self.current_round_actions = []

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.current_round_actions = []

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        """Track opponent actions for tendency analysis"""
        try:
            player_name = action.get("player", {}).get("name", "")
            action_type = action.get("action", "")

            # Only track opponent actions (not our own)
            if player_name and "Opponent" in player_name or "Opp" in player_name:
                self.current_round_actions.append(action_type)

                if action_type == "raise":
                    self.opponent_stats["raises"] += 1
                elif action_type == "call":
                    self.opponent_stats["calls"] += 1
                elif action_type == "fold":
                    self.opponent_stats["folds"] += 1

                self.opponent_stats["total_actions"] += 1
        except Exception:
            pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


if __name__ == "__main__":
    print("Monte Carlo V7 - Advanced Heads-Up Strategy")
    print("Factors: Hand strength + Pot odds + Bet sizing + SPR + Opponent tendencies + Game dynamics")
    player = MonteCarloV7Advanced()
    print("✓ Agent initialized")
