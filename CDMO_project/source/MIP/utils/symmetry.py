def round_robin_weeks(n: int):
    if n % 2 != 0 or n < 4:
        raise ValueError("n must be even and >= 4")
    A = list(range(1, n + 1))
    weeks = []
    for i in range(n - 1):
        pairs = []
        for k in range(n // 2):
            i = A[k]
            j = A[-(k + 1)]
            if i < j:
                pairs.append((i, j))
            else:
                pairs.append((j, i))
        weeks.append(pairs)
        A = [A[0]] + [A[-1]] + A[1:-1]
    return weeks
