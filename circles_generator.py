import copy

def generate(courses, times, aggregate=None):
    if aggregate is None:
        aggregate = []

    if courses == []:
        aggregate.append(copy.deepcopy(times))
        return aggregate

    name, course = courses[0]
    for option in course:
        valid = True
        for slot in option:
            day, start, end = slot
            for i in xrange(start, end):
                if times[day][i]:
                    valid = False
                    break
        if not valid:
            continue

        # Try it
        for slot in option:
            day, start, end = slot
            for i in xrange(start, end):
                times[day][i] = name

        generate(courses[1:], times, aggregate)

        for slot in option:
            day, start, end = slot
            for i in xrange(start, end):
                times[day][i] = False
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
