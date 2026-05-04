"""Quick test of Monte Carlo Player"""

from monte_carlo_player import MonteCarloPlayer
from opponent_types import RandomOpponent
from pypokerengine.api.game import setup_config, start_poker


def quick_test(num_games=3):
    """Play quick test games."""
    print("=" * 60)
    print("Monte Carlo Player - Quick Test")
    print("=" * 60)

    agent = MonteCarloPlayer()
    print(f"Agent initialized: {agent.__class__.__name__}")

    opponent = RandomOpponent()
    print(f"Testing against: {opponent.name}\n")

    total_wins = 0
    total_losses = 0

    for game_num in range(1, num_games + 1):
        print(f"Game {game_num}/{num_games}...")

        try:
            # Setup game config
            config = setup_config(
                max_round=10,
                initial_stack=10000,
                small_blind_amount=10
            )

            # Register players
            config.register_player(name="MonteCarlo", algorithm=agent)
            config.register_player(name="Random", algorithm=opponent)

            # Play game
            result = start_poker(config, verbose=0)

            # Check results
            players = result.get("players", [])
            if len(players) >= 2:
                mc_stack = players[0].get("stack", 0)
                random_stack = players[1].get("stack", 0)

                if mc_stack > random_stack:
                    print(f"  WIN: ${mc_stack} vs ${random_stack}")
                    total_wins += 1
                else:
                    print(f"  LOSS: ${mc_stack} vs ${random_stack}")
                    total_losses += 1
            else:
                print(f"  ERROR: Invalid result format")
                total_losses += 1

        except Exception as e:
            print(f"  ERROR: {str(e)[:60]}")
            total_losses += 1

    print("\n" + "=" * 60)
    total = total_wins + total_losses
    wr = total_wins / total if total > 0 else 0
    print(f"Results: {total_wins}W-{total_losses}L ({wr:.1%})")
    print("=" * 60)

    return total_wins