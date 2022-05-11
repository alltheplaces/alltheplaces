# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


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
    opening_hours = scrapy.Field()
    ref = scrapy.Field()
    brand = scrapy.Field()
    brand_wikidata = scrapy.Field()
    image = scrapy.Field()
    extras = scrapy.Field()
    source_data = scrapy.Field()


class SourceData(scrapy.Item):
    """
    Source data associated with the creation of this POI. Pipeline code may well find it useful.
    For example, social media links may optionally be extracted from individual POI websites.
    """
    response = scrapy.Field()
    # The entry used to generate the POI.
    ld_json = scrapy.Field()


def source_data(item, response=None):
    """
    Return the source data structure for the item, allocated if necessary. Optionally
    set the response object component of the source data.
    """
    if not item.get('source_data'):
        item['source_data'] = SourceData()
    if response:
        item['source_data']['response'] = response
    return item['source_data']
