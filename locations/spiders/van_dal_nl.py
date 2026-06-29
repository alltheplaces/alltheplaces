from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class VanDalNLSpider(CrawlSpider, StructuredDataSpider):
    name = "van_dal_nl"
    item_attributes = {"brand": "Van Dal", "brand_wikidata": "Q125580449"}
    start_urls = ["https://www.vdal.nl/winkels/"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"/tabletop/store-locator/detail/\w+$",
            ),
            callback="parse_sd",
        ),
    ]
    json_parser = "chompjs"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Van Dal ")
        item["website"] = response.url

        yield item
