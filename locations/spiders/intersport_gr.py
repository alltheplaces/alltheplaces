import json
from typing import Any

from scrapy.http import Response

from locations.linked_data_parser import LinkedDataParser
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class IntersportGRSpider(PlaywrightSpider):
    name = "intersport_gr"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://www.intersport.gr/el/etairia/katastimata/"]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[@data-control="box"]'):
            item = LinkedDataParser.parse_ld(
                json.loads(store.xpath('.//script[@type="application/ld+json"]/text()').get())
            )
            item["lat"] = store.xpath(".//@data-latitude").get()
            item["lon"] = store.xpath(".//@data-longitude").get()
            item["ref"] = item["website"] = response.urljoin(
                store.xpath('.//a[contains(text(),"Περισσότερα")]/@href').get()
            )
            item["branch"] = store.xpath('.//li[@class="name"]/text()').get()
            yield item
