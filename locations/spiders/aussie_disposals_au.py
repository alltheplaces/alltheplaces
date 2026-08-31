from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.google_url import url_to_coords
from locations.items import Feature


class AussieDisposalsAUSpider(Spider):
    name = "aussie_disposals_au"
    item_attributes = {"brand": "Aussie Disposals", "brand_wikidata": "Q117847729"}
    start_urls = ["https://www.aussiedisposals.com.au/"]
    requires_proxy = "AU"
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.xpath('//*[@class="store-grid"]//*[@class="store-card"]'):
            item = Feature()
            item["branch"] = location.xpath('.//*[contains(@class,"store-badge")]/text()').get()
            item["addr_full"] = location.xpath('.//*[@class="store-details"]//span/text()').get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            item["lat"], item["lon"] = url_to_coords(location.xpath('.//*[@class="store-map"]/@src').get())
            yield item
