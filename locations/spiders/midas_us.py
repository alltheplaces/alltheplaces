import scrapy

from locations.dict_parser import DictParser


class MidasUSSpider(scrapy.Spider):
    name = "midas_us"
    item_attributes = {"brand": "Midas", "brand_wikidata": "Q3312613"}
    start_urls = ["https://www.midas.com/store"]

    def parse(self, response):
        for state_url in response.css("a.locations-columns__link::attr(href)").getall():
            state_abbreviation = state_url.split("/")[-1]
            yield scrapy.Request(
                "https://www.midas.com/partialglobalsearch/getstatestorelist?state=" + state_abbreviation,
                callback=self.parse_state,
            )

    def parse_state(self, response):
        for store in response.json():
            store["street_address"] = store.pop("Address")
            item = DictParser.parse(store)
            item["website"] = store["ShopDetailsLink"]
            item["name"] = "Midas"
            # Emails are not unique to each store and some are personal email addresses.
            item["email"] = None
            yield item
