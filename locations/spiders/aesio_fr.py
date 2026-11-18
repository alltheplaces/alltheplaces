from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AesioFRSpider(SitemapSpider, StructuredDataSpider):
    name = "aesio_fr"
    item_attributes = {"brand": "Aésio Mutuelle", "brand_wikidata": "Q56320205"}
    allowed_domains = ["agences.aesio.fr"]
    sitemap_urls = ["https://agences.aesio.fr/locationsitemap1.xml"]
    wanted_types = ["InsuranceAgency"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        item["ref"] = response.url.rstrip("/").split("/")[-1].split("-", 1)[0]
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
