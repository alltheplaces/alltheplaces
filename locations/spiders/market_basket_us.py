import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MarketBasketUSSpider(scrapy.Spider):
    name = "market_basket_us"
    item_attributes = {"brand": "Market Basket", "brand_wikidata": "Q2079198"}
    start_urls = [
        "https://www.shopmarketbasket.com/wp-json/mb/v1/store-locations/?lat=42.7768318&lng=-71.2161428&all=1"
    ]

    def parse(self, response):
        for poi in response.json():
            item = DictParser.parse(poi)
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
