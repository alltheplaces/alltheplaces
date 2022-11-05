from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.linked_data_parser import LinkedDataParser


class JDSportsGBSpider(CrawlSpider):
    name = "jdsports_gb"
    item_attributes = {
        "brand": "JD Sports",
        "brand_wikidata": "Q6108019",
    }
    start_urls = ["https://www.jdsports.co.uk/store-locator/all-stores/"]
    rules = [
        Rule(
            LinkExtractor(allow="store-locator/"), callback="parse_store", follow=False
        )
    ]
    download_delay = 0.2

    def parse_store(self, response):
        if "-soon" in response.url:
            self.logger.warning("ignoring store opening soon %s", response.url)
        else:
            item = LinkedDataParser.parse(response, "Store")
            if item:
                item["ref"] = response.url.strip("/").split("/")[-1]
                yield item
