### Store various plotting parameters for histograms/bar plots (some arguments are image_K keywords, some are matplotlib) ###

### Barplot of imageJ brightness parameters ###
grey_hissy=dict(    
    outname='Brightness_distribution',  #Name of output file
    
    color='purple',
    alpha=0.4,
    width=0.3
    )

circ_hissy=dict(
    outname=' ',
    color='red',
    lengthrange=(0.1,0.95)
    )

### Default range units are of "length" as opposed to radii, diameter, area (implictly computed in imk_class)
size_hists=(
 #   dict(outname='short-range', color='yellow', lengthrange=(0,20), alpha=0.4 ),    
  #  dict(outname='large-range', color='black', lengthrange=(120,500), alpha=0.4 ),    
    dict(outname='full-range', color='blue', lengthrange=None, alpha=0.4 ),    
    dict(outname='mid-range', color='red', lengthrange=(10,120), alpha=0.4 ),
    
           )