import scrapy
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.geo import city_locations


class CardFactoryGBSpider(Spider):
    name = "card_factory_gb"
    item_attributes = {"brand": "Card Factory", "brand_wikidata": "Q5038192"}
    url_template = "https://www.cardfactory.co.uk/on/demandware.store/Sites-cardfactory-UK-Site/default/Stores-FindStores?showMap=true&radius=100&lat={}&long={}"

    def start_requests(self):
        for country in ["GB", "IE"]:
            for city in city_locations(country, 10000):
                yield scrapy.Request(
                    self.url_template.format(city["latitude"], city["longitude"]),
                    callback=self.parse,
                    cb_kwargs=dict(country=country),
                )

    def parse(self, response, country):
        for store in response.json()["stores"]["stores"]:
            item = DictParser.parse(store)
            item["country"] = country
            yield item
