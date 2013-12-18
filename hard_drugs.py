import re
import requests
from bs4 import BeautifulSoup
from common import *

SEMESTER = 'SEMESTER TWO'
URL = 'http://www.timetable.unsw.edu.au/2013/%s.html'
dow_to_int = lambda day: DAYS.index(day)

def vomit(data, depth=0):
  if type(data) is list:
    print ('  ' * depth) + '['
    for item in data:
      vomit(item, depth+1)
    print ('  ' * depth) + ']'
  elif type(data) is dict:
    print ('  ' * depth) + '{'
    for key, item in data.iteritems():
      print ('  ' * (depth+1)) + str(key) + ':'
      vomit(item, depth+2)
    print ('  ' * depth) + '}'
  else:
    print ('  ' * depth) + str(data)

def transform(bundle):
  """
    Receives a dict of text as extracted from timetable.unsw.
    Looks like...

    {
      u'Status': u'Open',
      u'Day/Start Time': u'Wed 17:00 - 18:00 (Weeks:2-9,10-13), ...',
      u'Section': u'W17A',
      u'Period': u'T2',
      u'Enrols/Capacity': u'7/8*',
      u'Activity': u'Tutorial-Laboratory',
      u'Class': u'10292',
    }

    Produces a smaller dict with sane keys and nicer class times.

    {
      'name': 'Tutorial-Laboratory',
      'time': [ (2, 17, 18), ... ],
    }
  """

  activity = bundle[u'Activity']

  date = bundle[u'Day/Start Time']
  matches = re.findall(r'(\w{3}) (\d{2}):\d{2} - (\d{2}):\d{2}\s*\(Weeks:([^)]+)\)', date)

  # At this point, matches is of form
  # [(u'Wed', u'15', u'16', u'2-9,10-13'), (u'Wed', u'16', u'18', u'2-9,10-13')]
  #
  # We do two things:
  # .. drop the weeks (last match group)
  # .. convert remaining items to integers, with DOW zero-based.

  def convert(item):
    assert len(item) == 4
    return (dow_to_int(item[0]), int(item[1]), int(item[2]))
  matches = map(convert, matches)

  return {
    'name': activity,
    'time': matches,
  }

def pack(classes):
  """
    Gets a list of lists of text-data from timetable.unsw, and packs it into a
    dictionary with their keys.

    The first list is used as keys. Remainder are the data, in same order.

    For example, input looks like...

    [
      [ u'Activity', u'Period', u'Class', u'Section', u'Status',
        u'Enrols/Capacity', u'Day/Start Time'
      ],
      [ u'Lecture', u'T2', u'2345', u'1UGA', u'Open', u'257/263*',
        u'Mon 16:00 - 18:00 (Weeks:1-9,11-13), Tue 13:00 - 14:00 (Weeks:1-9,10-12)'
      ],
      ...
    ]
  """

  assert len(classes) >= 2

  keys = classes[0]
  classes = classes[1:]
  packed = []
  for c in classes:
    packed.append(dict(zip(keys, c)))
  return packed

def sieve(flour):
  """
    Filters out short entries, i.e. lists with no more than 3 items.

    Makes sense because timetable.unsw data has 7 columns.
  """

  assert type(flour) is list and type(flour[0]) is list

  flour = filter(lambda f: len(f) > 3, flour)

  # Sanity check...
  assert all(map(lambda f: len(f) == 7, flour))

  return flour

def chop(carrots):
  """
    Processes the HTML table with class times/data, pulling out text contents
    of table>tr>td elements.

    There are probably cleaner/faster ways but I'm not too fussed.
  """

  carrots = carrots.find_all('tr', recursive=False)
  carrots = map(lambda carrot: carrot.find_all('td', recursive=False), carrots)

  for c in carrots:
    for k, cc in enumerate(c):
      c[k] = cc.text
  return carrots

def cook(URL):
  data = unicode(requests.get(URL).text)
  soup = BeautifulSoup(data, 'html.parser') # lxml parser has a bug
  potatoes = soup.find_all('td', attrs={'class': 'formBody'})

  for potato in potatoes:
    spuds = potato.find_all('table', recursive=False)

    for i, s in enumerate(spuds):
      if 'Go to Class Detail records' not in unicode(s):
        continue

      # Only care about a particular semester...
      if SEMESTER not in unicode(s):
        continue

      carrots = s.find_all('table')
      if len(carrots):
        carrots = chop(carrots[2])
        carrots = sieve(carrots)
        carrots = pack(carrots)
        carrots = map(transform, carrots)
        return carrots

def fetch_classes(subject):
  """
    Circles-compatible class fetcher.

    Takes in a subject code, in upper case, etc.
    Returns a dict with keys of class types, and values of lists of times.

    Example:

    {
      u'COMP2041 Lecture': [
        [(0, 16, 18), (1, 13, 14)],
      ],
      u'COMP2041 Tutorial-Laboratory': [
        [(4, 14, 15), (4, 15, 17)],
        [(4, 14, 15), (4, 15, 17)],
      ],
    }
  """

  data = cook(URL % subject)

  if data is None:
    raise SubjectNotFound(subject, SEMESTER.lower())

  # Data as returned by cook() has the choices spread out.
  # Combine them into lists to get the desired output format.
  classes = {}
  hatelife = {}
  for d in data:
    name = subject + ' ' + d['name']
    time = d['time']

    # YES I KNOW THIS SUCKS GET OFF MY BACK
    if str(time) in hatelife.get(name, set()):
      continue
    hatelife[name] = hatelife.get(name, set())
    hatelife[name].add(str(time))

    classes[name] = classes.get(name, []) + [time]

  return classes

if __name__ == '__main__':
  vomit(fetch_classes('COMP2041'))
