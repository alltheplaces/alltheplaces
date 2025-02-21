from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.pipelines.address_clean_up import clean_address


class CoopersHawkUSSpider(SitemapSpider, StructuredDataSpider):
    name = "coopers_hawk_us"
    item_attributes = {"brand": "Cooper's Hawk", "brand_wikidata": "Q17511079"}
    allowed_domains = ["chwinery.com"]
    sitemap_urls = ["https://chwinery.com/sitemaps-1-section-location-1-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/chwinery\.com\/locations\/[\w\-]+$", "parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["addr_full"] = clean_address(response.xpath('//p[@class="banner__subhead"]/a[1]/text()').get())
        if not item["addr_full"]:
            # Unopened restaurants do not have addresses listed.
            return
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = item.pop("name", None)
        item.pop("image", None)
        item.pop("facebook", None)
        item.pop("twitter", None)

        item["opening_hours"] = OpeningHours()
        hours_text = " ".join(response.xpath('(//table[@class="hours-table"])[1]//tr[@class="hours-table__row"]//text()').getall())
        item["opening_hours"].add_ranges_from_string(hours_text)

        apply_category(Categories.RESTAURANT, item)
        yield item
