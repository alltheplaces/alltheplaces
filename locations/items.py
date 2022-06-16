# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SourceData(scrapy.Item):
    """
    Source data associated with the creation of this POI. Pipeline code may well find it useful.
    For example, social media links may optionally be extracted from individual POI websites.
    """

    response = scrapy.Field()
    # The entry used to generate the POI.
    ld_json = scrapy.Field()


class GeojsonPointItem(scrapy.Item):
    lat = scrapy.Field()
    lon = scrapy.Field()
    name = scrapy.Field()
    addr_full = scrapy.Field()
    housenumber = scrapy.Field()
    street = scrapy.Field()
    street_address = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    postcode = scrapy.Field()
    country = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    website = scrapy.Field()
    twitter = scrapy.Field()
    facebook = scrapy.Field()
    opening_hours = scrapy.Field()
    image = scrapy.Field()
    ref = scrapy.Field()
    brand = scrapy.Field()
    brand_wikidata = scrapy.Field()
    image = scrapy.Field()
    located_in_wikidata = scrapy.Field()
    extras = scrapy.Field()
    source_data = scrapy.Field()

    def has_geo(self) -> bool:
        """
        Is the POI considered to have a position set.
        :return: true iff both latitude and longitude have float values one of which is non zero
        """
        lat_val = self.get("lat")
        lon_val = self.get("lon")
        if isinstance(lat_val, float) and isinstance(lon_val, float):
            return bool(self.get("lat") or self.get("lon"))
        return False

    def set_geo(self, lat, lon) -> bool:
        """
        Set the position of the POI indicating is successful or not
        :param lat: item latitude
        :param lon: item longitude
        :return: true iff item location updated and considered valid
        """
        try:
            lat_val = float(lat)
            lon_val = float(lon)
            self["lat"] = lat_val
            self["lon"] = lon_val
            return self.has_geo()
        except (TypeError, ValueError):
            return False

    def set_located_in(self, brand, logger):
        logger.info("set %s instance to be located in %s", self.get("brand"), brand)
        self["located_in_wikidata"] = brand.brand_wikidata

    def set_source_data(self, response=None) -> SourceData:
        """
        Return the source data structure for the item, allocated if necessary. Optionally
        set the response object component of the source data.
        """
        if not self.get("source_data"):
            self["source_data"] = SourceData()
        if response:
            self["source_data"]["response"] = response
        return self["source_data"]
