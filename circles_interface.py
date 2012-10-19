import re, urllib, os
from datetime import datetime, timedelta
import circles_generator

from tempfile import mkstemp
from subprocess import Popen as popen, PIPE
import json

URL_BASE = r'http://www.timetable.unsw.edu.au/2013/%s.html'
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

html_page_cache = {}
def get_classes(subject):
    def fetch_html():
        url = URL_BASE % subject
        return urllib.urlopen(url)

    def fetch_classes():
        lines = map(lambda x: x.strip(), [line for line in fetch_html()])
        classes = {}

        i = 0
        while i < len(lines)-5:
            if '#S1-' in lines[i]:
                name = subject + ' ' + re.sub(tags_re, '', lines[i], 10)

                times_line    = ''
                abort_counter = 0
                while '</td>' not in times_line:
                    # TODO: make this less idiotic
                    if abort_counter > 15:
                        raise ValueError('Detected runaway parser while processing subject %s. Contact Evgeny to fix.' % subject)
                    times_line += lines[i+OFFSET+abort_counter] + '\n'
                    abort_counter += 1

                times = re.sub(tags_re, '', times_line, 10)
                # Readability? Fuck that.
                times = [(dow_to_int(time[0]), int(time[1][:2]), int(time[3][:2])) for time in filter(bool, map(str.split, map(str.strip, re.sub(dow_re, '', times).split(', '))))]
                times = list(set(times))
                if times:
                    classes[name] = classes.get(name, []) + [times]
                i += OFFSET
            else:
                i += 1

        return classes

    def expired():
        if subject not in html_page_cache:
            return True

        timediff = datetime.now() - html_page_cache[subject][0]
        return timediff > timedelta(hours=1)

    def update():
        html_page_cache[subject] = (datetime.now(), fetch_classes())

    def get():
        return html_page_cache[subject][1]

    if (expired()):
        print '  ', subject, 'expired, fetching...'
        update()

    results = get()
    if not results:
        raise ValueError('Could not find subject `%s\' or it has no times listed. Try removing it or check the spelling.' % c)
    return results

def process_v2(subjects, SORTING_ORDER=None, CLASHES=0, NUM_RESULTS=0):
    def make_subject_file():
        data = map(get_classes, subjects)

        fd, fname = mkstemp(suffix='.crcl')
        def pr(*args):
            os.write(fd, ' '.join(map(unicode, args)) + '\n')

        pr(len(subjects), 13)

        for di in xrange(len(data)):
            pr('%s' % subjects[di])
            d = data[di]

            classes = []

            for k,v in d.iteritems():
                nm = k.split(' ', 1)[1]
                for t in v:
                    classes.append((nm, t))

            pr('  %d' % len(classes))
            for c in classes:
                pr('    %s' % c[0])
                pr('      %d' % len(c[1]))
                for t in c[1]:
                    dow = DAYS[t[0]]
                    pr('        %s %d-%d' % (dow, t[1], t[2]))

        os.close(fd)
        return fname

    fname = make_subject_file()
    args = ['circles-generator', fname, SORTING_ORDER, str(NUM_RESULTS), str(CLASHES)]
    stream = popen(args, stdout=PIPE)

    num_tables = int(stream.stdout.readline())
    data = stream.stdout.readline()

    os.unlink(fname)

    return num_tables, json.loads(data)

def print_classes(classes):
    for k, v in classes.iteritems():
        print '%s\n\t%s\n' % (k, '\n\t'.join(map(str, v)))

def dow_to_int(s):
    return DAYS.index(s)

def process(subjects, SORTING_ORDER=None, CLASHES=0):
    all_classes = {}

    for c in subjects:
        classes = get_classes(c)
        all_classes.update(classes)

    # print_classes(all_classes)

    stuff = all_classes.items()
    time_slots = [[False] * 24 for i in xrange(5)]
    tables = circles_generator.generate(stuff, time_slots, CLASHES)

    tables.sort()
    uniq = []
    for t in tables:
        if uniq == [] or uniq[-1] != t:
            uniq.append(t)
    tables = uniq

    tables = circles_generator.sort_timetables(tables, SORTING_ORDER)

    return tables
