''' Dictionaries of image parameters in the strict format:
    Filename: (image threshold), (image crop), (Estimated NP diameter)
    
    Examples:
       Fiber1:(140,255),(1200,3000,400,4000),(30)
       Fiber2: (122,255), (None),(None)
       
    Store builtin sizes here.
   
   '''


old_30=30.0 #nm
old_16=16.0 #nm

pella_50=48.6 #nm

new_22=22.0 #nm
new_18=18.0 #nm


sept_5_adj={
######F1
#'f1_5000.tif':( (163, 255),(1533, 9, 1422, 1104),(old_30)),   #No aggregates in crop
'f1_5000.tif':( (163, 255),(1242, 9, 1713, 1053),(old_30)),   #Huge aggregate in crop
'f1_10000.tif':( (166, 255),(None),(old_30)),
'f1_15000.tif':( (172, 255),(None),(old_30)),
#'f1_30000.tif': ( (158, 255), (None),(old_30)),
'f1_30000_low.tif': ( (155, 255), (None),(old_30)),
'f1_30000_high.tif': ( (183, 255), (None),(old_30)),



#######F2
'f2_5000.tif':( (152, 255), (951, 36, 1581, 2145),(old_30)),   
'f2_10000.tif':( (157, 255), (None),(old_30)),   
#              'f2_14390.tif':( (164, 255), (None),(old_30)),  
'f2_14390.tif':( (157, 255), (None),(old_30)),   #Trying to be identical with figures above
#             'f2_30000.tif':( (144, 255), (None),(old_30)),   
'f2_30000_low.tif':( (145, 255), (None),(old_30)),   
'f2_30000_high.tif':( (164, 255), (None),(old_30)),  

### F2 LOW HIGH ESTIMATION (added 12/19/12)
'f2_5000_low.tif':( (148, 255), (951, 36, 1581, 2145),(old_30)),   
'f2_5000_high.tif':( (166, 255), (951, 36, 1581, 2145),(old_30)),   

'f2_10000_low.tif':( (153, 255), (None),(old_30)),   
'f2_10000_high.tif':( (174, 255), (None),(old_30)),   

'f2_14390_low.tif':( (144, 255), (None),(old_30)),   #Trying to be identical with figures above
'f2_14390_high.tif':( (174, 255), (None),(old_30)),   #Trying to be identical with figures above



#######F3
'f3_5000.tif':( (144,255), (None),(old_30)),
'f3_9490.tif':((148,255),(None),(old_30)),
'f3_10000.tif':( (174,255), (42,144,2997,2109),(old_30)),
'f3_15000.tif':( (125,255), (None),(old_30)),
'f3_30000.tif':( (128, 255), (None),(old_30)),   

#######F4 (very high saturation, individual particles tough to distinguish)
####### Therefore, to get accurate coverage, need a high threshold estimate, to get particle distribution, less threshold
'f4_5000.tif':((110,255),(597, 18, 2466, 2265),(old_30)), 
'f4_5000_low.tif':((108,255),(597, 18, 2466, 2265),(old_30)), 
'f4_5000_high.tif':((153,255),(597, 18, 2466, 2265),(old_30)), 


#'f4_10000_scan7_int11.tif':((129, 255),(0, 1059, 1680, 1242),(old_30)),
'f4_10000_scan7_int11.tif':((127, 255),(9, 9, 3057, 924),(old_30)),  #Additional crop

'f4_10000_scan7_int11_low.tif':((98, 255),(9, 9, 3057, 924),(old_30)),
'f4_10000_scan7_int11_high.tif':((110, 255),(9, 9, 3057, 924),(old_30)),


'f4_10000_scan9.tif':((126,255),(60, 870, 2997, 1413),(old_30)),

'f4_15000_scan91.tif':((129,255),(60, 465, 2976, 1976),(old_30)),
'f4_15000_scan91_low.tif':((100,255),(60, 465, 2976, 1976),(old_30)),
'f4_15000_scan91_high.tif':((149,255),(60, 465, 2976, 1976),(old_30)),




'f4_30000_scan7_int111_low.tif':((87,255),(15, 273, 3042, 1986),(old_30)),  #Low Thresh, individual particles more distinct!!!
'f4_30000_scan7_int111_high.tif':((128,255),(15, 273, 3042, 1986),(old_30)),  #High Thresh, individual coverage more accurate!!!
'f4_30000_scan7_int111_low_nocrop.tif':((88,255),(None),(old_30)),  #Low Thresh, individual particles more distinct!!!


'f4_50000_scan7_int111_high.tif':((143, 255),(6, 129, 3066, 2157),(old_30)),  #LOW Thresh, individual particles more distinct!!!
'f4_50000_scan7_int111_low.tif':((98, 255),(6, 129, 3066, 2157),(old_30)),   #HIGH thresh, coverage more accurate
}

