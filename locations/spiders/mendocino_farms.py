from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MendocinoFarmsSpider(CrawlSpider, StructuredDataSpider):
    name = "mendocino_farms"
    item_attributes = {"brand": "Mendocino Farms", "brand_wikidata": "Q110671982"}
    start_urls = ["https://www.mendocinofarms.com/locations"]
    allowed_domains = ["www.mendocinofarms.com"]
    rules = [Rule(LinkExtractor(allow=(r"/locations/[\w-]+$",)), callback="parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    # The site lists both LocalBusiness and Restaurant. Both of these are accepded by StructuredDataSpider by default, so only allowing one removes duplicates.
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data):
        item["branch"] = item.pop("name")
        item["website"] = item["ref"]
        yield item
