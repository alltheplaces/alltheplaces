import json
import re
from urllib.parse import unquote

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DominosPizzaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dominos_pizza_us"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.com"]
    sitemap_urls = ["https://pizza.dominos.com/robots.txt"]
    sitemap_rules = [(r"com/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["FoodEstablishment"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if response.url == "https://pizza.dominos.com/new-york/new-york/61-ninth-avenue":
            return  # "Test Location"

        item["image"] = None

        if m := re.search(r"decodeURIComponent\(\"(.+)\"\)", response.text):
            data = json.loads(unquote(m.group(1)))
            item["ref"] = str(data["document"]["id"])
            item["extras"]["ref:google"] = data["document"].get("googlePlaceId")
            item["lat"] = data["document"]["yextDisplayCoordinate"]["latitude"]
            item["lon"] = data["document"]["yextDisplayCoordinate"]["longitude"]

        yield item
