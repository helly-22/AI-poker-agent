"""Compare V6 (Dynamic Trained) vs V8 (Enhanced with Pot Odds + SPR)"""

from monte_carlo_v6_dynamic import MonteCarloV6Dynamic
from monte_carlo_v8_enhanced import MonteCarloV8Enhanced
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
            except Exception:
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
print("V6 vs V8: Does adding Pot Odds + SPR help?")
print("=" * 70)
print("V6: Simple (loads trained thresholds only)")
print("V8: Enhanced (V6 + pot odds adjustment + SPR adjustment)")
print("\n20 games vs each of 8 opponents = 160 games per agent\n")

v6_wr = test_agent(MonteCarloV6Dynamic, "V6 (Simple)")
v8_wr = test_agent(MonteCarloV8Enhanced, "V8 (Enhanced: Pot Odds + SPR)")

print("\n" + "=" * 70)
print("FINAL RESULT")
print("=" * 70)
print(f"V6: {v6_wr:.1%}")
print(f"V8: {v8_wr:.1%}")

if v8_wr > v6_wr:
    diff = (v8_wr - v6_wr) * 100
    print(f"\n🏆🏆🏆 V8 WINS by {diff:.1f}%! 🏆🏆🏆")
    print("Pot odds + SPR enhancements help!")
elif v6_wr > v8_wr:
    diff = (v6_wr - v8_wr) * 100
    print(f"\n🏆🏆🏆 V6 WINS by {diff:.1f}%! 🏆🏆🏆")
    print("Simple is still better - enhancements don't help")
else:
    print(f"\n⚖️  TIED at {v6_wr:.1%}!")
