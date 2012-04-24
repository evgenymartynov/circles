import re, urllib
import circles_generator

URL_BASE = r'http://www.timetable.unsw.edu.au/2012/%s.html'
OFFSET = 6
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
tags_re = re.compile(r'<[^>]*>')
dow_re = re.compile(r'\([^\(]*\)')

def print_timetable(times):
    days = len(times)
    slots = len(times[0])

    print '=' * 160

    print '     ',
    for d in xrange(5):
        print '%30s' % DAYS[d],
    print
    print '-' * 160

    first, last = None, None
    for t in xrange(slots):
        subjects = [times[x][t] for x in xrange(5)]
        if any(subjects):
            if first is None:
                first = t
            last = t
        else:
            continue

    for t in xrange(first, last+1):
        print '%2d:00 |' % t,
        for d in xrange(5):
            print '%30s' % str(times[d][t] or '-')[:30],
        print

def get_lines(subject):
    url = URL_BASE % subject
    return urllib.urlopen(url)

def print_classes(classes):
    for k, v in classes.iteritems():
        print '%s\n\t%s\n' % (k, '\n\t'.join(map(str, v)))

def dow_to_int(s):
    return DAYS.index(s)

def get_classes(subject):
    lines = map(lambda x: x.strip(), [line for line in get_lines(subject)])

    classes = {}

    i = 0
    while i < len(lines)-5:
        if '#S2-' in lines[i]:
            name = subject + ' ' + re.sub(tags_re, '', lines[i], 10)
            times = re.sub(tags_re, '', lines[i+OFFSET], 10)
            # Readability? Fuck that.
            times = [(dow_to_int(time[0]), int(time[1][:2]), int(time[3][:2])) for time in map(lambda x: x.split(), map(lambda x: x.strip(), re.sub(dow_re, '', times).split(', ')))]
            classes[name] = classes.get(name, []) + [times]
            i += OFFSET
        else:
            i += 1

    return classes

def process(subjects, SORTING_ORDER=None):
    all_classes = {}

    for c in subjects:
        classes = get_classes(c)
        if not classes:
            raise ValueError('Could not find subject `%s\'. Aborting.' % c)
        all_classes.update(classes)

    # print_classes(all_classes)

    stuff = all_classes.items()
    time_slots = [[False] * 24 for i in xrange(5)]
    tables = circles_generator.generate(stuff, time_slots)

    tables.sort()
    uniq = []
    for t in tables:
        if uniq == [] or uniq[-1] != t:
            uniq.append(t)
    tables = uniq

    tables = circles_generator.sort_timetables(tables, SORTING_ORDER)

    return tables
