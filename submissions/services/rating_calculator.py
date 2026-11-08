def calculate_problem_rating(
    problem_rating,
    wrong_submission_count,
    elapsed_time
):
    time_penalty = problem_rating * 0.004 * elapsed_time

    wrong_penalty = 50 * wrong_submission_count

    calculated_rating = (
        problem_rating - time_penalty - wrong_penalty
    )

    minimum_rating = 0.4 * problem_rating

    final_points = max(minimum_rating, calculated_rating)

    return final_points



# \[
# t=\frac{elapsed\_time}{contest\_duration}
# \]

# \[
# rating\_a\_ref=problem\_rating\times 0.2^t
# \]

# \[
# rating_a=rating\_a\_ref-(50\times wrong\_submission\_count)
# \]