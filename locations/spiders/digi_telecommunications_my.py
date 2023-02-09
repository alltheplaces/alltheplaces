import re

from locations.storefinders.storepoint import StorepointSpider


class DiGiTelecommunicationsMYSpider(StorepointSpider):
    name = "digi_telecommunications_my"
    item_attributes = {"brand": "DiGi Telecommunications", "brand_wikidata": "Q3268530"}
    key = "1624a4f7eafca0"
