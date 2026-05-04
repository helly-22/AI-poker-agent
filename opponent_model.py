"""Opponent Model: Estimates opponent's hand ranges"""

from pypokerengine.players import BasePokerPlayer
import random


class OpponentModel(BasePokerPlayer):
    """Base class for modeling opponent behavior in poker."""

    def __init__(self, name="OpponentModel"):
        self.name = name
        self.action_history = []
        self.shown_hands = []
        self.win_loss_record = {"wins": 0, "losses": 0}

    def get_hand_range(self, street, action_history=None):
        """Get estimated opponent hand range."""
        return self._get_uniform_range()

    def estimate_hand_from_actions(self, round_state, betting_actions):
        """Estimate hand range based on specific actions."""
        return self._get_uniform_range()

    def update_from_result(self, opponent_hole_card, result):
        """Update model after seeing opponent's hand."""
        self.shown_hands.append({"cards": opponent_hole_card, "result": result})
        if result == "win":
            self.win_loss_record["wins"] += 1
        elif result == "loss":
            self.win_loss_record["losses"] += 1

    def get_raise_frequency(self):
        """Probability of raising when acting."""
        return 0.33

    def get_call_frequency(self):
        """Probability of calling when acting."""
        return 0.33

    def get_fold_frequency(self):
        """Probability of folding when acting."""
        return 0.33

    def get_bluff_frequency(self):
        """Probability of bluffing with weak hand."""
        return 0.0

    def add_action(self, action):
        """Add action to history."""
        self.action_history.append(action)

    def _get_uniform_range(self):
        """Return uniform distribution over all 169 starting hands."""
        hands = ["AA", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                 "AKo", "KK", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
                 "AQo", "KQo", "QQ", "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
                 "AJo", "KJo", "QJo", "JJ", "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
                 "ATo", "KTo", "QTo", "JTo", "TT", "T9s", "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s",
                 "A9o", "K9o", "Q9o", "J9o", "T9o", "99", "98s", "97s", "96s", "95s", "94s", "93s", "92s",
                 "A8o", "K8o", "Q8o", "J8o", "T8o", "98o", "88", "87s", "86s", "85s", "84s", "83s", "82s",
                 "A7o", "K7o", "Q7o", "J7o", "T7o", "97o", "87o", "77", "76s", "75s", "74s", "73s", "72s",
                 "A6o", "K6o", "Q6o", "J6o", "T6o", "96o", "86o", "76o", "66", "65s", "64s", "63s", "62s",
                 "A5o", "K5o", "Q5o", "J5o", "T5o", "95o", "85o", "75o", "65o", "55", "54s", "53s", "52s",
                 "A4o", "K4o", "Q4o", "J4o", "T4o", "94o", "84o", "74o", "64o", "54o", "44", "43s", "42s",
                 "A3o", "K3o", "Q3o", "J3o", "T3o", "93o", "83o", "73o", "63o", "53o", "43o", "33", "32s",
                 "A2o", "K2o", "Q2o", "J2o", "T2o", "92o", "82o", "72o", "62o", "52o", "42o", "32o", "22"]
        return {k: 1.0/169 for k in hands}

    def get_summary(self):
        """Return summary of opponent model."""
        return {"name": self.name, "actions": len(self.action_history), "shown_hands": len(self.shown_hands)}

    def declare_action(self, valid_actions, hole_card, round_state):
        """Required by BasePokerPlayer: decide an action - returns action string."""
        raise_freq = self.get_raise_frequency()
        call_freq = self.get_call_frequency()
        fold_freq = self.get_fold_frequency()

        total = raise_freq + call_freq + fold_freq
        if total == 0:
            total = 1
        raise_freq /= total
        call_freq /= total
        fold_freq /= total

        rand = random.random()

        # Try raise
        if rand < raise_freq:
            for action in valid_actions:
                if action["action"] == "raise":
                    return "raise"

        # Try call
        if rand < raise_freq + call_freq:
            for action in valid_actions:
                if action["action"] == "call":
                    return "call"

        # Try check
        for action in valid_actions:
            if action["action"] == "check":
                return "check"

        # Try fold
        for action in valid_actions:
            if action["action"] == "fold":
                return "fold"

        return "fold"

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

