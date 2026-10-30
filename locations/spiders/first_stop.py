import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class FirstStopSpider(SitemapSpider, StructuredDataSpider):
    name = "first_stop"
    item_attributes = {"brand": "First Stop", "brand_wikidata": "Q3072965"}
    sitemap_urls = [
        "https://centres.firststop.fr/sitemap.xml",
        "https://centres.firststop.be/sitemap.xml",
        "https://talleres.firststop.es/sitemap.xml",
    ]
    sitemap_rules = [(r"/ps\d+/", "parse_sd")]
    wanted_types = ["TireShop"]
    time_format = "%H:%M:%S"
    search_for_facebook = False
    search_for_twitter = False
    search_for_amenity_features = False
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_DELAY": 2}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen = set()

    def pre_process_data(self, ld_data: dict, **kwargs):
        for key in ("latitude", "longitude"):
            ld_data["geo"][key] = ld_data["geo"][key].replace(",", ".")
        ld_data["openingHours"] = [rule for rule in ld_data.get("openingHours", []) if re.search(r"\d", rule)]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("First Stop ").removesuffix(" by First Stop")
        # Some centres are listed several times under different ids
        key = (item["branch"], item["lat"], item["lon"])
        if key in self.seen:
            return
        self.seen.add(key)

        item["ref"] = re.search(r"/(ps\d+)/", response.url).group(1).upper()
        item["website"] = response.url
        if item["country"] == "FR":
            item["country"] = OVERSEAS_COUNTRIES.get(item["postcode"][:3], "FR")
        yield item
