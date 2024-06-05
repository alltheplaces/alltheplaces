import scrapy

from locations.hours import (
    DAYS_DE,
    DAYS_DK,
    DAYS_EN,
    DAYS_ES,
    DAYS_FI,
    DAYS_FR,
    DAYS_IT,
    DAYS_NL,
    DAYS_SE,
    OpeningHours,
)
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class GantSpider(scrapy.Spider):
    name = "gant"
    item_attributes = {
        "brand": "GANT",
        "brand_wikidata": "Q1493667",
    }
    start_urls = [
        ("https://www.gant.be/stores", DAYS_NL),
        ("https://dk.gant.com/stores", DAYS_DK),
        ("https://fi.gant.com/stores", DAYS_FI),
        ("https://fr.gant.com/stores", DAYS_FR),
        ("https://de.gant.com/stores", DAYS_DE),
        ("https://it.gant.com/stores", DAYS_IT),
        ("https://nl.gant.com/stores", DAYS_NL),
        ("https://pt.gant.com/stores", DAYS_ES),
        ("https://www.gant.es/stores", DAYS_ES),
        ("https://www.gant.se/stores", DAYS_SE),
        ("https://ch.gant.com/stores", DAYS_DE),
        ("https://www.gant.co.uk/stores", DAYS_EN),
    ]

    def start_requests(self):
        for url, language in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={"language": language})

    def parse(self, response, language):
        if (part_url := response.xpath("//*[@data-lat]/@data-action-url").get()) is not None:
            complete_url = response.url.replace("/stores", "") + part_url
            yield scrapy.Request(url=complete_url, callback=self.parse_website, cb_kwargs={"language": language})

    def parse_website(self, response, language):
        stores = response.json()["stores"]
        for store in stores:
            item = Feature()
            item["ref"] = store.get("ID", None)
            item["name"] = store.get("name", None)
            item["city"] = store.get("city", None)
            item["lat"] = store.get("latitude", None)
            item["lon"] = store.get("longitude", None)
            item["phone"] = store.get("phone", None)
            item["country"] = store.get("countryCode", None)
            item["postcode"] = store.get("postalCode", None)
            item["email"] = store.get("email", None)
            item["street_address"] = clean_address([store.get("address1"), store.get("address2")])
            oh = OpeningHours()
            for opening_hour in store["storeHours"]:
                oh.add_ranges_from_string(
                    ranges_string=opening_hour["day"] + " " + opening_hour["hours"], days=language, delimiters=" - "
                )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
