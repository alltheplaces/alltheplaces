import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT", "980": "MC", "988": "NC"}


class AdaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ada_fr"
    item_attributes = {"brand": "ADA", "brand_wikidata": "Q57313774"}
    allowed_domains = ["www.ada.fr"]
    sitemap_urls = ["https://www.ada.fr/sitemap.xml"]
    sitemap_rules = [(r"/location-voiture-[^/]+$", "parse_sd")]
    wanted_types = ["AutoRental"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # Many towns have their own page for a nearby agency. The agency record on the page
        # has its own id and the id of the agency that serves it (pdv). Only keep the page
        # of the agency itself, so each agency appears once.
        agency = re.search(r'"agency":\{"id":"(\w+)","name":"[^"]*","pdv":"(\w+)"', response.text.replace('\\"', '"'))
        if agency is None or agency.group(1) != agency.group(2):
            return
        if "TEST" in item["name"].upper():
            return

        item["ref"] = agency.group(1)
        item["branch"] = item.pop("name")
        item.pop("image", None)
        # addressRegion is always "fr"
        item.pop("state", None)
        item["country"] = OVERSEAS_COUNTRIES.get((item.get("postcode") or "")[:3], "FR")
        yield item