aug_13_adj={
    'f1_b1_15k21_low.tif':((143, 255),(1, 0, 1023, 628),(old_30)),
    'f1_b1_15k21_high.tif':((147, 255),(1, 0, 1023, 628),(old_30)),

    'f1_b1_30k2kx1_low.tif':((150, 255),(2, 1, 1020, 625),(old_30)),
    'f1_b1_30k2kx1_high.tif':((157, 255),(2, 1, 1020, 625),(old_30)),
    'f1_b1_30k1kx1_low.tif':((133, 255),(3, 30, 1021, 630),(old_30)),
    'f1_b1_30k1kx1_high.tif':((122, 255),(3, 30, 1021, 630),(old_30)),

    'f1_b1_50kx31_low.tif':((120, 255),(0, 2, 625, 672),(old_30)),
    'f1_b1_50kx31_high.tif':((133, 255),(0, 2, 625, 672),(old_30)),

    'f1_b1_100k11_low.tif': ((138, 255),(1, 33, 1017, 549),(old_30)),
    'f1_b1_100k11_high.tif': ((144, 255),(1, 33, 1017, 549),(old_30)),

    'f2_b1_5K21_low.tif': ((95, 255),(2, 1, 727, 536),(old_30)),  #5k not 50k
    'f2_b1_5K21_high.tif': ((108, 255),(2, 1, 727, 536),(old_30)),

    'f2_b1_15k_highres_9scan_11int1_low.tif': ((96, 255),(2, 2, 1020, 631),(old_30)),
    'f2_b1_15k_highres_9scan_11int1_high.tif': ((103, 255),(2, 2, 1020, 631),(old_30)),

    'f2_b1_30k31_low.tif': ((112, 255),(2, 14, 1020, 619),(old_30)),
    'f2_b1_30k31_high.tif': ((120, 255),(2, 14, 1020, 619),(old_30)), 

    'f2_b1_50k21_low.tif': ((119, 255),(6, 9, 1007, 625),(old_30)),
    'f2_b1_50k21_high.tif': ((121, 255),(6, 9, 1007, 625),(old_30)),

'f2_b1_100k21_low.tif':((112, 255),(5, 18, 1012, 614),(old_30)),
'f2_b1_100k21_high.tif':((145, 255),(5, 18, 1012, 614),(old_30)),

'f1_b2_5k21_low.tif':((129, 255),(4, 3, 434, 556),(old_30)),
'f1_b2_5k21_high.tif':((133, 255),(4, 3, 434, 556),(old_30)),
'f1_b2_15k11_low.tif':((95, 255),(4, 24, 1012, 604),(old_30)),
'f1_b2_15k11_high.tif':((128, 255),(4, 24, 1012, 604),(old_30)),
'f1_b2_30k21_low.tif':((130, 255),(5, 25, 989, 600),(old_30)),
'f1_b2_30k21_high.tif':((140, 255),(5, 25, 989, 600),(old_30)),
'f1_b2_50k11_low.tif':((110, 255),(14, 25, 984, 604),(old_30)),
'f1_b2_50k11_high.tif':((130, 255),(14, 25, 984, 604),(old_30)),
'f1_b2_100k11_low.tif':((103, 255),(49, 64, 916, 568),(old_30)),
'f1_b2_100k11_high.tif':((128, 255),(49, 64, 916, 568),(old_30)),
'f1_b2_100k21_low.tif':((115, 255),(24, 152, 966, 314),(old_30)),  #Added by adam later, (alread added to spreadsheet)
'f1_b2_100k21_high.tif':((157, 255),(24, 152, 966, 314),(old_30)),

'f2_b2_5k21_low.tif':((107, 255),(637, 284, 371, 342),(old_30)),
'f2_b2_5k21_high.tif':((129, 255),(637, 284, 371, 342),(old_30)),
'f2_b2_15k31_low.tif':((107, 255),(20, 50, 788, 612),(old_30)),
'f2_b2_15k31_high.tif':((126, 255),(20, 50, 788, 612),(old_30)),
'f2_b2_30k31_low.tif':((92, 255),(6, 18, 1004, 606),(old_30)),
'f2_b2_30k31_high.tif':((149, 255),(6, 18, 1004, 606),(old_30)),
'f2_b2_50k31_low.tif':((100, 255),(13, 32, 967, 598),(old_30)),
'f2_b2_50k31_high.tif':((138, 255),(13, 32, 967, 598),(old_30),)
}


