#!/usr/bin/env python
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

mu, sigma = 100, 15
x = mu + sigma*np.random.randn(1000)  #generate random data 

# the histogram of the data
counts, bins, patches = plt.hist(x, 50, normed=False, facecolor='green', alpha=0.75)
bcenters=(bins[:-1] + bins[1:])/2.0  

# add a 'best fit' line

### I need to pass my symmetric bins, 
y = mlab.normpdf( bcenters, mu, sigma)  #NormalDistribution evaluated at each x-value given mu, sigma
y=y * (counts/y)
l = plt.plot(bcenters, y, 'r--', linewidth=1)

plt.xlabel('Smarts')
plt.ylabel('Probability')
plt.title(r'$\mathrm{Histogram\ of\ IQ:}\ \mu=100,\ \sigma=15$')
plt.grid(True)

plt.show()