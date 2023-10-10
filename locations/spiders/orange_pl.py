import scrapy
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class OrangePLSpider(SitemapSpider):
    name = "orange_pl"
    item_attributes = {"brand": "Orange", "brand_wikidata": "Q1431486"}
    sitemap_urls = ["https://salony.orange.pl/client/sitemap-locations-pl.xml.gz"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "x-algolia-api-key": "7a46160ed01bb0af2c2af8d14b97f3c5",
            "x-algolia-application-id": "0KNEMTBXX3",
        }
    }

    def parse(self, response):
        store_id = response.url.rsplit("-")[-1]
        yield scrapy.Request(
            url=f"https://0knemtbxx3-dsn.algolia.net/1/indexes/OEPL_en/{store_id}",
            callback=self.parse_poi,
            cb_kwargs=dict(website=response.url),
        )

    def parse_poi(self, response, website):
        poi = response.json()
        poi["street_address"] = ", ".join(filter(None, [poi.pop("street1"), poi.pop("street2")]))
        poi["addr_full"] = ", ".join(filter(None, poi["formatted_address"]))
        poi["location"] = poi.pop("_geoloc")
        item = DictParser.parse(poi)
        item["country"] = poi["country"]["code"]
        item["city"] = poi["city"]["name"]
        item["website"] = website
        self.parse_hours(item, poi)
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item

    def parse_hours(self, item, poi):
        if hours := poi.get("formatted_opening_hours"):
            try:
                oh = OpeningHours()
                for day, hour in hours.items():
                    for times in hour:
                        oh.add_range(day, times.split("-")[0], times.split("-")[1], time_format="%I:%M%p")
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse hours {hours}: {e}")
