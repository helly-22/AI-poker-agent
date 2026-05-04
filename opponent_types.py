"""
Opponent Types: Different poker playing styles for training

Defines 8 different opponent archetypes with distinct strategies.
Each inherits from OpponentModel and overrides get_hand_range().
"""

from opponent_model import OpponentModel


class TightAggressiveOpponent(OpponentModel):
    """
    Tight Aggressive (TAG): Plays few hands, plays them hard.
    - Only plays premium hands
    - Raises frequently when playing
    - Folds weak hands quickly

    Preflop range: AA, KK, QQ, JJ, TT, 99, 88, AK, AQ, AJ, KQ
    """

    def __init__(self):
        super().__init__("TightAggressive")

    def get_hand_range(self, street, action_history=None):
        """TAG plays tight preflop, aggressive always."""
        if street == "preflop":
            return {
                "AA": 0.08, "KK": 0.07, "QQ": 0.06, "JJ": 0.05, "TT": 0.05,
                "99": 0.04, "88": 0.04,
                "AK": 0.12, "AQ": 0.08, "AJ": 0.06, "KQ": 0.05,
                "AKo": 0.08, "AQo": 0.05,
            }
        else:
            # Postflop: still tight
            return {
                "AA": 0.15, "KK": 0.12, "QQ": 0.10,
                "AK": 0.15, "AQ": 0.12,
                "Pair": 0.20,
                "Draw": 0.10,
                "Weak": 0.06,
            }

    def get_raise_frequency(self):
        return 0.70  # Very aggressive

    def get_fold_frequency(self):
        return 0.20  # Tight player who folds weak hands

    def get_bluff_frequency(self):
        return 0.15  # Some bluffs but not many


class LoosePassiveOpponent(OpponentModel):
    """
    Loose Passive (LP): Plays many hands, doesn't raise much.
    - Calls frequently
    - Rarely raises
    - Plays weak hands

    Preflop range: Most hands except worst 5%
    """

    def __init__(self):
        super().__init__("LoosePassive")

    def get_hand_range(self, street, action_history=None):
        """LP plays most hands."""
        if street == "preflop":
            # Very wide range
            return {
                "AA": 0.08, "KK": 0.07, "QQ": 0.06, "JJ": 0.05, "TT": 0.05,
                "99": 0.05, "88": 0.05, "77": 0.05, "66": 0.04, "55": 0.04,
                "AK": 0.10, "AQ": 0.08, "AJ": 0.07, "AT": 0.06,
                "KQ": 0.06, "KJ": 0.05,
                "Wheel": 0.02,  # 2-5 type hands
            }
        else:
            # Still plays wide range postflop
            return {
                "Pair": 0.30,
                "Draw": 0.20,
                "AnyTwo": 0.50,
            }

    def get_raise_frequency(self):
        return 0.10  # Very passive

    def get_fold_frequency(self):
        return 0.15  # Calls a lot

    def get_call_frequency(self):
        return 0.75  # Loves to call

    def get_bluff_frequency(self):
        return 0.05  # Doesn't bluff


class AggressiveBlufferOpponent(OpponentModel):
    """
    Aggressive Bluffer: Raises often, bluffs frequently.
    - High raise frequency
    - Bluffs often
    - Polarized range (strong hands OR bluffs)
    """

    def __init__(self):
        super().__init__("AggressiveBluffer")

    def get_hand_range(self, street, action_history=None):
        """Polarized range: premium hands or complete air."""
        if street == "preflop":
            return {
                # Premium hands (strong)
                "AA": 0.10, "KK": 0.08, "QQ": 0.07, "JJ": 0.06,
                "AK": 0.15, "AQ": 0.10,
                # Bluff hands (weak)
                "32o": 0.06, "42o": 0.06, "52o": 0.06, "62o": 0.06,
                "73o": 0.06, "83o": 0.06,
            }
        else:
            return {
                "Strong": 0.30,
                "Bluff": 0.40,
                "Medium": 0.30,
            }

    def get_raise_frequency(self):
        return 0.65  # Very aggressive

    def get_fold_frequency(self):
        return 0.25

    def get_bluff_frequency(self):
        return 0.45  # Bluffs a lot


class OnlyRaiseOpponent(OpponentModel):
    """
    Only Raise: Simplistic bot - only raises or folds.
    - No calling allowed
    - Binary strategy: raise or fold
    - Exploitable but good for testing
    """

    def __init__(self):
        super().__init__("OnlyRaise")

    def get_hand_range(self, street, action_history=None):
        """Tight range since only raises."""
        if street == "preflop":
            return {
                "AA": 0.15, "KK": 0.12, "QQ": 0.10, "JJ": 0.08,
                "AK": 0.20, "AQ": 0.12, "AJ": 0.08,
            }
        else:
            return {"Strong": 1.0}

    def get_raise_frequency(self):
        return 0.90  # Always raises

    def get_fold_frequency(self):
        return 0.10  # Folds weak hands


