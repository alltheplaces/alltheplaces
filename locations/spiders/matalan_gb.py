import json

from scrapy.spiders import SitemapSpider

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class MatalanGBSpider(SitemapSpider, StructuredDataSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    allowed_domains = ["www.matalan.co.uk"]
    sitemap_urls = ["https://www.matalan.co.uk/robots.txt"]
    sitemap_rules = [(r"/stores/uk/[^/]+/[^/]+/[^/]+$", "parse_sd")]
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
