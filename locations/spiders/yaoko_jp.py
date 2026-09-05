import re

from scrapy import Spider
from scrapy.http import Request, Response

from locations.items import Feature


class YaokoJPSpider(Spider):
    """Extract Yaoko (JP) store details from the official main website.

    ``start_requests`` fetches the single store-list page, extracts every store
    detail URL, and issues one request per store. A single ``parse`` then fills
    the whole item from each detail page (which carries all available data).
    """

    name = "yaoko_jp"
    item_attributes = {
        "brand": "ヤオコー",
        "brand_wikidata": "Q11344967",
    }

    list_url = "https://www.yaoko-net.com/store/"

    async def start(self):
        yield Request(self.list_url, callback=self.parse_list)

    def parse_list(self, response: Response):
        seen: set[str] = set()
        for url in response.xpath("//a[contains(@href, '/store/store')]/@href").getall():
            url = response.urljoin(url)
            if url in seen:
                continue
            seen.add(url)
            yield Request(url, callback=self.parse)

    def parse(self, response: Response):
        rows = response.xpath("//table[contains(@class, 'store_info_table')]//tr")
        info = {
            label: value
            for tr in rows
            if (label := tr.xpath("./th/text()").get(""))
            for value in [tr.xpath("string(./td)").get("")]
        }

        item = Feature()
        item["ref"] = response.url.rstrip("/").split("/")[-1].replace(".html", "")
        item["name"] = re.sub(r"（.*?）$", "", response.xpath("//h1/text()").get("")).strip()
        item["website"] = response.url
        item["country"] = "JP"

        addr_lines = [line.strip() for line in info.get("住所", "").split("\n") if line.strip()]
        item["addr_full"] = "\n".join(addr_lines)
        postcode = re.search(r"〒\s*([0-9\-]+)", info.get("住所", ""))
        if postcode:
            item["postcode"] = postcode.group(1)
        item["phone"] = info.get("電話番号", "").strip()
        item["opening_hours"] = info.get("営業時間", "").strip()

        yield item
