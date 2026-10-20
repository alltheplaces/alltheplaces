import re
from typing import Iterable
from urllib.parse import parse_qs

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class YhaCNSpider(Spider):
    name = "yha_cn"
    item_attributes = {"brand": "YHA China"}
    start_urls = ["https://www.yhachina.com/en-web-topic-view-id-108"]
    allowed_domains = ["www.yhachina.com"]
    # The site returns HTTP 400 if hit with the default concurrency, so throttle requests.
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_DELAY": 1}

    def parse(self, response: Response) -> Iterable[Feature]:
        # A handful of rows link out to Hong Kong hostels on the separate yha.org.hk site; skip them.
        for href in response.xpath('//table[@class="ptable"]//a[contains(@href, "hostel-detail-id")]/@href').getall():
            yield response.follow(href, callback=self.parse_hostel)

    def parse_hostel(self, response: Response) -> Iterable[Feature]:
        name = response.xpath("//h2/text()").get("").strip()
        if not name:
            # A handful of listings on the site have no name/address populated at source.
            return

        item = Feature()
        item["ref"] = re.search(r"id-(\d+)", response.url).group(1)
        item["name"] = name
        item["website"] = response.url

        map_href = response.xpath('//a[contains(@href, "map.qq.com")]/@href').get()
        if map_href and "?" in map_href:
            # Addresses can contain a literal "#" (e.g. house numbers like "825#"), which
            # urlparse would wrongly treat as a fragment separator, truncating the query string.
            params = parse_qs(map_href.split("?", 1)[1])
            if addr := params.get("addr"):
                item["addr_full"] = addr[0].strip()
            if (lon := params.get("pointx")) and (lat := params.get("pointy")):
                item["lon"] = lon[0]
                item["lat"] = lat[0]

        contact = " ".join(response.xpath('//span[@id="hutia"]//text()').getall())
        if m := re.search(r"Tel[：:]\s*([+\d()\-/\s]+?)\s*(?:Email|$)", contact):
            item["phone"] = m.group(1).strip()
        if m := re.search(r"Email[：:]\s*(\S+@\S+)", contact):
            item["email"] = m.group(1).strip()

        apply_category(Categories.TOURISM_HOSTEL, item)

        yield item
