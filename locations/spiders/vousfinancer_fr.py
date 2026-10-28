from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class VousfinancerFRSpider(SitemapSpider, StructuredDataSpider):
    name = "vousfinancer_fr"
    item_attributes = {"brand": "Vousfinancer", "brand_wikidata": "Q114185120"}
    allowed_domains = ["courtier.vousfinancer.com"]
    sitemap_urls = ["https://courtier.vousfinancer.com/sitemap.xml"]
    sitemap_rules = [(r"/courtier-en-credit-a-[^/]+-\d+$", "parse_sd")]
    wanted_types = ["FinancialService"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url.split("-")[-1]
        item["branch"] = item.pop("name").removeprefix("Courtier en crédit à ").split(" (")[0]
        # NSI only covers mainland France, so set these for the overseas agencies too
        item["name"] = "Vousfinancer"
        apply_category(Categories.OFFICE_FINANCIAL, item)
        if item.get("facebook") == "https://www.facebook.com/Vousfinancer/":
            item["facebook"] = None
        yield item
