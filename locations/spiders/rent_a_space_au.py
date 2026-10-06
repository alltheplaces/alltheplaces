import re
from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RentASpaceAUSpider(SitemapSpider, StructuredDataSpider):
    name = "rent_a_space_au"
    item_attributes = {"brand": "Rent a Space", "name": "Rent a Space"}
    sitemap_urls = ["https://rentaspace.com.au/location-sitemap.xml"]
    sitemap_rules = [(r"/self-storage/[^/]+/[^/]+/?$", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        # Structured data hours list only the weekend, the page body has the real office hours
        ld_data.pop("openingHoursSpecification", None)

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["addr_full"] = item.pop("street_address", None)
        item["branch"] = item.pop("name").removesuffix(" Storage")

        text = " ".join(t.strip() for t in response.xpath("//text()").getall() if t.strip())
        if m := re.search(r"Office Hours (Monday.*?)Public Holidays", text):
            item["opening_hours"] = oh = OpeningHours()
            oh.add_ranges_from_string(re.sub(r"Office Closed.*", "closed", m.group(1)))

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
