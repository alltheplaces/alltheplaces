from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LeroidumatelasFRSpider(CrawlSpider, StructuredDataSpider):
    name = "leroidumatelas_fr"
    item_attributes = {"brand": "Le Roi du Matelas", "brand_wikidata": "Q122931917"}
    start_urls = ["https://www.leroidumatelas.fr/magasins/"]
    rules = [Rule(LinkExtractor(allow=r"/magasin/"), callback="parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").replace("Mon magasin Le Roi du Matelas ", "")
        apply_category(Categories.SHOP_BED, item)
        yield item
