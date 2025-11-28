import re
from typing import Any
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DekraFRSpider(Spider):
    name = "dekra_fr"
    item_attributes = {"brand_wikidata": "Q383711"}
    start_urls = ["https://www.dekra-pl.com/scripts/franceMobile.js"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in re.findall(r"url: \"(/Rdv/Step1Nat/\d+)\"", response.text):
            yield Request(response.urljoin(link), self.parse_list)

    def parse_list(self, response: Response, **kwargs: Any) -> Any:
        for link in re.findall(r"viewcentre\('([^']+)'\)", response.text):
            yield Request(urljoin("https://www.dekra-pl.com/centre-detail/", link), self.parse_location)

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.removeprefix("https://www.dekra-pl.com/centre-detail/")
        item["branch"] = response.xpath('//div[@id="title_dekra"]/text()').get().removeprefix("DEKRA ")
        item["street_address"] = response.xpath(
            '//div[@class="centre-dekra centre-dekra-adresse address-container"]/div[2]/text()'
        ).get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//div[@class="maj"]/text()').get()]
        )
        item["website"] = response.url
        item["phone"] = response.xpath('//a[@class="liensTel"]/@href').get()

        if m := re.match(
            r"gotocentre\('(-?\d+\.\d+)','(-?\d+\.\d+)'\)",
            response.xpath('//button[contains(@onclick, "gotocentre")]/@onclick').get(default=""),
        ):
            item["lat"], item["lon"] = m.groups()

        yield item
