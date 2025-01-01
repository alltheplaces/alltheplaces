from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.items import Feature


class LagerhausATSpider(SitemapSpider):
    name = "lagerhaus_at"
    item_attributes = {"brand": "Lagerhaus", "brand_wikidata": "Q1232873"}
    sitemap_urls = ["https://lagerhaus.at/sitemap/index.xml"]
    sitemap_rules = [("/standort/", "parse")]
    sitemap_follow = ["locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath("//h1").xpath("normalize-space()").get()
        item["street_address"] = response.xpath('//*[@class="A5SKTxfddRWFz7lYLFXx"]').xpath("normalize-space()").get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@class="crIzOQn7PNuYkyfoUq9P"]//*[@class="m4VniD5GavaCh3bqMUKm"]'):
            day = sanitise_day(
                day_time.xpath('.//*[@class="HUI8SAWj6xc116qIMHGC GtBm40epTsrl8DTPJIA_"]/text()').get(), DAYS_DE
            )
            for time_string in day_time.xpath(".//li"):
                time = time_string.xpath(".//text()").get()
                if "geschlossen" in time:
                    item["opening_hours"].set_closed(day)
                else:
                    open_time, close_time = time.replace("Uhr", "").split("-")
                    item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        yield item
