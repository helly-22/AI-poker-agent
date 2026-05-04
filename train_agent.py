"""
Training script for Monte Carlo Poker Agent

Trains agent against different opponent types and saves weights.
Run this BEFORE tournament to pre-compute trained weights.
"""

import json
import os
import sys
from datetime import datetime
from monte_carlo_player import MonteCarloPlayer
from opponent_types import get_opponent_by_type
from pypokerengine.api.game import setup_config, start_poker


def train_against_opponent_type(opponent_type, num_games=100):
    """
    Train agent against one opponent type for multiple games.

    Args:
        opponent_type: String name of opponent type
        num_games: Number of games to play

    Returns:
        dict: Results with win rate and statistics
    """
    print(f"\nTraining against {opponent_type}...")
    print(f"Playing {num_games} games...")

    agent = MonteCarloPlayer()
    opponent = get_opponent_by_type(opponent_type)

    wins = 0
    losses = 0
    ties = 0
    total_profit = 0

    for game_num in range(num_games):
        try:
            # Setup and run game using setup_config API
            config = setup_config(max_round=10, initial_stack=10000, small_blind_amount=10)
            config.register_player(name="MCAgent", algorithm=agent)
            config.register_player(name="Opponent", algorithm=opponent)

            # Play game
            result = start_poker(config, verbose=0)

            # Determine winner
            players = result.get("players", [])
            if len(players) >= 2:
                my_stack = players[0].get("stack", 0)
                opp_stack = players[1].get("stack", 0)

                if my_stack > opp_stack:
                    wins += 1
                    total_profit += (my_stack - 10000)
                elif my_stack < opp_stack:
                    losses += 1
                    total_profit -= (opp_stack - 10000)
                else:
                    ties += 1
            else:
                losses += 1

            # Print progress
            if (game_num + 1) % 10 == 0:
                current_wr = wins / (wins + losses + ties) if (wins + losses + ties) > 0 else 0
                print(f"  Game {game_num + 1}/{num_games}: Win rate = {current_wr:.1%}")

        except Exception as e:
            print(f"  Error in game {game_num + 1}: {e}")
            losses += 1

    # Calculate statistics
    total_games = wins + losses + ties
    win_rate = wins / total_games if total_games > 0 else 0

    results = {
        "opponent_type": opponent_type,
        "games_played": total_games,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "total_profit": total_profit,
        "avg_profit_per_game": total_profit / total_games if total_games > 0 else 0,
    }

    print(f"  Results: {wins}W-{losses}L ({win_rate:.1%}), Profit: ${total_profit}")

    return results


def extract_opponent_strategies(opponent_types_list, all_results):
    """Extract opponent strategies from training results."""
    opponent_strategies = {}

    for opp_type in opponent_types_list:
        if "error" in all_results.get(opp_type, {}):
            continue

        opponent = get_opponent_by_type(opp_type)
        strategy = {
            "description": opponent.name if hasattr(opponent, 'name') else opp_type,
            "raise_frequency": getattr(opponent, 'raise_frequency', 0.33),
            "call_frequency": getattr(opponent, 'call_frequency', 0.33),
            "fold_frequency": getattr(opponent, 'fold_frequency', 0.33),
            "bluff_frequency": getattr(opponent, 'bluff_frequency', 0.0),
        }
        opponent_strategies[opp_type] = strategy

    return opponent_strategies


