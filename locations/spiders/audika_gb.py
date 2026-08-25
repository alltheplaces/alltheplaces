import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AudikaGBSpider(CrawlSpider, StructuredDataSpider):
    name = "audika_gb"
    item_attributes = {"brand": "Audika", "brand_wikidata": "Q2870745"}
    start_urls = ["https://www.audika.co.uk/hearing-aids-centre/all-clinics"]
    rules = [Rule(LinkExtractor(allow=r"/hearing-aids-centre/[a-z-]+/audika-"), callback="parse")]
    wanted_types = ["LocalBusiness"]
    search_for_facebook = False
    search_for_email = False

    def post_process_item(self, item: Feature, response: TextResponse, raw_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name").removeprefix("Audika ")
        centerid = re.search(
            r"([0-9]+)$",
            response.xpath("//a[starts-with(@href,'/book-appointment/online-booking?centerid=')]/@href").get(),
        )
        if centerid:
            item["extras"]["center_id"] = centerid.group(1)
        item["addr_full"] = item.pop("street_address")
        item["opening_hours"] = OpeningHours()
        for str in raw_data.get("openingHours"):
            item["opening_hours"].add_ranges_from_string(str)
        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
