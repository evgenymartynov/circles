DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

class CirclesError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class SubjectNotFound(CirclesError):
    def __init__(self, subject, semester='the current semester'):
      super(SubjectNotFound, self).__init__(
        'Cannot find subject %s in %s. '
        'Check that the course is offered in this period, '
        'and report missing subjects to Evgeny.' % (subject, semester)
      )
