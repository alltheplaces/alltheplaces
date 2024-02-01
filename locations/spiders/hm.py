import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# The webpage with the country list seems to block the spider in weekly runs, while the API doesn't.
# The list is used only if "use_hardcoded_countries" is True.
# Last update: Feb 2024
HM_COUNTRIES = [
    "hu",
    "nz",
    "cn",
    "cy",
    "jo",
    "kz",
    "pl",
    "es",
    "pt",
    "lu",
    "qa",
    "co",
    "cl",
    "om",
    "at",
    "ie",
    "ro",
    "us",
    "gb",
    "mk",
    "za",
    "sk",
    "se",
    "ae",
    "ma",
    "kh",
    "bh",
    "hr",
    "fi",
    "be",
    "au",
    "al",
    "sa",
    "id",
    "fr",
    "cz",
    "tr",
    "xk",
    "ua",
    "sg",
    "mo",
    "my",
    "rs",
    "si",
    "th",
    "nl",
    "bg",
    "by",
    "ec",
    "pe",
    "kw",
    "tn",
    "tw",
    "vn",
    "ba",
    "lv",
    "gt",
    "cr",
    "gr",
    "lt",
    "no",
    "lb",
    "hk",
    "it",
    "ee",
    "dk",
    "ge",
    "eg",
    "ru",
    "jp",
    "ph",
    "de",
    "il",
    "mx",
    "ch",
    "is",
    "uy",
    "pa",
    "ca",
    "in",
    "kr",
]


class HMSpider(scrapy.Spider):
    name = "hm"
    item_attributes = {"brand": "H&M", "brand_wikidata": "Q188326"}

    use_hardcoded_countries = True

    def country_url(self, country_code):
        return f"https://api.storelocator.hmgroup.tech/v2/brand/hm/stores/locale/en_us/country/{country_code}?_type=json&campaigns=true&departments=true&openinghours=true"

    def start_requests(self):
        if self.use_hardcoded_countries:
            for country_code in HM_COUNTRIES:
                yield scrapy.Request(self.country_url(country_code), callback=self.parse_country)
        else:
            yield scrapy.Request("http://www.hm.com/entrance.ahtml", callback=self.parse)

    def parse(self, response):
        for country_code in response.xpath("//@data-location").getall():
            yield scrapy.Request(self.country_url(country_code), callback=self.parse_country)

    def parse_country(self, response):
        for store in response.json()["stores"]:
            store.update(store.pop("address"))
            store["street_address"] = ", ".join(filter(None, [store.get("streetName1"), store.get("streetName2")]))

            item = DictParser.parse(store)

            item["ref"] = store["storeCode"]
            item["extras"] = {"storeClass": store.get("storeClass")}

            oh = OpeningHours()
            for rule in store["openingHours"]:
                oh.add_range(rule["name"], rule["opens"], rule["closes"])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
