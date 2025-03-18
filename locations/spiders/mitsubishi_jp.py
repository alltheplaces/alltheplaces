import json
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

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

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_info = json.loads(response.xpath('//*[@id="kyotenInfoId"]/text()').get(""))[0]
        item = Feature()
        item["ref"] = response.url.split("tenpoCD=")[1]
        item["website"] = response.url
        item["name"] = location_info["kyotenName"]
        item["lat"] = location_info["kyotenIdo"]
        item["lon"] = location_info["kyotenKeido"]
        # location_info["kyoten_addr"] doesn't contain postcode
        item["addr_full"] = clean_address(
            response.xpath('//*[contains(text(),"住所")]/following-sibling::td/span/text()').getall()
        )
        yield item
