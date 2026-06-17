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
                allow=r"https://www\.aohostels\.com/en/[^/]+/[^/]+/$",
                deny=[
                    r"/conferences/",
                    r"/youth-hostel/",
                    r"/test/",
                    r"/newsletter/",
                    r"/press/",
                    r"/service/",
                    r"/services/",
                    r"/infos/",
                    r"/about-ao/",
                    r"/career/",
                    r"/business/",
                    r"/backpacker/",
                ],
            ),
            callback="parse_sd",
        )
    ]
    wanted_types = ["Hostel"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
