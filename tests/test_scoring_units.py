import pytest

from contests.services.rating_formula import calculate_new_rating
from submissions.services.rating_calculator import calculate_problem_rating


@pytest.mark.parametrize(
    'rating, wrong, minutes, expected',
    [
        (1000, 0, 0, 1000),        # instant solve keeps full points
        (1000, 0, 10, 960),        # 0.4% of the rating lost per minute
        (1000, 2, 10, 860),        # plus 50 points per wrong attempt
        (1500, 1, 30, 1270),       # 1500 - 180 - 50
        (1000, 0, 200, 400),       # floor: never below 40% of the rating
        (1000, 20, 0, 400),        # floor also applies to many wrong attempts
        (800, 0, 10_000, 320),     # floor for a very late solve
    ],
)
def test_problem_points(rating, wrong, minutes, expected):
    assert calculate_problem_rating(rating, wrong, minutes) == pytest.approx(expected)


def test_first_rated_contest_uses_the_contest_score():
    assert calculate_new_rating(0, 800, rated_contests=0) == 800


def test_later_contests_blend_with_factor_0_3():
    # 1000 + 0.3 * (500 - 1000) = 850
    assert calculate_new_rating(1000, 500, rated_contests=1) == 850


def test_new_rating_is_rounded_to_two_decimals():
    # 100.33 + 0.3 * (200.77 - 100.33) = 130.462
    assert calculate_new_rating(100.33, 200.77, rated_contests=2) == 130.46
