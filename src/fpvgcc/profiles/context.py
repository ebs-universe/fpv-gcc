

class ContextBase(object):

    def __init__(self):
        self._suppressed_names = []
        self._suppressed_regions = ['*default*']

    @property
    def suppressed_names(self):
        return self._suppressed_names

    def suppress_name(self, name):
        self._suppressed_names.append(name)

    def unsuppress_name(self, name):
        while name in self._suppressed_names:
            self._suppressed_names.remove(name)

    @property
    def suppressed_regions(self):
        return self._suppressed_regions
