import numpy as np
import matplotlib.pyplot as plt
from matplotlib import figure

## Quick curve fitting of BSA paper from nist
x=[10.0 , 30.0 , 60.0]  #Particle diams 10,30,60nm
y=[0.023, 0.017, 0.014]  #BSA per square nm assuming spheres, converted x--> area
cov=[60.0, 44.0, 36.0] #Coverage percentage corresponding to bsa/per square nm (y)

def bsa_count(diams, style='single'):
    ''' Returns bsa molecules per unit surface area given a diameter of a particle,
    and a fitting style.  Essentially just returns the y value of a fit curve
    given x (diamter).'''

    if style=='single':
        z=np.polyfit(x, y, 1)  
        p=np.poly1d(z)        
        return p(diams)
        
                
    elif style=='dual':
        dout=[]

        x1=x[0:2] #Make x[0:2]
        y1=y[0:2]# ditto
        z1=np.polyfit(x1, y1, 1)  
        p1=np.poly1d(z1)         
            
        x2=x[1:3]   #Make x[1:3]
        y2=y[1:3] # ditto
        z2=np.polyfit(x2, y2, 1)  
        p2=np.poly1d(z2)         
                
        for d in diams:
            if d < x[1]:  #If d < 30
                dout.append(p1(d))
            else:
                dout.append(p2(d))
        return dout
         
    else:
        raise AttributeError('syle must be "single" or "dual", not %s'%style)


def _map_cov(bsa_area):
    ''' Given bsa surface area, map this to percent coverage using the fact that 0.0386nm-2 is 100% coverage'''
    return 100.0* ( bsa_area / 0.0386)

if __name__=='__main__':
    vals=np.linspace(min(x)-5, max(x)+5, 10)  
    
    fig=plt.figure()
    ax1=fig.add_subplot(111)
    line1=ax1.plot(x,y, 'o-')
    line2=ax1.plot(vals, bsa_count(vals, style='single'), color='black', ls='--')
    line3=ax1.plot(vals, bsa_count(vals, style='dual'), color='red', ls='--')   
    ax1.yaxis.tick_right()  #Does something to prevent tick mark overlapping
    ax1.yaxis.set_label_position("right")
    plt.ylabel('BSA per unit surface area (nm-2)')
    plt.xlabel('Diameter (nm)')
    plt.title('BSA density vs. NP diameter')   

    ax2 = fig.add_subplot(111, sharex=ax1, frameon=False)
    ax2.yaxis.tick_left()
    ax2.yaxis.set_label_position("left")
    plt.ylabel("Shell Coverage (%)")    
    

    ### Bit odd, but add padding to y axis values, then when I scale the coverage, it scales correctly.  Only issue is that axis tick marks don't completly line up!  
    ### THus, it may be a bit tricky to get right values on y-axis by eye
    padding=0.002
    ymax, ymin=y[-1]-padding , y[0]+padding
    ax1.set_ylim(ymax, ymin)
    ax2.set_ylim(_map_cov(ymax), _map_cov(ymin))

    ax1.legend(('NIST BSA Data', 'Single fit', 'Dual point fit'))
        
    plt.show()
