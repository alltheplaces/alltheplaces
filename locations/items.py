# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


# TODO: In the past, all ATP items had point geometry (or, rarely,
# no known geometry at all), hence the name of this class. While this
# still is the case for the vast majority of data, it might make sense
# to rename "GeojsonPointItem" to "Feature" across the ATP codebase
# in a global search-and-replace.
class GeojsonPointItem(scrapy.Item):
    lat = scrapy.Field()
    lon = scrapy.Field()
    geometry = scrapy.Field()
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
    located_in = scrapy.Field()
    located_in_wikidata = scrapy.Field()
    nsi_id = scrapy.Field()
    extras = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self._values.get("extras"):
            self.__setitem__("extras", {})


Feature = GeojsonPointItem
