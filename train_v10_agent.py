"""
Training script for V10 (Trainable version)

Trains V10 by:
1. Running games against different opponent types
2. Tracking which buckets won/lost
3. Computing per-bucket adjustment factors
4. Saving learned bucket adjustments to v10_trained_buckets.json
"""

import json
import os
from datetime import datetime
from monte_carlo_v10_trainable import MonteCarloV10Trainable
from opponent_types import get_opponent_by_type
from pypokerengine.api.game import setup_config, start_poker


def train_v10_agent(games_per_opponent=30):
    """Train V10 against all opponent types"""

    opponent_types = [
        "TightAggressive",
        "LoosePassive",
        "AggressiveBluffer",
        "OnlyRaise",
        "OnlyCall",
        "Limper",
        "Defensive",
        "Random"
    ]

    print("\n" + "=" * 80)
    print("TRAINING V10: 40-Bucket Hand Abstraction with Learned Per-Bucket Adjustments")
    print("=" * 80)
    print(f"Configuration: {games_per_opponent} games per opponent type")
    print(f"Total games: {games_per_opponent * len(opponent_types)}")
    print()

    # Create a single agent instance to accumulate training across all games
    agent = MonteCarloV10Trainable()

    total_wins = 0
    total_losses = 0
    opponent_results = {}

    # Train against each opponent type
    for opp_type in opponent_types:
        print(f"\nTraining vs {opp_type}...")
        wins = 0
        losses = 0

        for game_num in range(games_per_opponent):
            try:
                # Create fresh opponent for each game
                opponent = get_opponent_by_type(opp_type)

                config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=10)
                config.register_player(name="Agent", algorithm=agent)
                config.register_player(name="Opp", algorithm=opponent)

                result = start_poker(config, verbose=0)

                if result["players"][0]["stack"] > result["players"][1]["stack"]:
                    wins += 1
                else:
                    losses += 1

                if (game_num + 1) % 10 == 0:
                    print(f"  Game {game_num + 1}/{games_per_opponent}: {wins}W-{losses}L", end='\r')

            except Exception as e:
                losses += 1
                print(f"  Error in game {game_num + 1}: {e}")

        total_wins += wins
        total_losses += losses
        wr = wins / (wins + losses) if (wins + losses) > 0 else 0

        opponent_results[opp_type] = {
            "games_played": games_per_opponent,
            "wins": wins,
            "losses": losses,
            "win_rate": wr
        }

        print(f"  {opp_type:20} {wins}W-{losses}L ({wr:.1%})")

    # Compute overall results
    overall_wr = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0

    print("\n" + "=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)
    print(f"Overall: {total_wins}W-{total_losses}L ({overall_wr:.1%})")

    # Show per-bucket performance
    print("\n" + "=" * 80)
    print("PER-BUCKET PERFORMANCE (40 buckets)")
    print("=" * 80)

    # Collect bucket stats from agent
    bucket_performance = []
    for bucket in range(40):
        bucket_info = agent.bucket_stats[bucket]
        wins = bucket_info["wins"]
        losses = bucket_info["losses"]
        total = wins + losses

        if total > 0:
            wr = wins / total
        else:
            wr = 0.5

        bucket_performance.append({
            "bucket": bucket,
            "strength_range": f"{bucket/40:.2f}-{(bucket+1)/40:.2f}",
            "wins": wins,
            "losses": losses,
            "win_rate": wr
        })

    # Print top 5 performing buckets
    top_buckets = sorted(bucket_performance, key=lambda x: x["win_rate"], reverse=True)[:5]
    print("\nTop 5 Performing Buckets:")
    for bp in top_buckets:
        print(f"  Bucket {bp['bucket']:2d} ({bp['strength_range']}): "
              f"{bp['wins']}W-{bp['losses']}L ({bp['win_rate']:.1%})")

    # Print bottom 5 performing buckets
    bottom_buckets = sorted(bucket_performance, key=lambda x: x["win_rate"])[:5]
    print("\nBottom 5 Performing Buckets:")
    for bp in bottom_buckets:
        print(f"  Bucket {bp['bucket']:2d} ({bp['strength_range']}): "
              f"{bp['wins']}W-{bp['losses']}L ({bp['win_rate']:.1%})")

    # Save learned bucket adjustments
    print("\n" + "=" * 80)
    print("SAVING TRAINED BUCKET ADJUSTMENTS")
    print("=" * 80)

    agent.save_bucket_adjustments("v10_trained_buckets.json")

    # Also save comprehensive training report
    training_report = {
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "games_per_opponent": games_per_opponent,
            "total_games": games_per_opponent * len(opponent_types)
        },
        "overall_results": {
            "wins": total_wins,
            "losses": total_losses,
            "win_rate": overall_wr
        },
        "opponent_results": opponent_results,
        "bucket_performance": bucket_performance
    }

    with open("v10_training_report.json", 'w') as f:
        json.dump(training_report, f, indent=2)

    print("✓ Saved training report to v10_training_report.json")

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE!")
    print("=" * 80)
    print(f"\nFiles created:")
    print(f"  1. v10_trained_buckets.json - Per-bucket adjustments (for loading in future games)")
    print(f"  2. v10_training_report.json - Detailed training statistics")
    print(f"\nNext steps:")
    print(f"  1. V10 will automatically load bucket adjustments on startup")
    print(f"  2. Use test_v10_vs_v6.py to compare V10 vs V6 performance")
    print(f"  3. Final win rate: {overall_wr:.1%}")
    print()

    return overall_wr


if __name__ == "__main__":
    # Parse command line arguments
    import sys
    games_per_opponent = 30  # Default

    if len(sys.argv) > 1:
        try:
            games_per_opponent = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python train_v10_agent.py [games_per_opponent]")
            print(f"Using default: {games_per_opponent} games per opponent")

    train_v10_agent(games_per_opponent)
