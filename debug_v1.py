"""Debug V1 to see what's going wrong"""

from monte_carlo_v1_hand_abstraction import MonteCarloV1HandAbstraction

agent = MonteCarloV1HandAbstraction()

# Test hand classifications
test_hands = [
    (['AC', 'KD'], "should be PREMIUM"),
    (['AH', 'AS'], "should be PREMIUM"),
    (['AD', 'KH'], "should be PREMIUM"),
    (['JC', 'JS'], "should be STRONG"),
    (['AQ', 'AQ'], "should be STRONG"),
    (['8C', '8D'], "should be MEDIUM"),
    (['2H', '3D'], "should be WEAK"),
]

print("Hand Classification Test:")
print("=" * 60)

for hand, expected in test_hands:
    bucket = agent._classify_hand(hand)
    print(f"{hand}: {bucket:10} ({expected})")

print("\n" + "=" * 60)
print("Board Evaluation Test:")
print("=" * 60)

test_boards = [
    ([], "Preflop (no board)"),
    (['AH', 'KD', 'QC'], "AKQ - Wet board"),
    (['2H', '3D', '4C'], "2-3-4 - Dry board"),
    (['AH', 'KC', 'QD', 'JH'], "Broadway turn"),
]

for board, desc in test_boards:
    strength = agent._evaluate_board(board)
    print(f"{str(board):30} {desc:25} Strength: {strength:.2f}")

print("\n" + "=" * 60)
print("MC Simulation Test:")
print("=" * 60)

buckets = ["PREMIUM", "STRONG", "MEDIUM", "WEAK"]
board_stages = [0, 3, 4, 5]  # preflop, flop, turn, river

for bucket in buckets:
    print(f"\n{bucket}:")
    for stage in board_stages:
        stage_name = {0: "Preflop", 3: "Flop", 4: "Turn", 5: "River"}[stage]
        strength = agent._run_mc_simulations(bucket, stage)
        print(f"  {stage_name:10}: {strength:.2f}")
