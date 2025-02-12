from scrapy import Spider

from locations.items import Feature


class ZebrosZASpider(Spider):
    name = "zebros_za"
    item_attributes = {"brand": "Zebro's", "brand_wikidata": "Q116619443"}
    start_urls = ["https://www.zebros.co.za/store-locator/"]
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//div[@class="vc_tta-container"]/.//tbody/tr'):
            item = Feature()
            if location.xpath(".//td/text()") == []:
                continue
            item["branch"] = location.xpath(".//td/text()")[0].get()
            item["addr_full"] = location.xpath(".//td/text()")[1].get()
            item["phone"] = location.xpath('.//td/a[contains(@href, "tel:")]/@href').get()
            yield item
