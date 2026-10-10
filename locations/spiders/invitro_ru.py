from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

NATIONAL_HOTLINE = "8002003630"


class InvitroRUSpider(SitemapSpider, StructuredDataSpider):
    name = "invitro_ru"
    item_attributes = {"brand": "Инвитро", "brand_wikidata": "Q4200546"}
    sitemap_urls = ["https://www.invitro.ru/sitemap/offices.xml"]
    sitemap_rules = [(r"/offices/[-\w]+/clinic\.php\?ID=\d+$", "parse_sd")]
    wanted_types = ["MedicalBusiness"]
    json_parser = "chompjs"
    search_for_email = False
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 300, "RETRY_TIMES": 5}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        item["ref"] = response.url.split("ID=")[-1]
        if coords := response.xpath('//div[@id="mapOfficeDetail"]/@data-coord').get():
            item["lat"], item["lon"] = coords.strip().split(",")
        if phone := item.get("phone"):
            if "".join(filter(str.isdigit, phone)).endswith(NATIONAL_HOTLINE):
                item["phone"] = None
        apply_category(Categories.MEDICAL_LABORATORY, item)
        yield item
