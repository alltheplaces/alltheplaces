import re

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class TjoyJPSpider(Spider):
    name = "tjoy_jp"
    item_attributes = {"brand": "T・ジョイ", "brand_wikidata": "Q11319016"}
    start_urls = ["https://tjoy.jp/"]

    def parse(self, response):
        for theater in response.xpath('//div[contains(@class,"theater-list")]//a[contains(@href,"tjoy.jp/")]'):
            url = theater.xpath("./@href").get().strip()
            slug = url.rstrip("/").rsplit("/", 1)[-1]
            name = " ".join(theater.xpath("./text()[normalize-space()]").getall())
            yield Request(
                url=f"https://tjoy.jp/{slug}/access",
                callback=self.parse_access,
                cb_kwargs={"ref": slug, "name": name},
            )

    def parse_access(self, response, ref, name):
        addr = " ".join(response.xpath('//dt[contains(text(),"住所")]/following-sibling::dd[1]//text()').getall())
        addr = " ".join(addr.split())
        postcode = None
        if m := re.match(r"〒\s*(\d{3}-?\d{4})\s*(.*)", addr):
            postcode = m.group(1)
            addr = m.group(2).strip()

        phone_node = " ".join(
            response.xpath('//dt[contains(text(),"電話")]/following-sibling::dd[1]//text()[normalize-space()]').getall()
        ).strip()
        phone = None
        if m := re.search(r"\d{2,4}-\d{2,4}-\d{4}", phone_node):
            phone = m.group(0)

        item = Feature()
        item["ref"] = ref
        item["name"] = "T・ジョイ"
        item["branch"] = name
        item["addr_full"] = addr
        item["postcode"] = postcode
        item["phone"] = phone
        item["country"] = "JP"
        item["website"] = f"https://tjoy.jp/{ref}"

        extract_google_position(item, response)

        apply_category(Categories.CINEMA, item)

        yield item
