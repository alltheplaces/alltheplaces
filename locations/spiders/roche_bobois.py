from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RocheBoboisSpider(SitemapSpider, StructuredDataSpider):
    name = "roche_bobois"
    item_attributes = {"brand": "Roche Bobois", "brand_wikidata": "Q3437504"}
    sitemap_urls = ["https://www.roche-bobois.com/en-GB/sitemap_index.xml"]
    sitemap_rules = [(r"com/en-GB/showrooms/[^/]+/\w(\d+)\.html$", "parse")]
    wanted_types = ["FurnitureStore"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        try:
            oh = OpeningHours()
            for rule in ld_data["openingHours"]:
                day, times = rule.split(" ", 1)
                if times == "Closed":
                    oh.set_closed(day)
                else:
                    for time in times.split(" / "):
                        oh.add_range(day, *time.split(" - "), time_format="%I:%M %p")
            item["opening_hours"] = oh
        except Exception:
            pass

        item["website"] = item["extras"]["website:en"] = response.xpath(
            '//link[@rel="alternate"][@hreflang="en"]/@href'
        ).get()
        item["extras"]["website:fr"] = response.xpath('//link[@rel="alternate"][@hreflang="fr-fr"]/@href').get()

        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
