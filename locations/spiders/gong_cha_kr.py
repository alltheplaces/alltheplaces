from typing import Any

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.gong_cha import GongChaSpider


class GongChaKRSpider(Spider):
    name = "gong_cha_kr"
    item_attributes = GongChaSpider.item_attributes
    start_urls = ["https://www.gong-cha.co.kr/brand/store/list?page=1"]

    def parse(self, response: Response, page: int = 1, **kwargs: Any) -> Any:
        seqs = response.xpath('//div[@class="table-wrap"]//a/@data-seq').getall()
        if not seqs:
            return

        csrf_name = response.xpath('//meta[@name="_csrf_header"]/@content').get()
        csrf_token = response.xpath('//meta[@name="_csrf"]/@content').get()
        for seq in seqs:
            yield FormRequest(
                "https://www.gong-cha.co.kr/brand/store/store_detail",
                formdata={"seq": seq, csrf_name: csrf_token},
                callback=self.parse_store,
            )

        yield Request(
            f"https://www.gong-cha.co.kr/brand/store/list?page={page + 1}",
            cb_kwargs={"page": page + 1},
        )

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        store = response.json()["data"]

        item = Feature()
        item["ref"] = store["seq"]
        item["branch"] = store["title"]
        item["addr_full"] = store["addr"]
        item["state"] = store["sido"]
        item["lat"] = store["lat"]
        item["lon"] = store["lng"]
        if store["tel"] != "-":
            item["phone"] = store["tel"]

        conveniences = (store.get("convenience") or "").split(",")
        apply_yes_no(Extras.TOILETS, item, "20" in conveniences)
        apply_yes_no(Extras.WIFI, item, "40" in conveniences)

        # TODO: parse store["time"] (opening hours) and store["holiday"] once the
        # Korean-language formats are handled reliably.

        apply_category(Categories.CAFE, item)
        yield item
