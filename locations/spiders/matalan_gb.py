import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class MatalanGBSpider(CrawlSpider, StructuredDataSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    allowed_domains = ["www.matalan.co.uk"]
    start_urls = ["https://www.matalan.co.uk/stores/uk"]
    rules = [
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/stores/uk/[^/]+$")),
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/stores/uk/[^/]+/[^/]+$"), "parse_sd", follow=True),
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/store/[^/]+/[^/]+$"), "parse_sd"),
    ]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["phone"] = None
        item["website"] = response.url

        if item["name"].startswith("CLOSED "):
            set_closed(item)

        item["branch"] = item.pop("name").split(" - ", 1)[1]

        storedata = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        store = json.loads(storedata)["props"]["pageProps"]["store"]
        item["lat"] = store["latitude"]
        item["lon"] = store["longitude"]
        yield item
