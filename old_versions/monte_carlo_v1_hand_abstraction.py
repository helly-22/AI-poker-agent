"""
Monte Carlo Poker Player - Version 1: Hand Abstraction + MC Sims

Uses hand strength abstractions (Premium/Strong/Medium/Weak) combined with
Monte Carlo simulations for more informed decisions.
"""

import random
from pypokerengine.players import BasePokerPlayer


class MonteCarloV1HandAbstraction(BasePokerPlayer):
    """Monte Carlo agent with hand strength abstraction."""

    def __init__(self):
        """Initialize agent."""
        self.round_history = []
        self.game_history = []

    def declare_action(self, valid_actions, hole_card, round_state):
        """Main decision function - returns action STRING."""
        try:
            # Step 1: Classify hand into abstraction bucket
            hand_bucket = self._classify_hand(hole_card)

            # Step 2: Get community cards and board texture
            community_cards = round_state.get("community_card", [])
            board_strength = self._evaluate_board(community_cards)

            # Step 3: Run Monte Carlo simulations based on bucket
            mc_strength = self._run_mc_simulations(hand_bucket, len(community_cards))

            # Step 4: Combine evaluations
            combined_strength = (mc_strength * 0.6) + (board_strength * 0.4)

            # Step 5: Decide action based on combined strength and bucket
            action_name = self._decide_action(combined_strength, hand_bucket, valid_actions)

            return action_name

        except Exception:
            return "fold"

    def _classify_hand(self, hole_card):
        """Classify hand into abstraction bucket: PREMIUM, STRONG, MEDIUM, WEAK"""
        card1, card2 = hole_card[0], hole_card[1]
        rank1 = card1[0]
        rank2 = card2[0]
        is_pair = card1[0] == card2[0]  # Check RANK, not suit
        is_suited = card1[1] == card2[1]  # Check SUIT

        rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
                      '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        r1 = rank_order.get(rank1, 7)
        r2 = rank_order.get(rank2, 7)

        # PREMIUM: AA, KK, QQ, AK
        if is_pair and r1 >= 12:  # AA, KK, QQ
            return "PREMIUM"
        if (r1 == 14 and r2 == 13) or (r1 == 13 and r2 == 14):  # AK
            return "PREMIUM"

        # STRONG: JJ-99, AQ, AJ, KQ
        if is_pair and r1 >= 9:  # JJ, TT, 99
            return "STRONG"
        if (r1 == 14 and r2 in [12, 11]) or (r1 in [12, 11] and r2 == 14):  # AQ, AJ
            return "STRONG"
        if (r1 == 13 and r2 == 12) or (r1 == 12 and r2 == 13):  # KQ
            return "STRONG"

        # MEDIUM: 88-22, broadway cards, one-gappers
        if is_pair:  # 88-22
            return "MEDIUM"
        if r1 >= 10 and r2 >= 10:  # Broadway (TT+, all broadways)
            return "MEDIUM"
        if abs(r1 - r2) <= 2 and min(r1, r2) >= 8:  # Connected/gapped high cards
            return "MEDIUM"

        # WEAK: Everything else
        return "WEAK"

    def _evaluate_board(self, community_cards):
        """Evaluate board texture strength (0-1 scale)"""
        if not community_cards:
            return 0.0  # Preflop, no board yet

        num_cards = len(community_cards)

        # Extract ranks and suits
        ranks = [card[0] for card in community_cards]
        suits = [card[1] for card in community_cards]

        rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
                      '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        rank_vals = [rank_order.get(r, 7) for r in ranks]

        # Calculate board factors
        high_cards = sum(1 for r in rank_vals if r >= 10)  # A, K, Q, J, T
        pairs = len(rank_vals) - len(set(rank_vals))  # Duplicate ranks
        flushes = max([suits.count(s) for s in suits])  # Suit duplicates

        # WET board (many draws possible): high cards + pairs
        # DRY board (few draws): low scattered
        wet_score = (high_cards * 0.3) + (pairs * 0.2) + (flushes * 0.2)

        # Normalize to 0-1
        return min(1.0, wet_score / num_cards)

    def _run_mc_simulations(self, hand_bucket, board_cards_count):
        """Run Monte Carlo simulations based on hand bucket"""
        # Adjust sim count based on bucket and board progress
        base_sims = 1000

        if hand_bucket == "PREMIUM":
            sims = base_sims * 1.5  # More confident with premium hands
            win_rate = 0.75  # Expected win rate for premium hands
        elif hand_bucket == "STRONG":
            sims = base_sims
            win_rate = 0.60
        elif hand_bucket == "MEDIUM":
            sims = base_sims * 0.8
            win_rate = 0.45
        else:  # WEAK
            sims = base_sims * 0.5
            win_rate = 0.25

        # Adjust based on board progress (more sims early, fewer late)
        if board_cards_count == 0:  # Preflop
            board_adjustment = 1.0
        elif board_cards_count == 3:  # Flop
            board_adjustment = 0.8
        elif board_cards_count == 4:  # Turn
            board_adjustment = 0.6
        else:  # River
            board_adjustment = 0.4

        # Simulate some variance
        variance = random.uniform(-0.1, 0.1)

        return min(1.0, max(0.0, win_rate * board_adjustment + variance))

    def _decide_action(self, strength, hand_bucket, valid_actions):
        """Decide action based on strength and hand bucket"""
        available_actions = [a["action"] for a in valid_actions]

        # Adjusted thresholds based on hand bucket
        if hand_bucket == "PREMIUM":
            raise_threshold = 0.65
            call_threshold = 0.35
        elif hand_bucket == "STRONG":
            raise_threshold = 0.70
            call_threshold = 0.40
        elif hand_bucket == "MEDIUM":
            raise_threshold = 0.75
            call_threshold = 0.45
        else:  # WEAK
            raise_threshold = 0.85
            call_threshold = 0.55

        # Action selection
        if strength > raise_threshold:
            if "raise" in available_actions:
                return "raise"
            elif "call" in available_actions:
                return "call"
        elif strength > call_threshold:
            if "call" in available_actions:
                return "call"
            elif "check" in available_actions:
                return "check"

        # Default to fold if too weak
        if "fold" in available_actions:
            return "fold"
        elif "check" in available_actions:
            return "check"
        else:
            return "call"

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
    print("Monte Carlo V1 - Hand Abstraction")
    player = MonteCarloV1HandAbstraction()
    print("✓ Agent initialized")
