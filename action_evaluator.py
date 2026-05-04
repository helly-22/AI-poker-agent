"""
Action Evaluator: Calculate expected value (EV) of poker actions

For each valid action (fold, call, check, raise), calculates expected value
based on hand strength and opponent model.
"""


class ActionEvaluator:
    """
    Evaluates expected value of each action in poker.

    EV = (Probability of Win * Amount Won) - (Probability of Loss * Amount Bet)
    """

    def __init__(self, hand_strength_evaluator):
        """
        Args:
            hand_strength_evaluator: HandStrengthEvaluator instance
        """
        self.evaluator = hand_strength_evaluator

    def evaluate_all_actions(self, hole_card, round_state, opponent_model):
        """
        Calculate EV for all valid actions.

        Args:
            hole_card: Your 2 cards
            round_state: Current game state dict with:
                - pot: current pot size
                - community_card: board cards
                - seats: player info
                - small_blind_pos: position of small blind
            opponent_model: OpponentModel instance with estimated hand range

        Returns:
            dict: {action_name: ev_value}
                  e.g., {"fold": 0.5, "call": 1.2, "raise": 2.1}
        """
        valid_actions = self._extract_valid_actions(round_state)
        community_cards = round_state.get("community_card", [])
        pot = round_state.get("pot", 0)

        # Get hand strength vs opponent's estimated range
        opponent_range = opponent_model.get_hand_range(
            self._get_street(community_cards),
            round_state
        )

        hand_strength = self.evaluator.get_hand_strength_vs_range(
            hole_card,
            community_cards,
            opponent_range,
            num_sims=500  # Faster with fewer sims
        )

        # Calculate EV for each action
        action_evs = {}
        for action_info in valid_actions:
            action_type = action_info.get("action")
            ev = self._calculate_action_ev(
                action_type,
                hand_strength,
                pot,
                round_state,
                opponent_model
            )
            action_evs[action_type] = ev

        return action_evs

    def _calculate_action_ev(self, action_type, hand_strength, pot, round_state, opponent_model):
        """
        Calculate EV for a specific action.

        Args:
            action_type: "fold", "call", "check", or "raise"
            hand_strength: Float 0-1 (probability of winning)
            pot: Current pot size
            round_state: Game state
            opponent_model: Opponent behavior model

        Returns:
            float: Expected value of this action
        """
        if action_type == "fold":
            # Folding has 0 EV from this point (you lose what's in pot)
            return 0.0

        elif action_type == "call":
            call_amount = self._get_call_amount(round_state)
            if call_amount is None:
                return 0.0

            # EV = (hand_strength * pot) - ((1 - hand_strength) * call_amount)
            ev = (hand_strength * pot) - ((1 - hand_strength) * call_amount)
            return ev

        elif action_type == "check":
            # Checking is like calling $0
            # EV = hand_strength * current_pot
            return hand_strength * pot

        elif action_type == "raise":
            raise_amount = self._get_raise_amount(round_state)
            call_amount = self._get_call_amount(round_state)

            if raise_amount is None or call_amount is None:
                return 0.0

            # Two scenarios:
            # 1. Opponent folds to raise
            # 2. Opponent calls the raise

            opponent_fold_prob = opponent_model.get_fold_frequency()
            opponent_fold_prob = min(0.95, max(0.05, opponent_fold_prob))  # Bound it

            # EV if opponent folds: win the current pot
            ev_if_fold = pot

            # EV if opponent calls: go to showdown with larger pot
            # Bet amount is raise_amount, opponent must call that
            total_bet = raise_amount
            new_pot = pot + total_bet + call_amount

            ev_if_call = (hand_strength * new_pot) - ((1 - hand_strength) * total_bet)

            # Weighted average
            ev = (opponent_fold_prob * ev_if_fold) + ((1 - opponent_fold_prob) * ev_if_call)

            return ev

        return 0.0

    def _extract_valid_actions(self, round_state):
        """
        Extract valid actions from game state.

        Args:
            round_state: Game state dict

        Returns:
            list: List of valid action dicts
        """
        return round_state.get("valid_actions", [])

    def _get_call_amount(self, round_state):
        """
        Get the amount needed to call.

        Args:
            round_state: Game state

        Returns:
            float or None: Amount to call, or None if no valid call
        """
        try:
            valid_actions = round_state.get("valid_actions", [])
            for action in valid_actions:
                if action.get("action") == "call":
                    return action.get("amount", 0)
            return None
        except:
            return None

    def _get_raise_amount(self, round_state):
        """
        Get the raise amount.

        Args:
            round_state: Game state

        Returns:
            float or None: Raise amount, or None if no valid raise
        """
        try:
            valid_actions = round_state.get("valid_actions", [])
            for action in valid_actions:
                if action.get("action") == "raise":
                    # The "amount" field varies by implementation
                    # Try to get the raise amount
                    if "amount" in action:
                        return action.get("amount", 10)
                    else:
                        return 10  # Default raise amount
            return None
        except:
            return None

    def _get_street(self, community_cards):
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

    def pick_best_action(self, action_evs, valid_actions):
        """
        Pick action with highest EV from calculated EVs.

        Args:
            action_evs: Dict of {action: ev_value}
            valid_actions: List of valid action dicts

        Returns:
            str: Best action name ("fold", "call", etc.)
        """
        # Filter to only valid actions
        valid_action_names = {a.get("action") for a in valid_actions}

        # Get best action
        best_action = None
        best_ev = float('-inf')

        for action_name, ev in action_evs.items():
            if action_name in valid_action_names and ev > best_ev:
                best_ev = ev
                best_action = action_name

        # Fallback: call if available
        if best_action is None:
            if "call" in valid_action_names:
                best_action = "call"
            elif "check" in valid_action_names:
                best_action = "check"
            else:
                best_action = "fold"

        return best_action

    def get_action_summary(self, action_evs):
        """Return summary of action EVs."""
        if not action_evs:
            return "No actions to evaluate"

        lines = ["Action EV Summary:"]
        for action, ev in sorted(action_evs.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {action}: {ev:.2f}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Simple test
    from hand_strength_evaluator import HandStrengthEvaluator
    from opponent_types import get_opponent_by_type

    evaluator = HandStrengthEvaluator(num_simulations=500)
    action_eval = ActionEvaluator(evaluator)

    # Create a mock round state
    round_state = {
        "pot": 100,
        "community_card": ["HA", "HK", "HQ"],
        "valid_actions": [
            {"action": "fold"},
            {"action": "call", "amount": 50},
            {"action": "raise", "amount": 100},
        ],
        "seats": [],
    }

    hole_card = ["CA", "DA"]
    opponent = get_opponent_by_type("TightAggressive")

    # Evaluate actions
    action_evs = action_eval.evaluate_all_actions(hole_card, round_state, opponent)

    print(action_eval.get_action_summary(action_evs))
    best = action_eval.pick_best_action(action_evs, round_state["valid_actions"])
    print(f"\nBest action: {best}")
