"""
Hand Strength Evaluator using Monte Carlo Simulation
Calculates poker hand equity using MC simulations.
"""

import random
from pypokerengine.engine.card import Card
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.engine.deck import Deck


class HandStrengthEvaluator:
    """
    Evaluates hand strength using Monte Carlo simulation.
    """

    def __init__(self, num_simulations=1000):
        """Initialize with number of simulations."""
        self.num_simulations = num_simulations

    def calculate_hand_strength(self, hole_card, community_cards, num_sims=None):
        """
        Calculate hand strength vs random opponent hands.

        Args:
            hole_card: List of 2 Card objects or strings
            community_cards: List of Card objects or strings (0-5 cards)
            num_sims: Override number of simulations

        Returns:
            float: Win probability (0.0 to 1.0)
        """
        if num_sims is None:
            num_sims = self.num_simulations

        hole_card = self._normalize_cards(hole_card)
        community_cards = self._normalize_cards(community_cards)

        # Build remaining deck
        all_card_ids = set(range(1, 53))
        used_ids = set([c.to_id() for c in hole_card] + [c.to_id() for c in community_cards])
        remaining_ids = list(all_card_ids - used_ids)

        wins = 0
        ties = 0

        for _ in range(num_sims):
            # Sample opponent's 2 cards
            opp_ids = random.sample(remaining_ids, 2)
            opp_hand = [Card.from_id(cid) for cid in opp_ids]

            # Simulate remaining board
            board = self._simulate_board_runout(
                community_cards,
                remaining_ids,
                opp_ids
            )

            # Evaluate hands
            my_rank = HandEvaluator.eval_hand(hole_card, board)
            opp_rank = HandEvaluator.eval_hand(opp_hand, board)

            if my_rank > opp_rank:
                wins += 1
            elif my_rank == opp_rank:
                ties += 1

        hand_strength = (wins + 0.5 * ties) / num_sims
        return hand_strength

    def get_hand_strength_vs_range(self, hole_card, community_cards, opponent_range, num_sims=None):
        """
        Calculate hand strength vs specific opponent hand distribution.

        Args:
            hole_card: List of 2 Card objects or strings
            community_cards: List of Card objects or strings (0-5 cards)
            opponent_range: Dict mapping hand names to probabilities
                           {"AA": 0.05, "KK": 0.04, ...}
            num_sims: Override number of simulations

        Returns:
            float: Win probability vs range
        """
        if num_sims is None:
            num_sims = self.num_simulations

        hole_card = self._normalize_cards(hole_card)
        community_cards = self._normalize_cards(community_cards)

        # Build remaining deck
        all_card_ids = set(range(1, 53))
        used_ids = set([c.to_id() for c in hole_card] + [c.to_id() for c in community_cards])
        remaining_ids = list(all_card_ids - used_ids)

        wins = 0
        ties = 0
        valid_sims = 0

        for _ in range(num_sims):
            # Sample opponent hand from distribution
            opp_hand_str = self._sample_from_distribution(opponent_range)

            try:
                opp_hand = self._hand_str_to_cards(opp_hand_str, remaining_ids)
                if opp_hand is None:
                    continue

                opp_ids = [c.to_id() for c in opp_hand]

                # Simulate remaining board
                board = self._simulate_board_runout(
                    community_cards,
                    remaining_ids,
                    opp_ids
                )

                # Evaluate hands
                my_rank = HandEvaluator.eval_hand(hole_card, board)
                opp_rank = HandEvaluator.eval_hand(opp_hand, board)

                if my_rank > opp_rank:
                    wins += 1
                elif my_rank == opp_rank:
                    ties += 1

                valid_sims += 1
            except:
                continue

        if valid_sims == 0:
            return 0.5

        hand_strength = (wins + 0.5 * ties) / valid_sims
        return hand_strength

    def _simulate_board_runout(self, current_board, remaining_ids, exclude_ids):
        """Complete the community board with random cards."""
        board = list(current_board)
        excluded = set(exclude_ids)
        available = [cid for cid in remaining_ids if cid not in excluded]

        cards_needed = 5 - len(board)
        if cards_needed > 0 and len(available) >= cards_needed:
            new_ids = random.sample(available, cards_needed)
            board.extend([Card.from_id(cid) for cid in new_ids])

        return board

    def _sample_from_distribution(self, hand_distribution):
        """Sample a hand from probability distribution."""
        hands = list(hand_distribution.keys())
        probs = list(hand_distribution.values())

        total = sum(probs)
        if total == 0:
            return hands[0]

        probs = [p / total for p in probs]
        return random.choices(hands, weights=probs, k=1)[0]

    def _hand_str_to_cards(self, hand_str, remaining_ids):
        """
        Convert hand string like 'AA' or 'AKs' to Card objects.
        Returns None if cards not available in remaining deck.
        """
        remaining_set = set(remaining_ids)

        # Parse hand string
        if len(hand_str) < 2:
            return None

        rank1 = hand_str[0]
        rank2 = hand_str[1]

        is_suited = len(hand_str) > 2 and hand_str[2] == 's'

        # Map rank to card IDs
        rank_map = {
            'A': [49, 50, 51, 52],  # Ace in all 4 suits
            'K': [45, 46, 47, 48],  # King
            'Q': [41, 42, 43, 44],  # Queen
            'J': [37, 38, 39, 40],  # Jack
            'T': [33, 34, 35, 36],  # Ten
            '9': [29, 30, 31, 32],
            '8': [25, 26, 27, 28],
            '7': [21, 22, 23, 24],
            '6': [17, 18, 19, 20],
            '5': [13, 14, 15, 16],
            '4': [9, 10, 11, 12],
            '3': [5, 6, 7, 8],
            '2': [1, 2, 3, 4],
        }

        if rank1 not in rank_map or rank2 not in rank_map:
            return None

        rank1_ids = [cid for cid in rank_map[rank1] if cid in remaining_set]
        rank2_ids = [cid for cid in rank_map[rank2] if cid in remaining_set]

        if not rank1_ids or not rank2_ids:
            return None

        if rank1 == rank2:  # Pair like AA
            if len(rank1_ids) < 2:
                return None
            selected_ids = random.sample(rank1_ids, 2)
        elif is_suited:  # Suited like AKs
            # Pick same suit
            for suit in range(4):
                id1 = rank_map[rank1][suit]
                id2 = rank_map[rank2][suit]
                if id1 in remaining_set and id2 in remaining_set:
                    selected_ids = [id1, id2]
                    break
            else:
                return None
        else:  # Offsuit like AKo or any two cards
            selected_ids = [random.choice(rank1_ids), random.choice(rank2_ids)]

        return [Card.from_id(cid) for cid in selected_ids]

    def _normalize_cards(self, cards):
        """Convert card strings to Card objects if needed."""
        if not cards:
            return []

        normalized = []
        for card in cards:
            if isinstance(card, str):
                normalized.append(Card.from_str(card))
            else:
                normalized.append(card)

        return normalized


if __name__ == "__main__":
    evaluator = HandStrengthEvaluator(num_simulations=1000)
    print("HandStrengthEvaluator imported successfully!")

    # Simple test
    try:
        strength = evaluator.calculate_hand_strength(["HA", "DA"], [])
        print(f"AA strength: {strength:.2%}")
    except Exception as e:
        print(f"Error: {e}")
