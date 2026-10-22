from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class EasycashFRSpider(CrawlSpider, StructuredDataSpider):
    name = "easycash_fr"
    item_attributes = {"brand": "Easycash", "brand_wikidata": "Q105395978", "name": "Easycash"}
    allowed_domains = ["magasins.easycash.fr"]
    start_urls = ["https://magasins.easycash.fr/"]
    rules = [Rule(LinkExtractor(allow=r"/[^/]+-\w+/ENT\d+-[^/]+$"), callback="parse_sd")]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url.split("/")[-1].split("-", 1)[0]
        item["branch"] = item.pop("name").removeprefix("Easy Cash ").removeprefix("Easycash ")
        # Overseas stores have "DOM" as their region
        if item.get("state") == "DOM":
            item["state"] = None
            item["country"] = OVERSEAS_COUNTRIES.get(item.get("postcode", "")[:3], "FR")
        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
