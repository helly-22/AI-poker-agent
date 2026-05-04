"""Compare V6 (Dynamic Trained) vs V7 (Advanced Heads-Up Strategy)"""

from monte_carlo_v6_dynamic import MonteCarloV6Dynamic
from monte_carlo_v7_advanced import MonteCarloV7Advanced
from opponent_types import get_opponent_by_type
from pypokerengine.api.game import setup_config, start_poker


def test_agent(agent_class, agent_name, num_games=20):
    """Test agent against all opponent types"""
    opponents = ["TightAggressive", "LoosePassive", "AggressiveBluffer", "Defensive", "Random", "OnlyRaise", "OnlyCall", "Limper"]

    print(f"\nTesting {agent_name}...")
    total_wins = 0
    total_losses = 0

    for opp_type in opponents:
        agent = agent_class()
        opponent = get_opponent_by_type(opp_type)
        wins, losses = 0, 0

        for _ in range(num_games):
            try:
                config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=10)
                config.register_player(name="Agent", algorithm=agent)
                config.register_player(name="Opponent", algorithm=opponent)
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

    overall_wr = total_wins / (total_wins + total_losses)
    print(f"  {'=' * 40}")
    print(f"  TOTAL:             {total_wins}W-{total_losses}L ({overall_wr:.1%})")
    return overall_wr


print("\n" + "=" * 70)
print("HEADS-UP SHOWDOWN: V6 vs V7")
print("=" * 70)
print("V6: Dynamic Trained (loads JSON thresholds)")
print("V7: Advanced (considers pot odds, bet sizing, opponent tendencies, SPR, etc.)")
print("\n20 games vs each of 8 opponents = 160 games per agent\n")

v6_wr = test_agent(MonteCarloV6Dynamic, "V6 (Dynamic Trained)")
v7_wr = test_agent(MonteCarloV7Advanced, "V7 (Advanced Heads-Up)")

print("\n" + "=" * 70)
print("FINAL RESULT")
print("=" * 70)
print(f"V6: {v6_wr:.1%}")
print(f"V7: {v7_wr:.1%}")

if v7_wr > v6_wr:
    diff = (v7_wr - v6_wr) * 100
    print(f"\n🏆🏆🏆 V7 WINS by {diff:.1f}%! 🏆🏆🏆")
elif v6_wr > v7_wr:
    diff = (v6_wr - v7_wr) * 100
    print(f"\n🏆🏆🏆 V6 WINS by {diff:.1f}%! 🏆🏆🏆")
else:
    print(f"\n⚖️  TIED at {v6_wr:.1%}!")
