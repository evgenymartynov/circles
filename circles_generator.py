import copy

def generate(courses, times, clashes_allowed, aggregate=None):
    if clashes_allowed < 0:
        return aggregate

    if aggregate is None:
        aggregate = []

    # Short-circuit
    if len(aggregate) >= 100000:
        return aggregate

    if courses == []:
        aggregate.append(copy.deepcopy(times))
        return aggregate

    name, course = courses[0]
    for option in course:
        clash_amount = 0
        for slot in option:
            day, start, end = slot
            for i in xrange(start, end):
                if times[day][i]:
                    clash_amount += 1
        if clash_amount > clashes_allowed:
            continue

        # Try it
        oldvals = []
        for slot in option:
            day, start, end = slot
            for i in xrange(start, end):
                oldvals.append((day, i, times[day][i]))
                if times[day][i]:
                    times[day][i] = times[day][i] + ' | ' + name
                else:
                    times[day][i] = name

        generate(courses[1:], times, clashes_allowed - clash_amount, aggregate)

        for a, b, v in oldvals:
            times[a][b] = v
    return aggregate

def comparator_free(a):
    return sum([any(x) for x in a])

def comparator_unfree(a):
    return -comparator_free(a)

def comparator_hours_at_uni(a):
    hours = 0
    for day in xrange(5):
        first, last = None, None
        for hour in xrange(24):
            if a[day][hour]:
                if first is None:
                    first = hour
                last = hour
        if first:
            hours += last-first + 1

    return hours

def sort_timetables(tables, ordering):
    if not ordering:
        return tables

    comparators = {
        'free': comparator_free,
        'unfree': comparator_unfree,
        'hours': comparator_hours_at_uni,
    }

    assert ordering in comparators

    return sorted(tables, key=comparators[ordering])
