"""
Test different Monte Carlo abstractions to find the best one.
Compares win rates across different versions.
"""

from monte_carlo_player import MonteCarloPlayer
from monte_carlo_v1_hand_abstraction import MonteCarloV1HandAbstraction
from opponent_types import get_opponent_by_type
from pypokerengine.api.game import setup_config, start_poker


def test_agent_vs_opponent(agent_class, agent_name, opponent_type, num_games=20):
    """Test an agent against a specific opponent"""
    print(f"\n  Testing {agent_name} vs {opponent_type}...")

    agent = agent_class()
    opponent = get_opponent_by_type(opponent_type)

    wins = 0
    losses = 0

    for game_num in range(num_games):
        try:
            config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=10)
            config.register_player(name="TestAgent", algorithm=agent)
            config.register_player(name="Opponent", algorithm=opponent)

            result = start_poker(config, verbose=0)

            if "players" in result and len(result["players"]) >= 2:
                my_stack = result["players"][0].get("stack", 0)
                opp_stack = result["players"][1].get("stack", 0)

                if my_stack > opp_stack:
                    wins += 1
                else:
                    losses += 1
            else:
                losses += 1

        except Exception as e:
            print(f"    Error in game {game_num + 1}: {e}")
            losses += 1

    win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
    return wins, losses, win_rate


def main():
    """Test all versions against multiple opponents"""

    agents = [
        (MonteCarloPlayer, "BASELINE (Current)"),
        (MonteCarloV1HandAbstraction, "V1 (Hand Abstraction)"),
    ]

    opponents = [
        "TightAggressive",
        "LoosePassive",
        "Random",
        "Defensive",
    ]

    print("=" * 70)
    print("MONTE CARLO ABSTRACTION TESTING")
    print("=" * 70)
    print(f"Testing {len(agents)} agent versions")
    print(f"Against {len(opponents)} opponent types")
    print(f"20 games per matchup\n")

    results = {}

    for agent_class, agent_name in agents:
        print(f"\n{'=' * 70}")
        print(f"AGENT: {agent_name}")
        print(f"{'=' * 70}")

        agent_results = {}
        total_wins = 0
        total_losses = 0

        for opponent_type in opponents:
            wins, losses, wr = test_agent_vs_opponent(agent_class, agent_name, opponent_type, 20)
            agent_results[opponent_type] = {"wins": wins, "losses": losses, "wr": wr}
            total_wins += wins
            total_losses += losses

            print(f"    {opponent_type}: {wins}W-{losses}L ({wr:.1%})")

        overall_wr = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0
        agent_results["OVERALL"] = {"wins": total_wins, "losses": total_losses, "wr": overall_wr}
        results[agent_name] = agent_results

        print(f"\n  OVERALL: {total_wins}W-{total_losses}L ({overall_wr:.1%})")

    # Summary
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    agent_names = [name for _, name in agents]
    for opponent_type in opponents + ["OVERALL"]:
        print(f"\n{opponent_type}:")
        for agent_name in agent_names:
            wr = results[agent_name][opponent_type]["wr"]
            wins = results[agent_name][opponent_type]["wins"]
            losses = results[agent_name][opponent_type]["losses"]
            print(f"  {agent_name}: {wins}W-{losses}L ({wr:.1%})")

    # Determine winner
    print("\n" + "=" * 70)
    print("WINNER")
    print("=" * 70)
    best_agent = max(agent_names, key=lambda name: results[name]["OVERALL"]["wr"])
    best_wr = results[best_agent]["OVERALL"]["wr"]
    print(f"✓ {best_agent}: {best_wr:.1%} win rate")


if __name__ == "__main__":
    main()