### Note: All of these are low res images and were performed by Annie.
aug_6_adj={
'8_b1_f2_100k2_low.tif':((138 ,255), (23, 13, 998, 585),(old_30)),	
'8_b1_f2_100k2_high.tif':((164 ,255), (23, 13, 998, 586),(old_30)),	
'8_b1_f2_80k2_low.tif':((116 ,255), (14, 80, 996, 516),(old_30)),	
'8_b1_f2_80k2_high.tif':((149 ,255), (14, 80, 996, 517),(old_30)),	
'8_b1_f2_50k3_low.tif':((131 ,255), (5, 15, 1013, 583),(old_30)),	
'8_b1_f2_50k3_high.tif':((142 ,255), (5, 15, 1013, 584),(old_30)),	
'8_b1_f2_30k2_low.tif':((139 ,255), (11, 13, 922, 566),(old_30)),	
'8_b1_f2_30k2_high.tif':((165 ,255), (11, 13, 922, 567),(old_30)),	

'8_b1_f4_50k5_low.tif':((144 ,255), (5, 6, 1002, 550),(old_30)),
'8_b1_f4_50k5_high.tif':((182 ,255), (5, 6, 1002, 551),(old_30)),
'8_b1_f4_30k3_low.tif':((137 ,255), (4, 4, 1014, 589),(old_30)),
'8_b1_f4_30k3_high.tif':((168 ,255), (4, 4, 1014, 590),(old_30)),

'8_b2_f2_100k2_low.tif':((157 ,255), (7, 211, 650, 455),(old_30)),	
'8_b2_f2_100k2_high.tif':((169 ,255), (7, 211, 650, 456),(old_30)),	
'8_b2_f2_80k_low.tif':((144 ,255), (20, 252, 650, 363),(old_30)),	
'8_b2_f2_80k_high.tif':((154 ,255), (20, 252, 650, 363),(old_30)),	
'8_b2_f2_50k2_low.tif':((159 ,255), (114, 6, 906, 588),(old_30)),	
'8_b2_f2_50k2_high.tif':((173 ,255), (114, 6, 906, 589),(old_30)),	

'8_b2_f3_100k2_low.tif':((112 ,255), (3, 11, 1017, 591),(old_30)),	
'8_b2_f3_100k2_high.tif':((122 ,255), (3, 11, 1017, 592),(old_30)),	
'8_b2_f3_50k3_low.tif':((144 ,255), (104, 2, 816, 598),(old_30)),	
'8_b2_f3_50k3_high.tif':((155 ,255), (104, 2, 816, 599),(old_30)),	
'8_b2_f3_30k_low.tif':((140 ,255), (275, 4, 746, 599),(old_30)),	
'8_b2_f3_30k_high.tif':((160 ,255), (275, 4, 746, 600),(old_30)),	
'8_b2_f3_30k3_low.tif':((147 ,255), (3, 4, 541, 661),(old_30)),	
'8_b2_f3_30k3_high.tif':((150 ,255), (3, 4, 541, 662),(old_30)),	

'8_b3_f3_50k3_low.tif':((122 ,255), (20, 205, 985, 379),(old_30)),	
'8_b3_f3_50k3_high.tif':((136 ,255), (20, 205, 985, 380),(old_30)),	
'8_b3_f3_30k_low.tif':((128 ,255), (186, 91, 578, 457),(old_30)),	
'8_b3_f3_30k_high.tif':((141 ,255), (186, 91, 578, 458),(old_30)),	

'8_b3_f4_100k3_low.tif':((136 ,255), (2, 11, 1016, 590),(old_30)),	
'8_b3_f4_100k3_high.tif':((155 ,255), (2, 11, 1016, 590),(old_30)),	
'8_b3_f4_50k2_low.tif':((155 ,255), (38, 39, 335, 630),(old_30)),	
'8_b3_f4_50k2_high.tif':((163 ,255), (38, 39, 335, 631),(old_30)),	
'8_b3_f4_30k3_low.tif':((157 ,255), (9, 138, 488, 533),(old_30)),	
'8_b3_f4_30k3_high.tif':((161 ,255), (9, 138, 488, 533),(old_30)),	

'8_b1_f3_100k_low.tif':((131 ,255), (2, 3, 1019, 597),(old_30)),	
'8_b1_f3_100k_high.tif':((141 ,255), (2, 3, 1019, 597),(old_30),)
}


