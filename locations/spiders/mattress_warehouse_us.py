import re
from typing import Any

from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature


class MattressWarehouseUSSpider(CrawlSpider):
    name = "mattress_warehouse_us"
    BRANDS = {
        "mattress_warehouse": {"brand": "Mattress Warehouse", "brand_wikidata": "Q61995079"},
        "sleep_outfitters": {"brand": "Sleep Outfitters", "brand_wikidata": "Q120509459"},
    }
    start_urls = ["https://mattresswarehouse.com/store-locator"]

    rules = [
        Rule(LinkExtractor(allow=r"/store-locator/[a-z]+$")),
        Rule(
            LinkExtractor(allow=r"/store-locator/mattress-stores-in"),
            callback="parse",
            follow=True,
        ),
    ]

    store_link_extractor = LinkExtractor(allow=r"/store-locator/(sleep-outfitters-of-|mattress-warehouse-of-)")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        lat_lon_data = re.findall(
            r"(\d+\.\d+),.*?(-?\d+\.\d+)", response.xpath('//*[contains(text(),"loaderData")]/text()').get(default="")
        )
        links = self.store_link_extractor.extract_links(response)
        for link in links:
            for lat_lon in lat_lon_data:
                yield Request(url=link.url, callback=self.parse_details, cb_kwargs={"lat_lon": lat_lon})

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/div[2]/text()").get()
        item["addr_full"] = response.xpath('//*[@class="flex items-center gap-3"]//text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        item["lat"], item["lon"] = kwargs.get("lat_lon", (None, None))
        if "sleep-outfitters" in response.url:
            item.update(self.BRANDS["sleep_outfitters"])

        else:
            item.update(self.BRANDS["mattress_warehouse"])
        yield item
