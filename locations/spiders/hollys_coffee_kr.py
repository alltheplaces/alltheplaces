import re

import scrapy

from locations.items import Feature


class HollysCoffeeKRSpider(scrapy.Spider):
    name = "hollys_coffee_kr"
    item_attributes = {"brand_wikidata": "Q12624386"}
    start_urls = ["https://www.hollys.co.kr/store/korea/korStore.do"]

    def parse(self, response, **kwargs):
        current_page = kwargs.get("current_page", 1)
        if branch_ids := response.xpath("//td/a/@onclick").getall():
            for branch_id in set(branch_ids):
                if match := re.search(r"storeView\((\d+)\)", branch_id):
                    b_id = match.group(1)
                    yield scrapy.Request(
                        url=f"https://www.hollys.co.kr/store/korea/korStoreDetail.do?pageNo={current_page}&branchId={b_id}&sido=&gugun=&store=&internet=&smoking=&terrace=&location=&fname=&summerIt=&allday=",
                        callback=self.parse_store,
                    )

            yield scrapy.Request(
                url=f"https://www.hollys.co.kr/store/korea/korStore.do?pageNo={current_page + 1}&sido=&gugun=&store=",
                cb_kwargs=dict(current_page=current_page + 1),
            )

    def parse_store(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//*[@class='store_name']/text()").get()
        item["addr_full"] = response.xpath(
            "//*[text()='주소']/following-sibling::*[contains(@class, 'center_t')]/text()"
        ).get()
        item["phone"] = response.xpath(
            "//*[text()='전화번호']/following-sibling::*[contains(@class, 'center_t')]/text()"
        ).get()
        item["website"] = item["ref"] = response.url
        if match := re.search(r"LatLng\(([\d.-]+)\s*,\s*([\d.-]+)\)", response.text):
            item["lat"], item["lon"] = match.groups()
        yield item
