from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_CZ, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone, get_url


class O2CZSpider(SitemapSpider):
    name = "o2_cz"
    allowed_domains = ["www.o2.cz"]
    sitemap_urls = ["https://www.o2.cz/sitemap/prodejny.xml"]
    sitemap_rules = [("/prodejny/", "parse")]
    item_attributes = {
        "brand": "O2",
        "brand_wikidata": "Q1759255",
    }

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            entry["loc"] = entry["loc"].replace(".xml", "")
            yield entry

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.removeprefix("https://www.o2.cz/prodejny/")
        item["addr_full"] = (
            response.xpath("//a[contains(@href, 'www.google.com/maps')]/@href").get().split("destination=")[-1]
        )
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["website"] = get_url(response)
        extract_email(item, response)
        extract_phone(item, response)

        oh = OpeningHours()
        for row in response.xpath("//div[contains(.,'Otevírací doba')]//tr"):
            day, hrs = row.xpath("td/text()[normalize-space()]").getall()
            if day := sanitise_day(day.strip(), DAYS_CZ):
                if "Zavřeno" in hrs.title():
                    oh.set_closed(day)
                else:
                    oh.add_ranges_from_string(day + " " + hrs.strip())
        item["opening_hours"] = oh

        yield item
