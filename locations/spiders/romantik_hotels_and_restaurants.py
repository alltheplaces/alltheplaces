from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class RomantikHotelsAndRestaurentsSpider(CrawlSpider, StructuredDataSpider):
    name = "romantik_hotels_and_restaurants"
    item_attributes = {"brand": "Romantik Hotels & Restaurants", "brand_wikidata": "Q126075497"}
    start_urls = ["https://www.romantikhotels.com/en/hotels/"]
    rules = [Rule(LinkExtractor(allow="/en/hotels/", restrict_xpaths='//*[@class="relative"]'), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Romantik ", "")
        extract_google_position(item, response)
        apply_category(Categories.HOTEL, item)
        yield item
