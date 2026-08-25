import json
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
        item["addr_full"] = item.pop("street_address")
        item["branch"] = item.pop("name").removeprefix("Audika ")
        item["website"] = response.url
        item["ref"] = json.loads(response.xpath('//script[@class="clinicPageConfiguration"]/text()').get())["olb"][
            "clinic"
        ]["ExternalClinicCode"]

        if image := item.get("image"):
            if "retail/shared/images/clinic" in image:
                item["image"] = None
            else:
                item["image"] = image.replace("https://www.audika.co.ukhttps://www.audika.co.ukhttps", "https")

        if item.get("email") in ["info@audika.co.uk"]:
            del item["email"]

        item["opening_hours"] = OpeningHours()
        for str in raw_data.get("openingHours"):
            item["opening_hours"].add_ranges_from_string(str)
        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
