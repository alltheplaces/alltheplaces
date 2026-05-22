from typing import Iterable, Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day, DAYS_ES
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

CHARTER = {"brand": "Charter", "brand_wikidata": "Q95916752"}


class ConsumESSpider(SitemapSpider, StructuredDataSpider):
    name = "consum_es"
    item_attributes = {"brand": "Consum", "brand_wikidata": "Q8350308"}
    sitemap_urls = ["https://www.consum.es/robots.txt"]
    sitemap_rules = [(r"/supermercados/([^/]+)/$", "parse")]
    wanted_types = ["Store"]
    search_for_facebook = False
    search_for_twitter = False

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for e in entries:
            if "/supermercados/" in e["loc"] and not e["loc"].endswith("/"):
                e["loc"] += "/"
            yield e

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = response.url

        if ld_data.get("description") == "Charter":
            item.update(CHARTER)

        item["extras"]["website:es"] = response.xpath('//link[@rel="alternate"][@hreflang="es"]/@href').get()
        item["extras"]["website:ca"] = response.xpath('//link[@rel="alternate"][@hreflang="ca"]/@href').get()
        item["extras"]["website:en"] = response.xpath('//link[@rel="alternate"][@hreflang="en"]/@href').get()

        try:
            item["opening_hours"] = self.parse_hours(response)
        except Exception:
            pass

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for rule in response.xpath('//p[@class="day"]/text()').getall():
            day, times = rule.split(": ", 1)
            day = sanitise_day(day, DAYS_ES)
            if times == "Cerrado":
                oh.set_closed(day)
            else:
                for t in times.split(" y "):
                    oh.add_range(day, *t.strip().split("-"))
        return oh
