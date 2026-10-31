from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LapeyreFRSpider(SitemapSpider, StructuredDataSpider):
    name = "lapeyre_fr"
    item_attributes = {"brand": "Lapeyre", "brand_wikidata": "Q3117467"}
    allowed_domains = ["magasins.lapeyre.fr"]
    sitemap_urls = ["https://magasins.lapeyre.fr/sitemap.xml"]
    sitemap_rules = [(r"/lapeyre-[^/]+-\d+$", "parse_sd")]
    wanted_types = ["HomeGoodsStore"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Lapeyre ")
        item["ref"] = item["ref"].rsplit("#store-", 1)[-1]
        yield item
