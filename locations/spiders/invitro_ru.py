from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class InvitroRUSpider(SitemapSpider, StructuredDataSpider):
    name = "invitro_ru"
    item_attributes = {"brand": "Инвитро", "brand_wikidata": "Q4200546"}
    sitemap_urls = ["https://www.invitro.ru/sitemap/offices.xml"]
    sitemap_rules = [(r"/offices/[-\w]+", "parse")]
    link_extractor = LinkExtractor(allow=r"/offices/[-\w]+/clinic.php\?ID=\d+$")
    wanted_types = ["MedicalBusiness"]
    json_parser = "chompjs"
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 300, "RETRY_TIMES": 5}
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in self.link_extractor.extract_links(response):
            yield response.follow(url=link.url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        coords = response.xpath('//div[@id="mapOfficeDetail"]/@data-coord').get()
        if coords:
            item["lat"], item["lon"] = coords.strip().split(",")
        apply_category(Categories.MEDICAL_LABORATORY, item)
        yield item
