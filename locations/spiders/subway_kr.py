import chompjs
import scrapy
from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.subway import SubwaySpider


class Subwaykrpider(scrapy.Spider):
    name = "subway_kr"
    item_attributes = SubwaySpider.item_attributes
    link_extractor = LinkExtractor(allow="/storeDetail?")

    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield Request("https://www.subway.co.kr/storeSearch?page=1", meta={"page": 1})

    def parse(self, response: Response, **kwargs):
        links = self.link_extractor.extract_links(response)
        if len(links) == 0:
            return
        else:
            next_page = response.meta["page"] + 1
            yield Request(f"https://www.subway.co.kr/storeSearch?page={next_page}", meta={"page": next_page})

            for link in links:
                yield Request(link.url, callback=self.parse_store)

    def parse_store(self, response, **kwargs):
        data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var storeInfo")]/text()').re_first(r"var storeInfo = (\{.*\});")
        )
        data.update(data.pop("franchiseDetail"))
        item = DictParser.parse(data)
        item["name"] = data.get("storNm")
        item["addr_full"] = merge_address_lines([data.get("storAddr1"), data.get("storAddr2")])
        item["phone"] = data.get("storTel")
        item["ref"] = item["website"] = response.url
        yield item