def build_decision_thresholds(all_results):
    """Build decision thresholds based on training win rates."""
    win_rates = [r.get('win_rate', 0.5) for r in all_results.values() if 'win_rate' in r]
    avg_wr = sum(win_rates) / len(win_rates) if win_rates else 0.5
    adjustment = (avg_wr - 0.5) * 2

    return {
        "preflop": {
            "raise_threshold": max(0.50, min(0.75, 0.65 + adjustment * 0.05)),
            "call_threshold": max(0.30, min(0.60, 0.45 + adjustment * 0.05)),
            "fold_threshold": max(0.10, min(0.40, 0.25 + adjustment * 0.05)),
        },
        "flop": {
            "raise_threshold": max(0.45, min(0.70, 0.60 + adjustment * 0.05)),
            "call_threshold": max(0.25, min(0.55, 0.40 + adjustment * 0.05)),
            "fold_threshold": max(0.05, min(0.35, 0.20 + adjustment * 0.05)),
        },
        "turn": {
            "raise_threshold": max(0.40, min(0.65, 0.55 + adjustment * 0.05)),
            "call_threshold": max(0.20, min(0.50, 0.35 + adjustment * 0.05)),
            "fold_threshold": max(0.05, min(0.35, 0.20 + adjustment * 0.05)),
        },
        "river": {
            "raise_threshold": max(0.35, min(0.60, 0.50 + adjustment * 0.05)),
            "call_threshold": max(0.15, min(0.45, 0.30 + adjustment * 0.05)),
            "fold_threshold": max(0.00, min(0.30, 0.15 + adjustment * 0.05)),
        },
    }


def build_classification_thresholds(all_results):
    """Build thresholds to identify opponent types during tournament play."""
    return {
        "tight_aggressive_raise_threshold": 0.65,
        "loose_passive_call_threshold": 0.70,
        "defensive_fold_threshold": 0.70,
        "min_hands_to_classify": 15,
    }


def save_trained_weights(opponent_types_list, all_results):
    """Extract and save lightweight trained weights for tournament deployment."""
    opponent_strategies = extract_opponent_strategies(opponent_types_list, all_results)
    decision_thresholds = build_decision_thresholds(all_results)
    classification_thresholds = build_classification_thresholds(all_results)

    trained_weights = {
        "training_timestamp": datetime.now().isoformat(),
        "opponent_strategies": opponent_strategies,
        "decision_thresholds": decision_thresholds,
        "classification_thresholds": classification_thresholds,
        "training_results": all_results,
    }

    with open("trained_weights.json", "w") as f:
        json.dump(trained_weights, f, indent=2)

    print("\n✓ Trained weights saved to trained_weights.json")
    return trained_weights


def main():
    """Main training loop."""
    # Parse command line arguments
    num_games = 100
    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python train_agent.py [num_games]")
            print(f"Using default: {num_games} games")

    opponent_types_list = [
        "TightAggressive",
        "LoosePassive",
        "AggressiveBluffer",
        "OnlyRaise",
        "OnlyCall",
        "Limper",
        "Defensive",
        "Random",
    ]

    print("=" * 60)
    print("MONTE CARLO POKER AGENT - TRAINING PIPELINE")
    print("=" * 60)
    print(f"Training against {len(opponent_types_list)} opponent types")
    print(f"Games per opponent: {num_games}")
    print(f"Total games: {len(opponent_types_list) * num_games}")
    print("=" * 60)

    # Train against each opponent type
    all_results = {}
    for opponent_type in opponent_types_list:
        try:
            results = train_against_opponent_type(opponent_type, num_games)
            all_results[opponent_type] = results
        except Exception as e:
            print(f"ERROR training against {opponent_type}: {e}")
            all_results[opponent_type] = {"error": str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    total_wins = sum(r.get("wins", 0) for r in all_results.values() if "wins" in r)
    total_losses = sum(r.get("losses", 0) for r in all_results.values() if "losses" in r)
    total_games_played = total_wins + total_losses
    overall_wr = total_wins / total_games_played if total_games_played > 0 else 0

    print(f"Overall Win Rate: {total_wins}W-{total_losses}L ({overall_wr:.1%})")
    print(f"Total Games Played: {total_games_played}")

    for opponent_type, results in all_results.items():
        if "error" in results:
            print(f"  {opponent_type}: ERROR - {results['error']}")
        else:
            wr = results.get("win_rate", 0)
            wins = results.get("wins", 0)
            losses = results.get("losses", 0)
            print(f"  {opponent_type}: {wins}W-{losses}L ({wr:.1%})")

    # Save weights
    print()
    save_trained_weights(opponent_types_list, all_results)

    # Save summary
    with open("training_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print("✓ Training results saved to training_results.json")
    print("\n" + "=" * 60)
    print("Training complete! Agent is ready for tournament.")
    print("=" * 60)


if __name__ == "__main__":
    main()
