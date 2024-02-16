#!/usr/bin/env python


"""
Select property project calc area output shp.py
===============================================


Description: This script pre-processes and prepares individual property shapefiles the fire zonal stats on one property.py script.
This script reads in a list of property name, subsets them from the cadastre, calculates area in WGS84z52 and z53, adds a “uid” feature, and outputs a shapefile per property name in the chosen projection.

For a full list of spatial reference (epsg codes), read: https://spatialreference.org/ref/epsg/

Author: Rob McGregor
email: Robert.Mcgregor@nt.gov.au
Date: 12/10/2020
Version: 1.0

###############################################################################################

MIT License

Copyright (c) 2020 Rob McGregor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.


THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

################################################################################################

Input requirements:
-------------------

1.	A list of property names in an excel format (one property per row in the first column.
2.	Output projection epsg code.

------------------------------------------------------------------------------------------------

Command arguments:
------------------

--cadastre (str)
Enter the file pathway of the cadastre, this must be located where the PGB-BAS14 drive has access, and include file path, filename and file extension.

--excel (str)
Enter the file pathway of an excel document which lists the property names (one per row, in the first column).

--epsg (int)
Enter the output spatial reference epsg code (GDA94 = 4283)

--output (str)
Enter the directory for the shapefile outputs.

-----------------------------------------------------------------------------------------------

Parameters: 
-----------
epsg (int)
See command arguments.

"""


from __future__ import print_function, division
#import pdb
import fiona
import argparse
import sys
import os
import shutil
import geopandas as gpd
import pandas as pd
import osgeo.gdal as gdal
import os
from osgeo import ogr

# this sets the environmental variables for the prj folders 
# https://stackoverflow.com/questions/56764046/gdal-ogr2ogr-cannot-find-proj-db-error


#os.environ['PROJ_LIB'] =  r'C:\Users\admrmcgr\Miniconda3\envs\zonal\Library\share\proj'
#os.environ['GDAL_DATA'] = r'C:\Users\admrmcgr\Miniconda3\envs\zonal\Library\share'


def getCmdargs():

    p = argparse.ArgumentParser(description="""Input a single or multiband raster to extracts the values from the input shapefile. """)

    p.add_argument("-c","--cadastre", help="Cadastre location")
        
    p.add_argument("-e","--excel", help="Read in the excel file with all property names in the first column")
    
    p.add_argument("-r","--epsg", help="Enter the crs in epsg format (i.e. 4283)")
    
    p.add_argument("-o","--file_path", help="Output shapefile directory")
    

    cmdargs = p.parse_args()
    
    if cmdargs.cadastre is None:

        p.print_help()

        sys.exit()

    return cmdargs
   
 
def mainRoutine():
    
    # read in the command arguments
    cmdargs = getCmdargs()
    
    
    cadastre = cmdargs.cadastre
    excel= cmdargs.excel
    epsg = cmdargs.epsg
    file_path = cmdargs.file_path
    
    epsg_int = int(epsg)
    print(epsg_int)
    
    if epsg_int == 28352:
        crs_name = "GDA94z52"
        crs_output = {'init': 'EPSG:28352'}
    elif epsg_int == 28353:
        crs_name = "GDA94z53"
        crs_output = {'init': 'EPSG:28353'}  
    elif epsg_int == 4283:
        crs_name = "GDA94" 
        crs_output = {'init': 'EPSG:4283'}   
    elif epsg_int == 32752:
        crs_name = "WGS84z52"
        crs_output = {'init': 'EPSG:32752'}
    elif epsg_int == 32753:
        crs_name = "WGS84z53"
        crs_output = {'init': 'EPSG:32753'}
    elif epsg_int == 3577:
        crs_name = "Albers" 
        crs_output = {'init': 'EPSG:3577'}
    else:
        crs_name = "not_defined"
        
    # check if a directory called " + crs_name + " already exists.
    crsDir = file_path + '\\' + crs_name 
    print(crsDir)    
    
    try:
        shutil.rmtree(crsDir)

    except:
        print("The following directory was deleted: ", crs_name)

    # create folder titled with the crs extension

    os.makedirs(crsDir)
    
    
    
    # Import in the cadastre and ensure the crs is set to GDA94
    cadastre = gpd.read_file(cadastre)
    print("Cadastre crs: ", cadastre.crs)

    #read in an excel sheet with all of the property names
    properties = pd.read_excel(excel)
    properties["Property"] = properties["Property"].str.upper()
    prop_list = properties.Property.unique().tolist()
    print("Properties identified: ", prop_list)
   
    #shapefile_list =[]

    # create individual property shapefiles from a list
    for i in prop_list:
        print (i)
        #To select rows whose column value equals a scalar, some_value, use ==:
        prop = cadastre[cadastre["PROP_NAME"]== i]
        
        # Calculate area WGS84z52
        WGS84z52 = prop.to_crs(32752)
        WGS84z52["area_WGS52_ha"] = WGS84z52['geometry'].area/ (10**6)*100
        area_test = WGS84z52['geometry'].area/ (10**6)*100
        
        # Calculate area WGS84z53
        WGS84z53 = WGS84z52.to_crs(32753)
        WGS84z53["area_WGS53_ha"] = WGS84z53['geometry'].area/ (10**6)*100
        area_test = WGS84z53['geometry'].area/ (10**6)*100
        print("z53 area: ", area_test)
       
        prop1 = WGS84z53.to_crs(4283)
        
        
        prop1.reset_index(drop=True, inplace=True)
        prop1['uid']= prop1.index + 1
        property1  = str.lower(i)
        property_name = property1.replace(" ", "_")
        print("Property Name: ", property_name)
        out_path = (crsDir + "//" + property_name + "_" + crs_name + ".shp")
        #shapefile_list.append(file_path)
        print("Original crs: ", prop1.crs)
        output = prop1.to_crs(crs_output)
        print("Output crs: ", output.crs)
        output.to_file(out_path, driver = 'ESRI Shapefile')
        print("--------------------------\n Export of " + property1 + " complete. \n ----------------------")

              
if __name__ == "__main__":
    mainRoutine()    