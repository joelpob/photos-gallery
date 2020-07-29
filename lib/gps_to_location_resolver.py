import requests
import sys
import os
import logging
import coloredlogs
import zipfile
import pandas as pd
import shutil
from scipy import spatial
from typing import List

class LatLongResolver():
    def __init__(self, cities_model_filename: str):
        if not os.path.exists(cities_model_filename):
            self.build_cities_dataset(cities_model_filename)
        self.cities_filename = cities_model_filename
        self.pd = pd.read_csv(self.cities_filename)
        self.init()

    def init(self):
        # build several trees based on population
        self.psmall = self.pd[(self.pd.population >= 5000) & (self.pd.population < 20000)]
        self.pmedium = self.pd[(self.pd.population >= 20000) & (self.pd.population < 1000000)]
        self.plarge = self.pd[(self.pd.population >= 1000000) & (self.pd.population < 10000000)]

        self.t5000 = spatial.KDTree(list(zip(self.psmall.latitude,
                                             self.psmall.longitude)))

        self.t6000 = spatial.KDTree(list(zip(self.pmedium.latitude,
                                             self.pmedium.longitude)))

        self.t7000 = spatial.KDTree(list(zip(self.plarge.latitude,
                                             self.plarge.longitude)))

    def nearest_helper(self, dataset: pd.DataFrame, tree: spatial.KDTree, latitude: float, longitude: float) -> List[str]:
        distance, index = tree.query([(latitude, longitude)])
        result = dataset.iloc[index]
        country = result.Country.item()
        city = result.asciiname.item()
        latitude = result.latitude.item()
        longitude = result.longitude.item()
        return [city, country]

    def build_cities_dataset(self, model_filename: str) -> pd.DataFrame:
        if os.path.exists(model_filename):
            return pd.read_csv(model_filename)

        download_url = 'http://download.geonames.org/export/dump/'

        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        logging.info('downloading {}'.format(download_url + 'cities500.zip'))
        r = requests.get(download_url + 'cities500.zip')
        with open('tmp/cities500.zip', 'wb') as f:
            f.write(r.content)

        logging.info('downloading {}'.format(download_url + 'countryInfo.txt'))
        r2 = requests.get(download_url + 'countryInfo.txt')
        with open('tmp/countryInfo.txt', 'wb') as f2:
            f2.write(r2.content)

        with zipfile.ZipFile('tmp/cities500.zip', 'r') as zip_ref:
            zip_ref.extractall('tmp')

        cities = pd.read_csv('tmp/cities500.txt', sep='\t',
                             names=['geonameid', 'name', 'asciiname', 'alternatenames',
                                    'latitude', 'longitude', 'feature class', 'feature code', 'country code', 'cc2',
                                    'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code',
                                    'population', 'elevation', 'dem', 'timezone', 'modification date'])

        # remove all the comment junk at the beginning of the file
        text = ''
        with open('tmp/countryInfo.txt', 'r') as f3:
            text = f3.read()
            text = text[text.index('#ISO') + 1:]
        with open('tmp/countryInfo_rewritten.txt', 'w') as f4:
            f4.write(text)

        countries = pd.read_csv('tmp/countryInfo_rewritten.txt', sep='\t')

        shaped_cities = cities[['asciiname', 'latitude', 'longitude', 'country code', 'population']]
        shaped_countries = countries[['ISO', 'Country']]
        result = shaped_cities.merge(shaped_countries, left_on='country code', right_on='ISO')

        result.to_csv(model_filename, header=True, index=False)
        shutil.rmtree('tmp')

        return result

    def nearest(self, latitude: float, longitude: float) -> List[str]:
        result = [self.nearest_helper(self.psmall, self.t5000, latitude, longitude),
                  self.nearest_helper(self.pmedium, self.t6000, latitude, longitude),
                  self.nearest_helper(self.plarge, self.t7000, latitude, longitude)]

        flat_list = [item for sublist in result for item in sublist]
        return list(set(flat_list))


coloredlogs.install(level='INFO')
