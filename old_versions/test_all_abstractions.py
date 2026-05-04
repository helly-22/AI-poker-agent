"""
Comprehensive test comparing all Monte Carlo abstraction versions
"""

from monte_carlo_player import MonteCarloPlayer
from monte_carlo_v2_board_texture import MonteCarloV2BoardTexture
from monte_carlo_v3_street_aware import MonteCarloV3StreetAware
from monte_carlo_v4_spr import MonteCarloV4SPR
from monte_carlo_v5_hybrid import MonteCarloV5Hybrid
from monte_carlo_v6_dynamic import MonteCarloV6Dynamic
from opponent_types import get_opponent_by_type
from pypokerengine.api.game import setup_config, start_poker


def test_agent_vs_opponent(agent_class, agent_name, opponent_type, num_games=20):
    """Test an agent against a specific opponent"""
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
            losses += 1

    win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
    return wins, losses, win_rate


def main():
    """Test all 5 versions comprehensively"""

    agents = [
        (MonteCarloPlayer, "BASELINE (Current)"),
        (MonteCarloV6Dynamic, "V6 (Dynamic Trained)"),
        (MonteCarloV2BoardTexture, "V2 (Board Texture)"),
        (MonteCarloV3StreetAware, "V3 (Street-Aware)"),
        (MonteCarloV4SPR, "V4 (SPR-Based)"),
        (MonteCarloV5Hybrid, "V5 (Hybrid)"),
    ]

    opponents = [
        "TightAggressive",
        "LoosePassive",
        "AggressiveBluffer",
        "Defensive",
        "Random",
    ]

    print("\n" + "=" * 80)
    print("MONTE CARLO ABSTRACTION COMPARISON - ALL VERSIONS (Including V6 Dynamic)")
    print("=" * 80)
    print(f"Testing {len(agents)} agent versions")
    print(f"Against {len(opponents)} opponent types")
    print(f"20 games per matchup = 100 games per agent\n")

    results = {}

    for agent_class, agent_name in agents:
        print(f"\n{'=' * 80}")
        print(f"TESTING: {agent_name}")
        print(f"{'=' * 80}")

        agent_results = {}
        total_wins = 0
        total_losses = 0

        for opponent_type in opponents:
            wins, losses, wr = test_agent_vs_opponent(agent_class, agent_name, opponent_type, 20)
            agent_results[opponent_type] = {"wins": wins, "losses": losses, "wr": wr}
            total_wins += wins
            total_losses += losses

            wr_pct = f"{wr:.1%}"
            record = f"{wins}W-{losses}L"
            print(f"  {opponent_type:20} {record:10} {wr_pct:>6}")

        overall_wr = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0
        agent_results["OVERALL"] = {"wins": total_wins, "losses": total_losses, "wr": overall_wr}
        results[agent_name] = agent_results

        print(f"  {'-' * 40}")
        print(f"  OVERALL:           {total_wins}W-{total_losses}L {overall_wr:.1%}")

    # Detailed comparison table
    print("\n" + "=" * 80)
    print("DETAILED COMPARISON TABLE")
    print("=" * 80)

    agent_names = [name for _, name in agents]

    for opponent_type in opponents + ["OVERALL"]:
        print(f"\n{opponent_type:20}:", end="")
        for agent_name in agent_names:
            wr = results[agent_name][opponent_type]["wr"]
            print(f"  {wr:>6.1%}", end="")
        print()

    # Summary and winner
    print("\n" + "=" * 80)
    print("RANKING (By Overall Win Rate)")
    print("=" * 80)

    ranked = sorted(
        agent_names,
        key=lambda name: results[name]["OVERALL"]["wr"],
        reverse=True
    )

    for i, agent_name in enumerate(ranked, 1):
        wr = results[agent_name]["OVERALL"]["wr"]
        wins = results[agent_name]["OVERALL"]["wins"]
        losses = results[agent_name]["OVERALL"]["losses"]
        print(f"{i}. {agent_name:30} {wins}W-{losses}L ({wr:.1%})")

    print("\n" + "=" * 80)
    best_agent = ranked[0]
    best_wr = results[best_agent]["OVERALL"]["wr"]
    print(f"✓ WINNER: {best_agent} with {best_wr:.1%} win rate")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
