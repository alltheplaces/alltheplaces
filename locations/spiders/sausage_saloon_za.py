from typing import Any

import scrapy
from scrapy import Spider

from locations.storefinders.wordpress_heron_foods_spider import WordpressHeronFoodsSpider

class SausageSaloonZASpider(WordpressHeronFoodsSpider):
    name = "sausage_saloon_za"
    item_attributes = {"brand": "Sausage Saloon", "brand_wikidata": "Q116619342"}
    domain = "www.sausagesaloon.co.za"
    radius = 10000000
    lat = -29
    lon = 24