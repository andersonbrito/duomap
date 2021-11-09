from geopy.geocoders import Nominatim
from shapely.geometry import Point, Polygon
import pandas as pd
import geopandas as gpd
import numpy as np

from shapely import wkt
# gpd.set_option('display.max_columns', 500)

# path = '/Users/anderson/GLab Dropbox/Anderson Brito/ITpS/projetos_itps/dashboard/nextstrain/run3_20210825_itps0/data/'
path = '/Users/anderson/GLab Dropbox/Anderson Brito/ITpS/projetos_itps/metasurvBR/data/metadata_genomes/'
shapefile = '/Users/anderson/GLab Dropbox/Anderson Brito/codes/geoCodes/macrorregioes_saude/macro.shp'
input = path + 'metadata_2021-11-05_upto2021-08-31_BRAonly.tsv'
coordinates = None
output = path + 'metadata_2021-11-05_upto2021-08-31_BRAonly_macro.tsv'
geo_cols = ['country', 'division', 'location']
get_coordinates = 'yes'
output_coordinates = 'yes'
lat_col = 'lat'
long_col = 'long'
unique_id = 'nm_hlt_'
extracols = ['abbrv_s', 'cd_hlt_']


geolocator = Nominatim(user_agent="email@gmail.com")  # add your email here

def load_table(file):
    df = ''
    if str(file).split('.')[-1] == 'tsv':
        separator = '\t'
        df = pd.read_csv(file, encoding='utf-8', sep=separator, dtype='str')
    elif str(file).split('.')[-1] == 'csv':
        separator = ','
        df = pd.read_csv(file, encoding='utf-8', sep=separator, dtype='str')
    elif str(file).split('.')[-1] in ['xls', 'xlsx']:
        df = pd.read_excel(file, index_col=None, header=0, sheet_name=0, dtype='str')
        df.fillna('', inplace=True)
    else:
        print('Wrong file format. Compatible file formats: TSV, CSV, XLS, XLSX')
        exit()
    return df


# Load sample metadata
df1 = load_table(input)
df1.fillna('', inplace=True)

df1['country'] = df1['country'].apply(lambda x: x.split('-')[0])
geodf = gpd.read_file(shapefile)
# geodf[unique_id] = geodf[unique_id].astype(str)
last_level = geo_cols[-1]

# input existing lat/longs
if coordinates not in ['', None]:
    if lat_col not in df1.columns.tolist():
        df1[lat_col] = ''
        df1[long_col] = ''

    dfC = load_table(coordinates)
    dfC = dfC[dfC['geolevel'].isin([last_level])]
    for id, row in dfC.iterrows():
        place_name = dfC.loc[id, 'name']
        if place_name in df1[last_level].tolist():
            lat = dfC.loc[dfC['name'] == place_name, lat_col].iloc[0]
            long = dfC.loc[dfC['name'] == place_name, long_col].iloc[0]

            # print(place_name, lat, long)

            df1.loc[df1[last_level] == place_name, lat_col] = lat
            df1.loc[df1[last_level] == place_name, long_col] = long


# print(df1)

if get_coordinates == 'yes':
    if lat_col not in df1.columns.tolist():
        lat_col = 'lat'
        long_col = 'long'
        df1[lat_col] = ''
        df1[long_col] = ''

    # find coordinates for locations not found in cache or XML file
    def find_coordinates(place):
        try:
            location = geolocator.geocode(place, language='en')
            lat, long = location.latitude, location.longitude
            coord = (str(lat), str(long))
            return coord
        except:
            coord = ('NA', 'NA')
            return coord

    found = {}
    notfound = []
    print('\nSearching for coordinates...')
    for id1, row1 in df1.iterrows():
        query = [df1.loc[id1, t] for t in geo_cols if t != 'region']

        lat = df1.loc[id1, lat_col]
        long = df1.loc[id1, long_col]
        if lat != '':
            coord = (lat, long)
            found['-'.join(query)] = coord
        else:
            coord = ('NA', 'NA')
            if '-'.join(query) not in found:
                target = query[-1]
                if target not in ['', 'NA', 'NAN', 'unknown', '-', np.nan, None]:
                    coord = find_coordinates(', '.join(query))  # search coordinates
                    found['-'.join(query)] = coord
                    print(', '.join(query) + ': ' + coord[0] + ', ' + coord[1])
            else:
                # print('Already found', '-'.join(query))
                coord = found['-'.join(query)]

            if 'NA' in coord:
                found['-'.join(query)] = coord
                if ', '.join(query) not in notfound:
                    notfound.append(', '.join(query))
            else:
                # print(traits[-1] + ', ' + address[-1] + '. Coordinates = ' + ', '.join(coord))
                df1.loc[id1, 'lat'] = coord[0]
                df1.loc[id1, 'long'] = coord[1]

    if len(notfound) > 1:
        print('\nCoordinates for these entries were not found. Try providing a file with such data, under --coordinates.')
        for entry in notfound:
            print('\t- ' + entry)

# print(df1.head())

geodf = geodf.explode()

for name, geodata in geodf.groupby(unique_id):
    for id1, row1 in df1.iterrows():
        lat = df1.loc[id1, lat_col]
        long = df1.loc[id1, long_col]
        if lat not in ['', 'NA', 'NAN', 'unknown', '-', np.nan, None]:
            point = Point(float(long), float(lat)) # coordinates

            for id2, row2 in geodata.iterrows():
                geometry = Polygon(geodata.loc[id2, 'geometry'])
                if point.within(geometry):
                    for col in [unique_id] + extracols:
                        value = geodata.loc[id2, col]
                        df1.loc[id1, col] = value
                        print(col + ' = ' + str(value))

# output updated dataframe
if output_coordinates != 'yes':
    df1 = df1.drop('lat', 1)
    df1 = df1.drop('long', 1)
df1.to_csv(output, sep='\t', index=False)

