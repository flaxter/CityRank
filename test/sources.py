from cities.models import *
from cities.utils import *

d = DataSource.objects.all()
sources =  [d[0],d[1],d[2]]
data = fetch_data(sources, False)
 
def rescale(data):
	lengths = [len(row) for row in data]
	middle = min(lengths) / 2

        for alpha in range(0,len(data)):
                # find m and b for f(x) = mx + b
                # for points (data[alpha][0], 100) and (data[alpha][0], 50)

                r0 = data[alpha][0].value
                r1 = data[alpha][middle].value
                m = 50 / (r0 - r1)
                b = 100 - m * r0 

                for j in range(lengths[alpha]):
                        data[alpha][j].value = m * data[alpha][j].value + b
        return data

