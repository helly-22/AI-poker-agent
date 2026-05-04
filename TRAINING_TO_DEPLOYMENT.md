# Training to Deployment: Data Storage Strategy

## The Problem

We need to:
1. **Train offline** - Learn from playing against different opponents
2. **Save knowledge** - Store what we learned
3. **Deploy at tournament** - Load and use learned information
4. **Play fast** - Make decisions in ~0.5 seconds (no retraining)

---

## Current Implementation Status

### ✅ What Gets Saved Now
- `trained_weights.json` - Minimal (just a placeholder currently)
- `training_results.json` - Results from training run

### ❌ What's Missing
- Learned hand strength adjustments
- Opponent tendency data
- Per-street strategy parameters
- Classification thresholds

---

## Proposed Storage Strategy

### Option 1: Lightweight (Current Approach) ✅ RECOMMENDED

**Store only what's necessary for fast tournament play:**

```json
{
  "metadata": {
    "training_date": "2026-05-02T10:30:00",
    "training_games": 500,
    "overall_win_rate": 0.58,
    "opponent_types_trained": ["Random", "TightAggressive", "LoosePassive", ...]
  },
  "opponent_strategies": {
    "TightAggressive": {
      "preflop_raise_frequency": 0.70,
      "postflop_cbet_frequency": 0.75,
      "fold_to_aggression": 0.30,
      "hand_range": {"AA": 0.08, "KK": 0.07, ...}
    },
    "LoosePassive": {
      "preflop_raise_frequency": 0.10,
      "postflop_cbet_frequency": 0.45,
      "fold_to_aggression": 0.15,
      "hand_range": {...}
    }
    ...
  },
  "decision_thresholds": {
    "preflop": {
      "strong_hand": 0.70,
      "marginal_hand": 0.50,
      "weak_hand": 0.30
    },
    "flop": {
      "strong_hand": 0.65,
      "marginal_hand": 0.45,
      "weak_hand": 0.25
    },
    ...
  },
  "feature_multipliers": {
    "position": {
      "button": 1.15,
      "small_blind": 1.10,
      "big_blind": 0.90
    },
    "board_texture": {
      "dry": 1.15,
      "connected": 0.95,
      "wet": 0.85
    },
    "spr": {
      "deep": 1.10,
      "medium": 1.0,
      "short": 0.90
    }
  }
}
```

**Advantages:**
- Small file size (~50KB)
- Fast to load (ms)
- Easy to understand and debug
- Sufficient for tournament play

---

### Option 2: Comprehensive (For Advanced Analysis)

**Store everything for maximum learning:**

```json
{
  "metadata": {...},
  "opponent_models": {
    "TightAggressive": {
      "action_history": [...],
      "shown_hands": [...],
      "win_loss_record": {"wins": 45, "losses": 12},
      "preflop_tendencies": {...},
      "flop_tendencies": {...},
      "turn_tendencies": {...},
      "river_tendencies": {...},
      "hand_ranges_by_street": {...}
    },
    ...
  },
  "hand_strength_data": {
    "preflop": {
      "AA": 0.865,
      "KK": 0.820,
      "QQ": 0.775,
      ...
    }
  },
  "training_history": [
    {"opponent": "Random", "games": 100, "win_rate": 0.52},
    {"opponent": "TightAggressive", "games": 100, "win_rate": 0.55},
    ...
  ]
}
```

**Disadvantages:**
- Large file size (several MB)
- Slow to load
- Unnecessary for tournament play

---

## Recommended: Hybrid Approach

### Phase 1: Training (Offline)
**Store EVERYTHING for analysis:**

```python
def save_training_data(training_results, agents_trained):
    """Save comprehensive training data"""
    
    full_data = {
        "timestamp": datetime.now().isoformat(),
        "training_results": training_results,
        "agents": {
            agent_name: {
                "opponent_model": agent.opponent_model.__dict__,
                "win_rate": agent.calculate_win_rate(),
                "opponent_streets": agent.opponent_streets,
                "game_history": agent.game_history,
            }
            for agent_name, agent in agents_trained.items()
        }
    }
    
    # Save everything
    with open("training_data_full.json", 'w') as f:
        json.dump(full_data, f, indent=2)
    
    # Extract key insights
    deployment_weights = extract_deployment_weights(full_data)
    with open("trained_weights.json", 'w') as f:
        json.dump(deployment_weights, f, indent=2)
```

### Phase 2: Deployment (Tournament)
**Load ONLY what's needed:**

