from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AoHostelsSpider(CrawlSpider, StructuredDataSpider):
    name = "ao_hostels"
    item_attributes = {"brand": "A&O", "brand_wikidata": "Q15890910"}
    start_urls = ["https://www.aohostels.com/en/all-locations/"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https://www\.aohostels\.com/en/[a-z-]+/[a-z-]+/$",
                deny=r"/en/(about-ao|career|conferences|facebook|google|infos|klarna|newsletter|press|service|services|test|youth-hostel)/",
            ),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["Hostel"]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # Derive branch from per-location name (e.g. "a&o Berlin Hauptbahnhof")
        item["branch"] = item.pop("name", None)

        # Use URL slug as a stable ref
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]

        # Set per-location website
        item["website"] = response.url

        apply_category(Categories.TOURISM_HOSTEL, item)

        yield item
