import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class TapeALOeilSpider(SitemapSpider, StructuredDataSpider):
    name = "tape_a_l_oeil"
    item_attributes = {"brand": "Tape à l'Œil", "brand_wikidata": "Q30749175"}
    allowed_domains = ["www.taokids.com"]
    sitemap_urls = ["https://www.taokids.com/sitemap-fr-sitemap-mag.xml"]
    sitemap_rules = [(r"/magasins/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["ClothingStore"]
    search_for_twitter = False
    search_for_facebook = False
    # Closed stores redirect to the country listing
    custom_settings = {"REDIRECT_ENABLED": False}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url.split("/magasins/", 1)[1]
        item["branch"] = re.sub(r"\s+(ALGERIE|MAROC|NOUVELLE CALEDONIE)$", "", item.pop("name"))
        item.pop("image", None)
        # Stores in the overseas departments are given as FR
        if item.get("country") == "FR":
            item["country"] = OVERSEAS_COUNTRIES.get(str(item.get("postcode") or "")[:3], "FR")
        yield item