```python
class MonteCarloPlayer(BasePokerPlayer):
    def __init__(self):
        self.weights = self._load_weights()
        self.opponent_classifier = OpponentClassifier(self.weights)
    
    def _load_weights(self):
        """Load pre-trained weights"""
        try:
            with open("trained_weights.json", 'r') as f:
                return json.load(f)
        except:
            return self._get_default_weights()
    
    def declare_action(self, valid_actions, hole_card, round_state):
        # Identify opponent type from recent behavior
        opponent_type = self.opponent_classifier.classify(
            self.opponent_streets
        )
        
        # Get pre-trained strategy for this opponent
        strategy = self.weights["opponent_strategies"].get(
            opponent_type,
            self.weights["opponent_strategies"]["Random"]  # Fallback
        )
        
        # Use strategy in decision making
        ...
```

---

## What to Store: Detailed Breakdown

### 1. **Opponent Strategies** (MUST STORE)

```json
{
  "opponent_strategies": {
    "OpponentName": {
      "preflop_raise_frequency": 0.70,
      "postflop_cbet_frequency": 0.75,
      "fold_to_aggression": 0.30,
      "call_frequency": 0.50,
      "bluff_frequency": 0.15,
      "hand_range_by_street": {
        "preflop": {
          "AA": 0.08,
          "KK": 0.07,
          ...
        },
        "flop": {...},
        "turn": {...},
        "river": {...}
      }
    }
  }
}
```

**Why?** This is the core of opponent modeling. Without it, you're back to assuming uniform ranges.

### 2. **Decision Thresholds** (SHOULD STORE)

```json
{
  "decision_thresholds": {
    "preflop": {
      "strong_hand": 0.70,
      "raise_threshold": 0.65,
      "call_threshold": 0.45,
      "fold_threshold": 0.25
    },
    "flop": {...},
    "turn": {...},
    "river": {...}
  }
}
```

**Why?** Different streets have different optimal play. Storing thresholds avoids hard-coding.

### 3. **Opponent Classification** (NICE TO HAVE)

```json
{
  "opponent_classification": {
    "identification_thresholds": {
      "raise_frequency_tight_aggressive": 0.65,
      "fold_frequency_defensive": 0.70,
      "call_frequency_loose_passive": 0.70
    },
    "min_hands_to_classify": 15
  }
}
```

**Why?** Let you identify opponent type after seeing ~15 hands, then switch strategies.

### 4. **Hand Strength Adjustments** (OPTIONAL)

```json
{
  "hand_strength_adjustments": {
    "vs_tight_aggressive": {
      "position_multiplier": 1.15,
      "texture_multiplier": 1.10,
      "recommended_spr_strategy": "short"
    },
    "vs_loose_passive": {...}
  }
}
```

**Why?** Fine-tune play against each opponent type.

---

## Implementation: Load & Use Training Data

### During Tournament Play

```python
class MonteCarloPlayerWithLearning(MonteCarloPlayer):
    
    def __init__(self):
        super().__init__()
        self.trained_weights = self._load_trained_weights()
        self.opponent_type_guess = None
        self.opponent_action_count = 0
    
    def declare_action(self, valid_actions, hole_card, round_state):
        # Try to identify opponent after ~15 hands
        if self.opponent_action_count >= 15 and not self.opponent_type_guess:
            self.opponent_type_guess = self._classify_opponent()
        
        # If we've identified opponent, use their trained strategy
        if self.opponent_type_guess:
            strategy = self.trained_weights["opponent_strategies"].get(
                self.opponent_type_guess
            )
            # Use strategy to adjust decisions
            return self._decide_with_strategy(
                valid_actions,
                hole_card,
                round_state,
                strategy
            )
        else:
            # Fallback to generic strategy during learning phase
            return super().declare_action(valid_actions, hole_card, round_state)
    
    def _classify_opponent(self):
        """Identify which trained opponent type this matches"""
        
        # Get opponent's stats from round_history
        raise_freq = self.opponent_model.get_raise_frequency()
        fold_freq = self.opponent_model.get_fold_frequency()
        call_freq = self.opponent_model.get_call_frequency()
        
        thresholds = self.trained_weights["classification_thresholds"]
        
        # Match to closest opponent type
        if raise_freq > thresholds["tight_aggressive_raise"]:
            return "TightAggressive"
        elif call_freq > thresholds["loose_passive_call"]:
            return "LoosePassive"
        elif fold_freq > thresholds["defensive_fold"]:
            return "Defensive"
        else:
            return "Random"  # Fallback
    
    def _decide_with_strategy(self, valid_actions, hole_card, round_state, strategy):
        """Make decision using opponent's trained strategy"""
        
        # Get base hand strength
        community_cards = round_state.get("community_card", [])
        street = self.analyzer.get_street(community_cards)
        
        hand_strength = self.evaluator.get_hand_strength_vs_range(
            hole_card,
            community_cards,
            strategy["hand_range_by_street"][street]  # Use THEIR range!
        )
        
        # Apply adjustment from trained strategy
        adjustment = strategy.get("hand_strength_adjustment", 1.0)
        adjusted_strength = hand_strength * adjustment
        
        # Get thresholds for this street
        thresholds = self.trained_weights["decision_thresholds"][street]
        
        # Make decision based on trained thresholds
        if adjusted_strength > thresholds["raise_threshold"]:
            return self._format_action("raise", valid_actions)
        elif adjusted_strength > thresholds["call_threshold"]:
            return self._format_action("call", valid_actions)
        else:
            return self._format_action("fold", valid_actions)
    
    def _load_trained_weights(self):
        """Load pre-trained strategies"""
        try:
            with open("trained_weights.json", 'r') as f:
                return json.load(f)
        except:
            return self._get_default_weights()
    
    def _get_default_weights(self):
        """Fallback if no training data"""
        return {
            "opponent_strategies": {
                "Random": {
                    "raise_frequency": 0.33,
                    "hand_range_by_street": {
                        "preflop": self._uniform_range(),
                        "flop": self._uniform_range(),
                        "turn": self._uniform_range(),
                        "river": self._uniform_range(),
                    }
                }
            },
            "decision_thresholds": {
                "preflop": {"raise_threshold": 0.65, "call_threshold": 0.45},
                "flop": {"raise_threshold": 0.60, "call_threshold": 0.40},
                "turn": {"raise_threshold": 0.55, "call_threshold": 0.35},
                "river": {"raise_threshold": 0.50, "call_threshold": 0.30},
            },
            "classification_thresholds": {
                "tight_aggressive_raise": 0.65,
                "loose_passive_call": 0.70,
                "defensive_fold": 0.70,
            }
        }
```

