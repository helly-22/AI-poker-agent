# Poker Agent Performance Comparison

## Final Results (Extended Test: 30 games per opponent = 150 total games)

| Agent | Performance | Notes |
|-------|-------------|-------|
| **V6 Dynamic** | **92.0%** | ✅ WINNER - Most stable & reliable |
| V10 Advanced Learning | 90.7% | Good variance, per-bucket tracking |
| V8 Enhanced | 83.8% | Pot odds + SPR only |

---

## V6 Dynamic (RECOMMENDED FOR SUBMISSION)
**Win Rate: 92.0% (138W-12L)**

### What it does:
- Loads pre-trained decision thresholds from `trained_weights.json`
- Uses hard-coded hand strength evaluation (poker theory)
- Street-specific thresholds (preflop: 0.688, flop: 0.638, turn: 0.588, river: 0.538)

### Breakdown:
- TightAggressive: 90.0%
- LoosePassive: 86.7%
- Defensive: 100.0%
- Random: 96.7%
- AggressiveBluffer: 86.7%

### Why it wins:
- Simple, stable, no overfitting
- Thresholds learned from 240 training games (30 games × 8 opponents)
- Consistent performance across multiple tests
- Clean separation: hard-coded hand eval + learned thresholds

---

## V10 Advanced Learning
**Win Rate: 90.7% (136W-14L)**

### What it does:
- Classifies hands into 40 strength buckets
- Tracks performance per bucket over last 40 rounds
- Adjusts thresholds per bucket based on recent win rates
- Falls back to V6's base thresholds if insufficient data

### Breakdown:
- TightAggressive: 90.0%
- LoosePassive: 86.7%
- Defensive: 100.0%
- Random: 90.0%
- AggressiveBluffer: 86.7%

### Why it's slightly worse:
- Online learning introduces variance
- 40-round window has noise in poker's high-variance environment
- Per-bucket adjustments can be too aggressive
- Slightly underperforms in larger samples

---

## V8 Enhanced (Reference Only)
**Win Rate: 83.8%**

- Attempted: V6 + pot odds + SPR
- Result: Complexity hurt performance
- Lesson: Adding features doesn't always help

---

## Recommendation

**Use V6 Dynamic for the tournament submission.**

- **Most reliable**: 92% win rate proven across extended testing
- **Simplest**: Easy to understand, debug, and deploy
- **Fastest**: No per-round learning overhead
- **Proven**: Consistent results across different opponent types

Files needed for submission:
1. `monte_carlo_v6_dynamic.py` - The agent code
2. `trained_weights.json` - The learned thresholds
3. `opponent_model.py` - Opponent simulation (if required)
4. `opponent_types.py` - Opponent type definitions (if required)

---

## Training Details (V6)

**Training command:**
```bash
python train_agent.py --games_per_opponent 30
```

**Result:**
- 30 games × 8 opponent types = 240 total training games
- Overall training win rate: 88.7% (211W-27L)
- Trained weights timestamp: 2026-05-03T05:20:51.607837

**Learned thresholds:**
```json
{
  "preflop": {"raise": 0.688, "call": 0.488},
  "flop": {"raise": 0.638, "call": 0.438},
  "turn": {"raise": 0.588, "call": 0.388},
  "river": {"raise": 0.538, "call": 0.338}
}
```

---

## Key Insights

1. **Simplicity wins**: V6's straightforward approach beats V7, V8, V10's complex variants
2. **Hard-coded poker theory + learned thresholds = optimal balance**
3. **Online learning introduces noise** in high-variance games
4. **Street-specific thresholds matter**: play tighter preflop, looser river
5. **Trained weights > arbitrary defaults**: V6 beats BASELINE by ~5%

---

## Files in `old_versions/`

- monte_carlo_v1_hand_abstraction.py
- monte_carlo_v2_board_texture.py
- monte_carlo_v3_street_aware.py
- monte_carlo_v4_spr.py
- monte_carlo_v5_hybrid.py
- monte_carlo_v7_advanced.py
- monte_carlo_v9_online_learning.py
- (All related test files)

These were tested and underperformed. Archived for reference only.
