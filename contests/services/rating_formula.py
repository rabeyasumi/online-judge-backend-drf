"""Global rating formula (pure Python, no Django imports).

First rated contest : new = contest_rating
Later contests      : new = old + 0.3 * (contest_rating - old)
"""

SMOOTHING = 0.3


def calculate_new_rating(old_rating, contest_rating, rated_contests):
    old_rating = float(old_rating)
    contest_rating = float(contest_rating)

    if rated_contests == 0:
        new_rating = contest_rating
    else:
        new_rating = old_rating + SMOOTHING * (contest_rating - old_rating)

    return round(new_rating, 2)
