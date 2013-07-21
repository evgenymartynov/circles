import re, os
from datetime import datetime, timedelta
import circles_generator

from tempfile import mkstemp
from subprocess import Popen as popen, PIPE
import json

from hard_drugs import fetch_classes as beautifulsoup_fetch_classes
from common import *

html_page_cache = {}
def get_classes(subject):
    def fetch_classes():
      return beautifulsoup_fetch_classes(subject)

    def expired():
        if subject not in html_page_cache:
            return True

        timediff = datetime.now() - html_page_cache[subject][0]
        return timediff > timedelta(hours=1)

    def update():
        html_page_cache[subject] = (datetime.now(), fetch_classes())

    def get():
        return html_page_cache[subject][1]

    if expired():
        print '  ', subject, 'expired, fetching...'
        update()

    results = get()
    if not results:
        raise SubjectNotFound(subject)
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

def process(subjects, SORTING_ORDER=None, CLASHES=0):
    all_classes = {}

    for c in subjects:
        classes = get_classes(c)
        all_classes.update(classes)

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
