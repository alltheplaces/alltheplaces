from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StarHotelsSpider(CrawlSpider, StructuredDataSpider):
    name = "star_hotels"
    item_attributes = {"brand": "Starhotels", "brand_wikidata": "Q3968369"}
    start_urls = ["https://www.starhotels.com/en/our-hotels/"]
    rules = [Rule(LinkExtractor(allow=r"", restrict_xpaths='//*[@class="launches-hotels d-all"]'), callback="parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.HOTEL, item)
        yield item
