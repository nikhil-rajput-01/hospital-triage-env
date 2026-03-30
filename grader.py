def grade(env):
    if env.total_generated == 0:
        return 0

    survival = (env.total_generated - env.total_died) / env.total_generated
    treatment = env.total_treated / env.total_generated

    avg_wait = env.total_wait_time / max(env.total_generated, 1)
    wait_score = max(0, 1 - avg_wait / 50)

    point_score = max(0, min(1, (env.point + 500) / 1000))

    final = (
        0.4 * survival +
        0.3 * treatment +
        0.2 * wait_score +
        0.1 * point_score
    )

    return round(final, 4)

def grade_easy(env):
    score = grade(env)
    return max(0.0, min(1.0, score))

def grade_medium(env):
    score = grade(env) * 0.9
    return max(0.0, min(1.0, score))

def grade_hard(env):
    score = grade(env) * 0.8
    return max(0.0, min(1.0, score))