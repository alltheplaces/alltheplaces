import scrapy
from geonamescache import GeonamesCache

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class HMSpider(scrapy.Spider):
    name = "hm"
    item_attributes = {"brand": "H&M", "brand_wikidata": "Q188326"}

    use_hardcoded_countries = True

    def country_url(self, country_code):
        return f"https://api.storelocator.hmgroup.tech/v2/brand/hm/stores/locale/en_us/country/{country_code}?_type=json&campaigns=true&departments=true&openinghours=true"

    def start_requests(self):
        if self.use_hardcoded_countries:
            for country in GeonamesCache().get_countries():
                yield scrapy.Request(self.country_url(country.lower()), callback=self.parse_country)
        else:
            yield scrapy.Request("http://www.hm.com/entrance.ahtml", callback=self.parse)

    def parse(self, response):
        for country_code in response.xpath("//@data-location").getall():
            yield scrapy.Request(self.country_url(country_code), callback=self.parse_country)

    def parse_country(self, response):
        for store in response.json()["stores"]:
            store.update(store.pop("address"))
            store["street_address"] = clean_address([store.get("streetName1"), store.get("streetName2")])

            item = DictParser.parse(store)

            item["ref"] = store["storeCode"]
            item["extras"] = {"storeClass": store.get("storeClass")}

            oh = OpeningHours()
            for rule in store["openingHours"]:
                oh.add_range(rule["name"], rule["opens"], rule["closes"])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
