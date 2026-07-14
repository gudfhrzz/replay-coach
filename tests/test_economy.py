from parser.cs2.economy import classify_buy


def test_pistol_round():
    assert classify_buy(1, 4_000, 3_000, 4_000).buy_type == "pistol"
    assert classify_buy(13, 4_000, 3_000, 4_000).buy_type == "pistol"


def test_full_eco():
    d = classify_buy(2, 1_000, 500, 10_000)
    assert d.buy_type == "full_eco"
    assert not d.is_forced


def test_full_buy():
    d = classify_buy(5, 25_000, 20_000, 30_000)
    assert d.buy_type == "full_buy"
    assert not d.is_forced


def test_force_buy_flag():
    # 풀바이 미달 장비인데 시작 자금의 80% 이상을 지출 → 포스
    d = classify_buy(3, 12_000, 11_000, 12_500)
    assert d.buy_type == "semi_buy"
    assert d.is_forced


def test_semi_eco_not_forced_when_saving():
    d = classify_buy(3, 6_000, 2_000, 20_000)
    assert d.buy_type == "semi_eco"
    assert not d.is_forced


def test_boundaries():
    assert classify_buy(2, 4_999, 0, 1).buy_type == "full_eco"
    assert classify_buy(2, 5_000, 0, 1).buy_type == "semi_eco"
    assert classify_buy(2, 10_000, 0, 1).buy_type == "semi_buy"
    assert classify_buy(2, 20_000, 0, 1).buy_type == "full_buy"


def test_zero_start_money_no_division_error():
    d = classify_buy(2, 0, 0, 0)
    assert d.buy_type == "full_eco"
    assert not d.is_forced
