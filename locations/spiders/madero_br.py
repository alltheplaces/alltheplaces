import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PT, DELIMITERS_PT, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class MaderoBRSpider(SitemapSpider, StructuredDataSpider):
    name = "madero_br"
    item_attributes = {"brand": "Madero", "brand_wikidata": "Q115206711"}
    sitemap_urls = ["https://www.restaurantemadero.com.br/pt/sitemap.xml"]
    sitemap_rules = [(r"/restaurante/\w\w/[-\w]+/[-\w]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        item["lat"] = response.xpath("//@data-lat").get() or None
        item["lon"] = response.xpath("//@data-lng").get() or None

        # Dine-in hours come first, followed by take away, delivery and drive-thru hours
        hours = " ".join(response.xpath('//*[@itemprop="openingHours"]//text()').getall())
        hours = re.split(r"\b(?:TAKE|DELIVERY|DRIVE|MADEROLAND)", hours, flags=re.IGNORECASE)[0]
        hours = re.sub(r"(\d)\s*h\s*(\d{2})?(?!\d)", lambda m: f"{m[1]}:{m[2] or '00'}", hours, flags=re.IGNORECASE)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            hours,
            days={**DAYS_PT, "Sabado": "Sa", "Sabádo": "Sa", "Domingos": "Su"},
            delimiters=DELIMITERS_PT + ["e", "as"],
        )

        apply_category(Categories.FAST_FOOD, item)

        yield item