---

## File Structure After Training

```
After Training Run:
├── trained_weights.json          ← LOAD THIS AT TOURNAMENT (small, fast)
├── training_results.json         ← Summary statistics
├── training_data_full.json       ← Complete history (for analysis, not needed at tournament)
└── training_logs/
    └── [timestamp]_training.log  ← Detailed training log
```

---

## Storage by Phase

### Training Phase
```
train_agent.py → plays thousands of games
  ↓
Collect statistics from each game
  ↓
Save to: trained_weights.json (light) + training_data_full.json (heavy)
  ↓
Extract key insights
```

### Tournament Phase
```
monte_carlo_player.py starts
  ↓
Load: trained_weights.json (fast, ~5ms)
  ↓
Classify opponent (after ~15 hands)
  ↓
Use opponent-specific strategies
  ↓
Play optimally at tournament
```

---

## Recommended Storage Format

Use JSON for simplicity and debugging:

```json
{
  "version": "1.0",
  "training_metadata": {
    "date": "2026-05-02T15:30:00Z",
    "total_games": 500,
    "overall_win_rate": 0.57,
    "game_duration_minutes": 125
  },
  "opponent_strategies": {
    "TightAggressive": {
      "description": "Plays tight, raises often",
      "raise_frequency": 0.70,
      "fold_frequency": 0.20,
      "call_frequency": 0.50,
      "bluff_frequency": 0.15,
      "preflop_range": {"AA": 0.08, "KK": 0.07, ...},
      "postflop_range": {...}
    },
    ...
  },
  "decision_framework": {
    "by_street": {
      "preflop": {
        "raise_threshold": 0.65,
        "call_threshold": 0.45,
        "fold_threshold": 0.20
      },
      ...
    }
  }
}
```

---

## Summary: What to Store

| Item | Store? | Size | Purpose |
|------|--------|------|---------|
| Opponent strategies | ✅ YES | 20KB | Core learning |
| Decision thresholds | ✅ YES | 2KB | Street-specific play |
| Classification rules | ✅ YES | 1KB | Identify opponent type |
| Training history | ⭕ MAYBE | 50KB | Analysis only |
| Full game logs | ❌ NO | 10MB+ | Not needed |
| Hand strength tables | ❌ NO | 1MB | Computed on-the-fly |

**Total for tournament: ~25KB** - Loads in <10ms

---

## Implementation Roadmap

```
1. Add save_training_weights() function to train_agent.py
2. Enhance monte_carlo_player to load and use weights
3. Implement opponent classification based on stored thresholds
4. Add fallback to defaults if weights missing
5. Test with training_results.json
6. Package trained_weights.json with submission
```

---

## Ready to Implement?

Would you like me to:
1. Add the save/load functions to the code?
2. Create the trained_weights.json schema?
3. Implement opponent classification based on training data?
4. All of the above?
