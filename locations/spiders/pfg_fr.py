from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class PfgFRSpider(StructuredDataSpider, CamoufoxSpider):
    name = "pfg_fr"
    item_attributes = {"brand": "PFG", "brand_wikidata": "Q3396087"}
    allowed_domains = ["www.pfg.fr"]
    start_urls = ["https://www.pfg.fr/nos-agences"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_DELAY": 4}

    def parse(self, response: Response, **kwargs):
        # Department index page links to one page per department.
        for url in response.xpath('//a[starts-with(@href, "/nos-agences/")]/@href').getall():
            if url.count("/") == 2:
                yield response.follow(url, callback=self.parse_department)

    def parse_department(self, response: Response, **kwargs):
        for url in response.xpath('//a[contains(@href, "/agence-pompes-funebres-pfg-")]/@href').getall():
            yield response.follow(url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data, **kwargs):
        apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)
        yield item