class OnlyCallOpponent(OpponentModel):
    """
    Only Call: Simplistic bot - only calls or folds.
    - Never raises
    - Calls frequently
    - Weak/medium hands
    """

    def __init__(self):
        super().__init__("OnlyCall")

    def get_hand_range(self, street, action_history=None):
        """Medium-weak range."""
        if street == "preflop":
            return {
                "AA": 0.06, "KK": 0.05, "QQ": 0.04, "JJ": 0.04, "TT": 0.04,
                "99": 0.04, "88": 0.04,
                "AK": 0.08, "AQ": 0.06, "AJ": 0.05, "AT": 0.04,
                "KQ": 0.05, "KJ": 0.04,
                "Any": 0.32,  # Calls with lots of hands
            }
        else:
            return {"Any": 1.0}

    def get_raise_frequency(self):
        return 0.0  # Never raises

    def get_fold_frequency(self):
        return 0.40  # Folds sometimes

    def get_call_frequency(self):
        return 0.60  # Calls most of the time


class LimperOpponent(OpponentModel):
    """
    Limper: Likes to limp (min-bet) preflop.
    - Min-bets (limps) frequently
    - Weak hand range
    - Calls postflop often
    """

    def __init__(self):
        super().__init__("Limper")

    def get_hand_range(self, street, action_history=None):
        """Very wide range, weak hands."""
        if street == "preflop":
            # Most hands
            return {
                "AA": 0.05, "KK": 0.04, "QQ": 0.03, "JJ": 0.03,
                "AK": 0.07, "AQ": 0.05,
                "Weak": 0.68,  # Lots of weak hands
            }
        else:
            return {"Any": 1.0}

    def get_raise_frequency(self):
        return 0.10  # Rarely raises

    def get_fold_frequency(self):
        return 0.20  # Limps and calls

    def get_call_frequency(self):
        return 0.70  # Calls a lot


class DefensiveOpponent(OpponentModel):
    """
    Defensive: Plays tight, folds easily.
    - Only plays premium hands
    - Folds frequently to aggression
    - Defensive play style
    """

    def __init__(self):
        super().__init__("Defensive")

    def get_hand_range(self, street, action_history=None):
        """Very tight range."""
        if street == "preflop":
            return {
                "AA": 0.15, "KK": 0.12, "QQ": 0.10,
                "AK": 0.20, "AQ": 0.15,
                "JJ": 0.08, "TT": 0.05,
            }
        else:
            return {"Premium": 1.0}

    def get_raise_frequency(self):
        return 0.20  # Rarely raises

    def get_fold_frequency(self):
        return 0.75  # Folds easily

    def get_call_frequency(self):
        return 0.05  # Doesn't call much

    def get_bluff_frequency(self):
        return 0.01  # Never bluffs


class RandomOpponent(OpponentModel):
    """
    Random: Plays completely randomly.
    - Uniform distribution across all hands
    - No strategy
    - Good baseline for testing
    """

    def __init__(self):
        super().__init__("Random")

    def get_hand_range(self, street, action_history=None):
        """Uniform across all hands."""
        return self._get_uniform_range()

    def get_raise_frequency(self):
        return 0.33  # Random

    def get_fold_frequency(self):
        return 0.33  # Random

    def get_call_frequency(self):
        return 0.34  # Random

    def get_bluff_frequency(self):
        return 0.25  # Random


def get_opponent_by_type(opponent_type):
    """
    Factory function to get opponent instance by type name.

    Args:
        opponent_type: String name of opponent type

    Returns:
        OpponentModel: Instance of requested opponent type
    """
    mapping = {
        "TightAggressive": TightAggressiveOpponent,
        "LoosePassive": LoosePassiveOpponent,
        "AggressiveBluffer": AggressiveBlufferOpponent,
        "OnlyRaise": OnlyRaiseOpponent,
        "OnlyCall": OnlyCallOpponent,
        "Limper": LimperOpponent,
        "Defensive": DefensiveOpponent,
        "Random": RandomOpponent,
    }

    if opponent_type not in mapping:
        raise ValueError(f"Unknown opponent type: {opponent_type}")

    return mapping[opponent_type]()


if __name__ == "__main__":
    # Test all opponent types
    opponent_types = [
        "TightAggressive",
        "LoosePassive",
        "AggressiveBluffer",
        "OnlyRaise",
        "OnlyCall",
        "Limper",
        "Defensive",
        "Random",
    ]

    print("Testing all opponent types:\n")
    for opp_type in opponent_types:
        opponent = get_opponent_by_type(opp_type)
        print(f"{opp_type}:")
        print(f"  Raise freq: {opponent.get_raise_frequency():.2%}")
        print(f"  Fold freq: {opponent.get_fold_frequency():.2%}")
        print(f"  Call freq: {opponent.get_call_frequency():.2%}")
        print(f"  Bluff freq: {opponent.get_bluff_frequency():.2%}")
        print()
