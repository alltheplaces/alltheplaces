from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations import google_url
from locations.structured_data_spider import StructuredDataSpider


class WrenKitchensGBSpider(CrawlSpider, StructuredDataSpider):
    name = "wren_kitchens_gb"
    item_attributes = {
        "brand": "Wren Kitchens",
        "brand_wikidata": "Q8037744",
        "country": "GB",
    }
    allowed_domains = ["wrenkitchens.com"]
    start_urls = ["https://www.wrenkitchens.com/showrooms/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https:\/\/www\.wrenkitchens\.com\/showrooms\/([-\w]+)$"),
            callback="parse_sd",
            follow=False,
        )
    ]
    download_delay = 0.5
    wanted_types = ["HomeAndConstructionBusiness"]

    def post_process_item(self, item, response, ld_data):
        google_url.extract_google_position(item, response)
        item["website"] = response.url  # Some URLs redirect
        yield item
