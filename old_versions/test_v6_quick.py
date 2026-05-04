"""Quick test comparing BASELINE vs V6 (Dynamic Trained)"""

from monte_carlo_player import MonteCarloPlayer
from monte_carlo_v6_dynamic import MonteCarloV6Dynamic
from opponent_types import get_opponent_by_type
from pypokerengine.api.game import setup_config, start_poker


def test_agent(agent_class, agent_name, num_games=10):
    """Test agent against 5 opponents"""
    opponents = ["TightAggressive", "LoosePassive", "Defensive", "Random", "AggressiveBluffer"]

    print(f"\n{'=' * 70}")
    print(f"TESTING: {agent_name}")
    print(f"{'=' * 70}")

    total_wins = 0
    total_losses = 0

    for opp_type in opponents:
        agent = agent_class()
        opponent = get_opponent_by_type(opp_type)

        wins = 0
        losses = 0

        for _ in range(num_games):
            try:
                config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=10)
                config.register_player(name="Agent", algorithm=agent)
                config.register_player(name="Opp", algorithm=opponent)

                result = start_poker(config, verbose=0)
                if result["players"][0]["stack"] > result["players"][1]["stack"]:
                    wins += 1
                else:
                    losses += 1
            except:
                losses += 1

        total_wins += wins
        total_losses += losses
        wr = wins / (wins + losses) if (wins + losses) > 0 else 0
        print(f"  {opp_type:20} {wins}W-{losses}L ({wr:.1%})")

    overall_wr = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0
    print(f"  {'-' * 40}")
    print(f"  OVERALL:           {total_wins}W-{total_losses}L ({overall_wr:.1%})")

    return overall_wr


print("\n" + "=" * 70)
print("QUICK TEST: BASELINE vs V6 (Dynamic Trained)")
print("=" * 70)
print("10 games vs each of 5 opponents = 50 games per agent\n")

baseline_wr = test_agent(MonteCarloPlayer, "BASELINE (Hard-Coded)")
v6_wr = test_agent(MonteCarloV6Dynamic, "V6 (Dynamically Trained from JSON)")

print("\n" + "=" * 70)
print("FINAL COMPARISON")
print("=" * 70)
print(f"BASELINE:  {baseline_wr:.1%}")
print(f"V6:        {v6_wr:.1%}")

if v6_wr > baseline_wr:
    diff = (v6_wr - baseline_wr) * 100
    print(f"\n🏆 V6 WINS by {diff:.1f}%!")
elif baseline_wr > v6_wr:
    diff = (baseline_wr - v6_wr) * 100
    print(f"\n🏆 BASELINE WINS by {diff:.1f}%!")
else:
    print(f"\n⚖️  TIED at {baseline_wr:.1%}!")