#Careful, this has some odd/mixed up filenames.  Fix these on ones that you intend to use.
aug_22={
'50k_highres_scan6_int4_low.tif':((101,255),(3,3,3063,1971),(old_30)), #f1
'50k_highres_scan6_int4_high.tif':((120,255),(3,3,3063,1971),(old_30)), #f1
'30k_low.tif':((100,255),(3,60,3063,2142),(old_30)), #f2
'30k_high.tif':((110,255),(3,60,3063,2142),(old_30)), #f2
'50k_low_res_7_11_low.tif':((95,255),(0,0,1023,738),(old_30)), #f3
'50k_low_res_7_11_low.tif':((105,255),(0,0,1023,738),(old_30)), #f3
} 


### Performed by Annie
oct_23_adj={'fiber1_50000_low.tif':((97, 255),(None),(pella_50)),
'fiber1_50000_high.tif':((117, 255),(None),(pella_50)),
'fiber1_30000_low.tif':((103, 255),(None),(pella_50)),
'fiber1_30000_high.tif':((115, 255),(None),(pella_50)),
'fiber1_10000_low.tif':((88, 255),(None),(pella_50)),
'fiber1_10000_high.tif':((115, 255),(None),(pella_50)),

'fiber2_50000_low.tif':((93, 255),(141, 258, 2616, 1947),(pella_50)),
'fiber2_50000_high.tif':((128, 255),(141, 258, 2616, 1947),(pella_50)),
'fiber2_30000_low.tif':((114, 255),(6, 864, 3054, 1434),(pella_50)),
'fiber2_30000_high.tif':((136, 255),(6, 864, 3054, 1434),(pella_50)),
'fiber2_10000_low.tif':((120, 225),(1056, 3, 2010, 2295),(pella_50)),
'fiber2_10000_high.tif':((134, 225),(1056, 3, 2010, 2295),(pella_50)),

### Performed by Zhaowen
'fiber3_10000_scan6_line113.tif':((124, 255),(None),(pella_50)),  #No low and high
'fiber3_30000_scan6_line113_low.tif':((116, 255),(6, 999, 3048, 1302),(pella_50)),
'fiber3_30000_scan6_line113_high.tif':((135, 255),(6, 999, 3048, 1302),(pella_50)),
'fiber3_50000_low.tif':((136, 255),(None),(pella_50)),
'fiber3_50000_high.tif':((145, 255),(None),(pella_50)),
'fiber3_50000_2_low.tif':((125, 255),(None),(pella_50)),
'fiber3_50000_2_high.tif':((143, 255),(None),(pella_50)),
'fiber3_100000_low.tif':((119, 255),(9, 897, 3054, 1371),(pella_50)),
'fiber3_100000_high.tif':((143, 255),(9, 897, 3054, 1371),(pella_50)),

'fiber4_10000_low.tif':((105, 255),(21, 15, 3018, 1344),(pella_50)),
'fiber4_10000_high.tif':((120, 255),(21, 15, 3018, 1344),(pella_50)),
'fiber4_30000_low.tif':((100, 255),( 	21, 972, 3051, 1320),(pella_50)),
'fiber4_30000_high.tif':((122, 255),(21, 972, 3051, 1320),(pella_50)),
'fiber4_50000_low.tif':((100, 255),( 	15, 12, 3042, 1572),(pella_50)),
'fiber4_50000_high.tif':((115, 255),(15, 12, 3042, 1572),(pella_50)),
'fiber4_100000_2_low.tif':((102, 255),(9, 9, 2589, 2283),(pella_50)),
'fiber4_100000_2_high.tif':((112,  255),(9, 9, 2589, 2283),(pella_50),)
}


