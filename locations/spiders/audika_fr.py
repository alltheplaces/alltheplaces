import html
import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AudikaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "audika_fr"
    item_attributes = {"brand": "Audika", "brand_wikidata": "Q2870745"}
    sitemap_urls = ["https://www.audika.fr/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.audika\.fr/centres/[^/]+/[^/]+$", "parse_sd")]
    search_for_facebook = False
    search_for_email = False

    def post_process_item(self, item: Feature, response: TextResponse, raw_data: dict, **kwargs) -> Iterable[Feature]:
        item["addr_full"] = item.pop("street_address")
        item["branch"] = html.unescape(item.pop("name")).removeprefix("Audioprothésiste Audika ")
        item["website"] = response.url
        item["ref"] = json.loads(response.xpath('//script[@class="clinicPageConfiguration"]/text()').get())["olb"][
            "clinic"
        ]["ExternalClinicCode"]

        if image := item.get("image"):
            if "retail/shared/images/clinic" in image:
                item["image"] = None
            elif "https://assets-we.rt.demant.com" in image:
                item["image"] = "https://assets-we.rt.demant.com" + image.split("https://assets-we.rt.demant.com", 1)[1]

        item["opening_hours"] = OpeningHours()
        for rule in raw_data.get("openingHours", []):
            item["opening_hours"].add_ranges_from_string(rule)

        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
