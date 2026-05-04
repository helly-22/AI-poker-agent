"""
Game State Analyzer: Extract and analyze poker game features

Calculates: SPR, position, board texture, stack info, street awareness
"""


class GameStateAnalyzer:
    """Analyzes current game state for decision making."""

    def __init__(self):
        pass

    # ===== STACK-TO-POT RATIO (SPR) =====

    def calculate_spr(self, round_state):
        """
        Stack-to-Pot Ratio: effective_stack / pot

        SPR interpretation:
        - SPR > 10: Deep stack, play wide ranges
        - SPR 6-10: Medium stack, standard play
        - SPR 3-6: Short stack, tighter play, all-in more
        - SPR < 3: Very short, mostly all-in decisions

        Args:
            round_state: Current game state

        Returns:
            float: SPR value
        """
        try:
            pot = round_state.get("pot", 0)
            if pot == 0:
                return 10.0  # Default high SPR if no pot yet

            # Get effective stack (min of our stack and opponent stack)
            my_stack = round_state.get("my_stack", 1000)
            opp_stack = round_state.get("opp_stack", 1000)
            effective_stack = min(my_stack, opp_stack)

            spr = effective_stack / pot if pot > 0 else 10.0
            return max(0.5, min(spr, 20.0))  # Bound between 0.5 and 20

        except Exception as e:
            return 5.0  # Default to medium SPR

    def get_spr_strategy(self, spr):
        """
        Return strategic guidance based on SPR.

        Returns:
            str: "deep", "medium", or "short"
        """
        if spr > 8:
            return "deep"
        elif spr > 4:
            return "medium"
        else:
            return "short"

    # ===== POSITION =====

    def get_position(self, round_state):
        """
        Determine position relative to button.

        Button (last to act) = best position
        Blinds (first to act) = worst position

        Args:
            round_state: Game state with seats and button position

        Returns:
            str: "button", "small_blind", or "big_blind"
        """
        try:
            seats = round_state.get("seats", {})
            button_pos = round_state.get("button_pos", 0)

            # Find our position
            my_pos = None
            for player in seats.get("players", []):
                if player.get("uuid") == "my_agent":
                    my_pos = player.get("seat", 0)
                    break

            if my_pos is None:
                return "unknown"

            # In heads-up (2 players), button is small blind
            if button_pos == my_pos:
                return "button"  # Small blind, last to act preflop
            else:
                return "big_blind"  # Big blind, first to act preflop

        except Exception:
            return "unknown"

    def position_multiplier(self, position):
        """
        Return hand strength multiplier based on position.

        Better position = can play wider ranges

        Args:
            position: "button", "small_blind", or "big_blind"

        Returns:
            float: Multiplier for hand strength (1.0 = neutral)
        """
        multipliers = {
            "button": 1.15,  # 15% stronger in position
            "small_blind": 1.10,
            "big_blind": 0.90,  # 10% weaker
            "unknown": 1.0,
        }
        return multipliers.get(position, 1.0)

    # ===== BOARD TEXTURE =====

    def analyze_board_texture(self, community_cards):
        """
        Analyze board texture: dry, semi-wet, wet, etc.

        Texture affects:
        - How much drawing hands matter
        - Variance of outcomes
        - Best hand strength advantage

        Args:
            community_cards: List of community cards

        Returns:
            dict: {
                "type": "dry"|"connected"|"wet"|"paired",
                "description": human readable
                "draw_potential": 0-1 (how likely draws)
                "variance": "low"|"medium"|"high"
            }
        """
        if not community_cards or len(community_cards) < 3:
            return {"type": "unknown", "draw_potential": 0.5, "variance": "medium"}

        try:
            ranks = [card[0] for card in community_cards]
            suits = [card[1] for card in community_cards]

            # Check for pair/trips/quads
            if len(ranks) != len(set(ranks)):
                return {
                    "type": "paired",
                    "description": "Paired board - reduces draws",
                    "draw_potential": 0.3,
                    "variance": "low",
                }

            # Check for flush draws (3+ same suit)
            suit_counts = {}
            for suit in suits:
                suit_counts[suit] = suit_counts.get(suit, 0) + 1

            has_three_flush = any(count >= 3 for count in suit_counts.values())
            max_suit_count = max(suit_counts.values()) if suit_counts else 0

            # Check for straight draws (connected cards)
            rank_values = self._rank_to_value(ranks)
            rank_values.sort()

            # Check gaps between consecutive cards
            gaps = [rank_values[i + 1] - rank_values[i] for i in range(len(rank_values) - 1)]
            max_gap = max(gaps) if gaps else 5

            # Analyze connectivity
            if max_gap == 1:
                # All connected (like 789)
                board_type = "connected"
                draw_potential = 0.8
                variance = "high"
            elif max_gap == 2:
                # Semi-connected (like 79T)
                board_type = "semi-connected"
                draw_potential = 0.6
                variance = "medium"
            else:
                # Disconnected (like 27K)
                board_type = "dry"
                draw_potential = 0.2
                variance = "low"

            # Adjust for flush possibilities
            if has_three_flush and board_type == "dry":
                board_type = "semi-wet"
                draw_potential = 0.5
                variance = "medium"
            elif has_three_flush:
                board_type = "wet"
                draw_potential = 0.9
                variance = "high"

            return {
                "type": board_type,
                "description": self._get_texture_description(board_type),
                "draw_potential": draw_potential,
                "variance": variance,
                "has_flush_draw": has_three_flush,
                "connected": max_gap <= 2,
            }

        except Exception:
            return {"type": "unknown", "draw_potential": 0.5, "variance": "medium"}

    def texture_multiplier(self, texture_info):
        """
        Return hand strength multiplier based on board texture.

        Dry boards amplify strong hand advantage.
        Wet boards reduce it (draws have value).

        Args:
            texture_info: From analyze_board_texture()

        Returns:
            float: Multiplier for hand strength
        """
        texture_type = texture_info.get("type", "unknown")

        multipliers = {
            "dry": 1.15,  # Strong hands get 15% boost
            "semi-connected": 1.05,
            "connected": 0.95,  # Draws reduce advantage
            "wet": 0.85,  # Many draws possible
            "paired": 1.10,
            "semi-wet": 1.0,
            "unknown": 1.0,
        }

        return multipliers.get(texture_type, 1.0)

    # ===== STREET AWARENESS =====

    def get_street(self, community_cards):
        """
        Determine current street from community cards.

        Args:
            community_cards: List of community cards

        Returns:
            str: "preflop", "flop", "turn", or "river"
        """
        if not community_cards:
            return "preflop"
        elif len(community_cards) == 3:
            return "flop"
        elif len(community_cards) == 4:
            return "turn"
        elif len(community_cards) == 5:
            return "river"
        else:
            return "preflop"

    def street_multiplier(self, street):
        """
        Adjust play based on street.

        Preflop: Tightest, most information missing
        River: Tightest play (no more cards), show down or bluff

        Args:
            street: From get_street()

        Returns:
            float: Hand strength multiplier
        """
        multipliers = {
            "preflop": 0.95,  # Tighter preflop
            "flop": 1.0,  # Standard
            "turn": 1.0,  # Standard
            "river": 1.05,  # Looser (no more uncertainty)
        }
        return multipliers.get(street, 1.0)

    # ===== STACK SIZE AWARENESS =====

    def get_stack_category(self, round_state):
        """
        Categorize stack size.

        Args:
            round_state: Game state

        Returns:
            str: "deep", "medium", or "short"
        """
        spr = self.calculate_spr(round_state)
        return self.get_spr_strategy(spr)

    def stack_multiplier(self, stack_category):
        """
        Adjust play based on stack depth.

        Deep stacks: Can afford to take risks, wider ranges
        Short stacks: Must be tight, fewer hands worth playing

        Args:
            stack_category: From get_stack_category()

        Returns:
            float: Hand strength multiplier
        """
        multipliers = {
            "deep": 1.1,  # 10% looser
            "medium": 1.0,  # Standard
            "short": 0.9,  # 10% tighter
        }
        return multipliers.get(stack_category, 1.0)

    # ===== POT ODDS =====

    def calculate_pot_odds(self, round_state):
        """
        Calculate pot odds: amount_to_call / (pot + amount_to_call)

        If hand_strength > pot_odds, it's +EV to call.

        Args:
            round_state: Game state

        Returns:
            float: Pot odds (0.0 to 1.0)
        """
        try:
            pot = round_state.get("pot", 0)
            call_amount = self._get_call_amount(round_state)

            if pot + call_amount == 0:
                return 0.5

            pot_odds = call_amount / (pot + call_amount)
            return max(0.0, min(pot_odds, 1.0))

        except Exception:
            return 0.5

    # ===== COMBINED ADJUSTMENT =====

    def calculate_adjusted_hand_strength(self, base_strength, round_state):
        """
        Adjust hand strength for all factors.

        Combines: position, board texture, stack size, street

        Args:
            base_strength: Hand strength (0-1) from MC simulations
            round_state: Current game state

        Returns:
            float: Adjusted hand strength (0-1)
        """
        adjusted = base_strength

        # Apply position multiplier
        position = self.get_position(round_state)
        adjusted *= self.position_multiplier(position)

        # Apply board texture multiplier
        community_cards = round_state.get("community_card", [])
        texture_info = self.analyze_board_texture(community_cards)
        adjusted *= self.texture_multiplier(texture_info)

        # Apply stack multiplier
        stack_cat = self.get_stack_category(round_state)
        adjusted *= self.stack_multiplier(stack_cat)

        # Apply street multiplier
        street = self.get_street(community_cards)
        adjusted *= self.street_multiplier(street)

        # Bound to [0, 1]
        return max(0.0, min(adjusted, 1.0))

    # ===== HELPER METHODS =====

    def _rank_to_value(self, ranks):
        """Convert rank characters to numeric values."""
        rank_map = {
            'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
            '9': 9, '8': 8, '7': 7, '6': 6, '5': 5,
            '4': 4, '3': 3, '2': 2
        }
        return [rank_map.get(r, 0) for r in ranks]

    def _get_texture_description(self, texture_type):
        """Get human-readable description."""
        descriptions = {
            "dry": "Dry board - few draws possible",
            "connected": "Connected board - many draws",
            "wet": "Wet board - high variance",
            "paired": "Paired board - reduced draws",
            "semi-wet": "Semi-wet - some draws",
            "semi-connected": "Semi-connected - moderate draws",
        }
        return descriptions.get(texture_type, "Unknown texture")

    def _get_call_amount(self, round_state):
        """Extract call amount from valid actions."""
        try:
            for action in round_state.get("valid_actions", []):
                if action.get("action") == "call":
                    return action.get("amount", 0)
            return 0
        except Exception:
            return 0

    # ===== DEBUG/ANALYSIS =====

    def get_state_summary(self, round_state):
        """Return summary of current game state analysis."""
        community_cards = round_state.get("community_card", [])

        return {
            "street": self.get_street(community_cards),
            "spr": self.calculate_spr(round_state),
            "spr_category": self.get_spr_category(round_state),
            "position": self.get_position(round_state),
            "stack_category": self.get_stack_category(round_state),
            "board_texture": self.analyze_board_texture(community_cards).get("type"),
            "pot_odds": self.calculate_pot_odds(round_state),
        }

    def get_spr_category(self, round_state):
        """Convenience method for SPR category."""
        return self.get_spr_strategy(self.calculate_spr(round_state))


if __name__ == "__main__":
    analyzer = GameStateAnalyzer()

    # Test board texture analysis
    test_boards = [
        ["HA", "DA", "CA"],  # Flush draw possibility
        ["H2", "D3", "C4"],  # Connected
        ["HA", "D2", "CK"],  # Dry
        ["HA", "DA", "CA"],  # Paired (impossible but for testing)
    ]

    print("Board Texture Analysis:")
    for board in test_boards:
        texture = analyzer.analyze_board_texture(board)
        print(f"{board}: {texture['type']} - {texture['description']}")

    print("\nPosition Multipliers:")
    for pos in ["button", "small_blind", "big_blind"]:
        mult = analyzer.position_multiplier(pos)
        print(f"{pos:15s}: {mult:.2f}x")

    print("\nStack Multipliers:")
    for stack in ["deep", "medium", "short"]:
        mult = analyzer.stack_multiplier(stack)
        print(f"{stack:15s}: {mult:.2f}x")
