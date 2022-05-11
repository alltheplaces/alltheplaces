# -*- coding: utf-8 -*-
from locations.items import GeojsonPointItem


class Brand:
    """
    Encapsulate brand information for a site, brand identifiers come from wikidata.
    A wikidata Q-code helps us disambiguate "things". It helps matching with other such disambiguated data sets.
    """

    def __init__(self, brand, brand_wikidata):
        self.brand = brand
        self.brand_wikidata = brand_wikidata

    def __str__(self):
        return self.brand

    @staticmethod
    def from_wikidata(brand, brand_wikidata):
        """
        Create a brand class instance.
        :param brand: the brand name
        :param brand_wikidata: the brand wikidata Q-code
        :return: brand class instance
        """
        return Brand(brand, brand_wikidata)

    def item(self, response_or_url=None):
        """
        Create a boiler plate POI item based on the brand. A HTTP response structure or URL
        for the POI may optionally be provided.
        """
        # TODO: this would a point to lazily integrate with NSI / wikidata etc to pick up extra brand information
        item = GeojsonPointItem()
        item['brand'] = self.brand
        item['brand_wikidata'] = self.brand_wikidata
        if not response_or_url:
            return item
        if isinstance(response_or_url, str):
            url = response_or_url
        else:
            item.set_source_data(response_or_url)
            url = response_or_url.url

        item['website'] = url
        # Use the individual POI URL as the ref, can always be re-worked in the spider if not appropriate
        item['ref'] = url
        return item
