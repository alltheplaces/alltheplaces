import json
from copy import deepcopy
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MitsubishiJPSpider(CrawlSpider):
    name = "mitsubishi_jp"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://map.mitsubishi-motors.co.jp/search/listHansha.do"]
    rules = [
        Rule(
            LinkExtractor(allow=r"search\.do\?hanshaCD=\d+&todofukenCD=\d+$"),
        ),
        Rule(LinkExtractor(allow=r"showKyoten\.do\?hanshaCD=\d+&kyotenCD=\d+&tenpoCD=\d+$"), callback="parse"),
    ]

    def build_sales_item(self, item):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-sales"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item):
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-service"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_info = json.loads(response.xpath('//*[@id="kyotenInfoId"]/text()').get(""))[0]
        item = Feature()
        item["ref"] = response.url.split("tenpoCD=")[1]
        item["website"] = response.url
        item["branch"] = location_info["kyotenName"]
        item["lat"] = location_info["kyotenIdo"]
        item["lon"] = location_info["kyotenKeido"]
        # location_info["kyoten_addr"] doesn't contain postcode
        item["addr_full"] = clean_address(
            response.xpath('//*[contains(text(),"住所")]/following-sibling::td/span/text()').getall()
        )
        item["phone"] = response.xpath('//*[contains(@class, "mod-link-tel")]//a/@href').get()
        item["extras"]["fax"] = response.xpath('//*[contains(@class, "mod-link-fax")]/text()').get()

        services = response.xpath('//*[@class="dealer__icon__txt"]/text()').getall()
        sales_available = "新車" in services or "中古車" in services
        service_available = "メンテナンス" in services

        if sales_available:
            sales_item = self.build_sales_item(item)
            apply_yes_no(Extras.CAR_REPAIR, sales_item, service_available)
            apply_yes_no(Extras.USED_CAR_SALES, sales_item, "中古車" in services)
            apply_yes_no(Extras.WIFI, sales_item, "WiFi" in services)
            yield sales_item

        if service_available:
            service_item = self.build_service_item(item)
            apply_yes_no(Extras.WIFI, service_item, "WiFi" in services)
            yield service_item

        if not sales_available and not service_available:
            self.logger.error(f"Unknown services: {services}, {item['branch']}, {item['ref']}")
            # Fallback yield for unknown cases
            apply_yes_no(Extras.WIFI, item, "WiFi" in services)
            yield item
