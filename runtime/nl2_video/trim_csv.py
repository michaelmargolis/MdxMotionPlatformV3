import numpy as np

t = np.loadtxt("mdx_coaster.csv", delimiter = ',')
print t
np.savetxt("mdx_coaster_trim.csv", t, delimiter=',', fmt='%0.3f')