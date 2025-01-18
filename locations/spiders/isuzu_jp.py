import re
from typing import Iterable

from unidecode import unidecode

from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature


ISUZU_SHARED_ATTRIBUTES = {"brand": "Isuzu", "brand_wikidata": "Q29803"}


class IsuzuJPSpider(CrawlSpider):
    name = "isuzu_jp"
    item_attributes = ISUZU_SHARED_ATTRIBUTES
    allowed_domains = ["sasp.mapion.co.jp"]
    start_urls = ["https://sasp.mapion.co.jp/b/isuzu_shop/attr/?t=attr_con&x=63&y=18"]
    rules = [Rule(LinkExtractor(allow=r"\/b\/isuzu_shop\/attr\/\?start=\d+", restrict_xpaths='//a[@id="m_nextpage_link"]'), callback="parse", follow=True)]

    def parse(self, response: Response) -> Iterable[Request]:
        for dealer in response.xpath('//tr[@class="MapiInfoGenre"]'):
            properties = {
                "ref": dealer.xpath('./td[2]/a/@href').get().split("/")[-2],
                "name": dealer.xpath('./td[2]/a/text()').get(),
                "lat": dealer.xpath('./td[1]/a/@href').get().split("/isuzu_shop/", 1)[1].split("_", 1)[0],
                "lon": dealer.xpath('./td[1]/a/@href').get().split("/isuzu_shop/", 1)[1].split("_", 1)[1].split("_", 1)[0],
                "addr_full": dealer.xpath('./td[3]/text()').get(),
                "website": "https://" + self.allowed_domains[0] + dealer.xpath('./td[2]/a/@href').get(),
            }
            apply_category(Categories.SHOP_TRUCK, properties)
            yield Request(url=properties["website"], meta={"properties": properties}, callback=self.parse_phone_number)

    def parse_phone_number(self, response: Response) -> Iterable[Feature]:
        properties = response.meta["properties"]

        # The first phone number like number listed should be the location's
        # primary phone number and not it's fax number, or separate number for
        # a service department adjoining the primary sales department.
        extra_data = unidecode(" ".join(response.xpath('//ul[@class="MapiInfoShopData"]/li/text()').getall()))
        if m := re.search(r"\W(\d{2,4}-\d{2,4}-\d{2,4})\W", extra_data):
            properties["phone"] = m.group(1)

        yield Feature(**properties)