### If I get lazy and want to rename a file on the fly to mix between runs, I just put it here.
special_renames={'f3_100000_low.tif':((112 ,255), (3, 11, 1017, 591),()),	
'f3_100000_high.tif':((122 ,255), (3, 11, 1017, 592))}

### RENAME THESE WITH UNDERSCORE OR THEY WONT SORT CORRECTLY!!!
june_TEM={'5C-1-60k-16b.tif':( (0, 18247),(None),()), '5C-2-60k-16b.tif':( (),(None) )}

january_14={
'f1_10000_2_low.tif':((46,255),(6,6,3054,2052),(pella_50)),
'f1_10000_2_high.tif':((50,255),(6,6,3054,2052),(pella_50)),
'f1_30000_low.tif':((64,255),(12,12,3051,2049),(pella_50)),

'f2_10000_low.tif':((70,255),(9,12,3051,2046),(pella_50)),
'f2_10000_high.tif':((76,255),(9,12,3051,2046),(pella_50)),
'f2_30000_low.tif':((67,255),(6,9,2967,2046),(pella_50)),
'f2_30000_high.tif':((72,255),(6,9,2967,2046),(pella_50)),

###the 10k image is extremely dark; check how resulting estimate compares to other 10k images.
'f3_10000_low.tif':((29,255),(6,6,3054,2061),(pella_50)),
'f3_10000_high.tif':((32,255),(6,6,3054,2061),(pella_50)),
'f3_30000_3_low.tif':((39,255),(6,9,3057,2067),(pella_50)),
'f3_30000_3_high.tif':((41,255),(6,9,3057,2067),(pella_50)),

'f4_10000_low.tif':((41,255),(9,9,3051,2058),(pella_50)),
'f4_10000_high.tif':((45,255),(9,9,3051,2058),(pella_50)),
'f4_30000_2_low.tif':((38,255),(6,6,3057,2061),(pella_50)),
'f4_30000_2_high.tif':((44,255),(6,6,3057,2061),(pella_50)),
}

january_28={
'f1_1_28_30000_low.tif':((62,255),(1323,669,1743,1629),(new_18)), #bad image, huge crop
'f1_1_28_30000_high.tif':((76,255),(1323,669,1743,1629),(new_18)),
'f3_1_28_50000_low.tif':((98,255),(3,258,3063,1722),(new_18)),
'f3_1_28_50000_high.tif':((105,255),(3,258,3063,1722),(new_18)),
'f3_1_28_100000_low.tif':((98,255),(3,123,3060,1713),(new_18)),
'f3_1_28_100000_high.tif':((117,255),(3,123,3060,1713),(new_18)),
'f4_1_28_30000_low.tif':((50,255),(3,3,3063,1992),(new_18)),
'f4_1_28_30000_high.tif':((70,255),(3,3,3063,1992),(new_18)),
'f4_1_28_494804_low.tif':((73,255),(3,6,3063,1989),(new_18)),
'f4_1_28_494804_high.tif':((84,255),(3,6,3063,1989),(new_18)),
}

january_29={
'f1_1_29_10000_low.tif':((81,255),(3,6,3063,984),(new_22)),
'f1_1_29_10000_high.tif':((92,255),(3,6,3063,984),(new_22)),
'f1_1_29_30000_low.tif':((77,255),(39,6,3027,2067),(new_22)),
'f1_1_29_30000_high.tif':((87,255),(39,6,3027,2067),(new_22)),
'f1_1_29_50000_low.tif':((79,255),(9,9,3045,2028),(new_22)),
'f1_1_29_50000_high.tif':((84,255),(9,9,3045,2028),(new_22)),
'f3_1_29_10000_low.tif':((78,255),(3,3,3063,2073),(new_22)),
'f3_1_29_10000_high.tif':((82,255),(3,3,3063,2073),(new_22)),
'f3_1_29_30000_low.tif':((73,255),(3,3,3063,2046),(new_22)),
'f3_1_29_30000_high.tif':((80,255),(3,3,3063,2046),(new_22)),
'f3_1_29_100000_low.tif':((86,255),(0,27,3069,1968),(new_22)),
'f3_1_29_100000_high.tif':((108,255),(0,27,3069,1968),(new_22)),
'f4_1_29_10000_low.tif':((45,255),(3,3,3063,1989),(new_22)),
'f4_1_29_10000_high.tif':((54,255),(3,3,3063,1989),(new_22)),
'f4_1_29_30000_low.tif':((40,255),(9,9,3054,1983),(new_22)),
'f4_1_29_30000_high.tif':((45,255),(9,9,3054,1983),(new_22)),
}

