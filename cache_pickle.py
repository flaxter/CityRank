from items.models import *
from items.utils import *

def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)


def mem_mgt(s):
	try:
		table, rows, items, display, middle = fetch_data(s, True)
		del table
		del rows
		del items
		del display
		del middle
	except ZeroDivisionError: pass

start = 8
total = 0
sources = list(DataSource.objects.filter(datascheme__type='r', active=True).order_by('id'))
for i in range(start, len(sources)): #set in combinations(sources, 2):
	for s in combinations(sources, i):
		total += 1
		print total, "- fetching data for", [source.id for source in s]
		mem_mgt(s)
