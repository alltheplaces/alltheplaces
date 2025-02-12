from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_CZ, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone, get_url


class O2CZSpider(SitemapSpider):
    name = "o2_cz"
    allowed_domains = ["www.o2.cz"]
    sitemap_urls = ["https://www.o2.cz/sitemap/prodejny.xml"]
    sitemap_rules = [(r"^https://www.o2.cz/prodejny/.*$", "parse")]
    item_attributes = {
        "brand": "O2",
        "brand_wikidata": "Q1759255",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.removeprefix("https://www.o2.cz/prodejny/")
        item["name"] = response.xpath("//h1/text()").get()
        item["addr_full"] = (
            response.xpath("//a[contains(@href, 'www.google.com/maps')]/@href").get().split("destination=")[-1]
        )
        item["lat"] = response.xpath("//*[@id='stores-config']/@data-store-lat").get()
        item["lon"] = response.xpath("//*[@id='stores-config']/@data-store-lng").get()
        item["website"] = get_url(response)
        extract_email(item, response)
        extract_phone(item, response)

        oh = OpeningHours()
        for row in response.xpath("//div[contains(.,'Otevírací doba')]//tr"):
            day, hrs = row.xpath("td/text()[normalize-space()]").getall()
            oh.add_ranges_from_string(day.strip() + " " + hrs.strip(), DAYS_CZ)
        item["opening_hours"] = oh.as_opening_hours()

        yield item