february_8={
'f1_30000_low.tif':((44,255),(9,609,3057,1689),(new_22)),
'f1_30000_high.tif':((54,255),(9,609,3057,1689),(new_22)),

'f2_30000_low.tif':((49,255),(None),(new_22)),  #THIS ONE USES BOTH TYPES
'f2_30000_high.tif':((57,255),(None),(new_22)),

'f2_30000_2_low.tif':((59,255),(None),(new_22)),  #THIS ONE USES BOTH TYPES


'f3_37k_lineint_low.tif':((101,255),(1,213,1021,553),(new_22)),
'f3_37k_lineint_high.tif':((111,255),(1,213,1021,553),(new_22)),

'f4_50000_low.tif':((41,255),(3,120,3063,2178),(new_22)),
'f4_50000_high.tif':((44,255),(3,120,3063,2178),(new_22),)
}

february_25={
'f3_30000_low.tif':((74,255),(3,3,3063,2004),(new_22)),
'f3_30000_high.tif':((89,255),(3,6,3060,2001),(new_22)),
'f3_30000_2_low.tif':((90,255),(12,39,3054,1968),(new_22)),
'f3_30000_high.tif':((111,255),(12,39,3054,1968),(new_22)),
'f4_30000_2_low.tif':((59,255),(6,6,3063,2001),(new_22)), ##blurry image
'f4_30000_2_high.tif':((73,255),(6,6,3063,2001),(new_22)), ##blurry image
'f4_30000_3_low.tif':((68,255),(3,6,3063,2004),(new_22)),
'f4_30000_3_high.tif':((83,255),(6,6,3063,2004),(new_22)),
'f4_30000_4_low.tif':((67,255),(3,3,3063,2007),(new_22)),
'f4_30000_4_high.tif':((79,255),(3,3,3063,2007),(new_22)),
            }

february_26={
'f1_30000_2_low.tif':((120,255),(3,6,3060,2001),(new_22)),
'f1_30000_2_high.tif':((135,255),(3,6,3060,2001),(new_22),)
}

march_7={
'F1_30000_low.tif':((106,255),(20, 40, 3016, 1920),(new_22)),   #With large aggregate
'F1_30000_high.tif':((119,255),(48,44,1996,1856),(new_22)),   #Double check

#'F1_30000_low.tif':((),(48,44,1996,1856),(new_22)),   #Without large aggregate GOOD EXAMPLE
#'F1_30000_high.tif':((),(48,44,1996,1856),(new_22)),   #Without large aggregate GOOD EXAMPLE

'F1_100000_low.tif':((100,255),(36, 44, 2940, 1936),(new_22)),
'F1_100000_high.tif':((110,255),(36, 44, 2940, 1936),(new_22)),

'F2_30000_low.tif':((100,255),(264,56,1432,1848),(new_22)),
'F2_30000_high.tif':((122,255),(264,56,1432,1848),(new_22)),

'F2_30000_2_low.tif':((101,255),(52,52,2176,1904),(new_22)),
'F2_30000_2_high.tif':((125,255),(52,52,2176,1904),(new_22)),

'F2_30000_3_low.tif':((112,255),(32,32,2036,1932),(new_22)),
'F2_30000_3_high.tif':((118,255),(32,32,2036,1932),(new_22)),

'F2_72600_low.tif':((104,255),(48, 60, 3024, 1924),(new_22)),   #Doublechek none
'F2_72600_high.tif':((115,255),(48, 60, 3024, 1924),(new_22)),

}

#alldics=[sept_5_adj ,aug_13_adj , aug_6_adj ,oct_23_adj, special_renames, january_14 ]
alldics=[january_14]#, aug_22, oct_23_adj, march_7] #name conflicts
manual_adjustments={}
### Make sure dictionaries don't have dupliate keys before merger ###
allkeys=[]
for dic in alldics:
    manual_adjustments.update(dic)  #Merged dictionaries
    for key in dic.keys():
        if key not in allkeys:
            allkeys.append(key)
        else:
            raise KeyError('In man_adjust.py, duplicate filename %s found between runs.'%(key))

