"""Test V10 (Advanced Learning + 40 Buckets) vs V6 (Current Winner)"""

from monte_carlo_v6_dynamic import MonteCarloV6Dynamic
from monte_carlo_v10_advanced_learning import MonteCarloV10AdvancedLearning
from opponent_types import get_opponent_by_type
from pypokerengine.api.game import setup_config, start_poker


def test_agent(agent_class, agent_name, num_games=20):
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
            except Exception as e:
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
print("TEST: V6 vs V10 (Advanced Online Learning)")
print("=" * 70)
print("20 games vs each of 5 opponents = 100 games per agent\n")

v6_wr = test_agent(MonteCarloV6Dynamic, "V6 (Learned Thresholds)")
v10_wr = test_agent(MonteCarloV10AdvancedLearning, "V10 (40-Bucket + 40-Round Learning)")

print("\n" + "=" * 70)
print("FINAL COMPARISON")
print("=" * 70)
print(f"V6:  {v6_wr:.1%}")
print(f"V10: {v10_wr:.1%}")

if v10_wr > v6_wr:
    diff = (v10_wr - v6_wr) * 100
    print(f"\n🏆 V10 WINS by {diff:.1f}%!")
elif v6_wr > v10_wr:
    diff = (v6_wr - v10_wr) * 100
    print(f"\n🏆 V6 WINS by {diff:.1f}%!")
else:
    print(f"\n⚖️  TIED at {v6_wr:.1%}!")
