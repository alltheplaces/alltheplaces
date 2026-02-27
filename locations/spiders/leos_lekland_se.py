import re
from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position, url_to_coords
from locations.items import Feature


class LeosLeklandSESpider(Spider):
    name = "leos_lekland_se"
    item_attributes = {
        "brand": "Leo's Lekland",
        "brand_wikidata": "Q133225932",
        "country": "SE",
    }
    allowed_domains = ["leoslekland.se"]
    start_urls = ["https://www.leoslekland.se/lekland"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for card in response.xpath('//li[contains(@class, "Card_card")]'):
            name = card.xpath('.//a[contains(@class, "Card_titleLink")]/text()').get()
            href = card.xpath('.//a[contains(@class, "Card_titleLink")]/@href').get()
            addr = card.xpath('.//div[contains(@class, "Card_addressContainer")]//p/text()').get()
            if not name or not href:
                continue
            name = name.strip()
            item = Feature()
            item["ref"] = href.strip("/").split("/")[-1] or href.strip("/").replace("/", "-")
            item["name"] = name
            item["website"] = response.urljoin(href)
            if addr:
                item["addr_full"] = addr.strip()
                if m := re.match(r"^(.+?),?\s*(\d{3}\s*\d{2})\s+(.+)$", item["addr_full"]):
                    item["street_address"] = m.group(1).strip()
                    item["postcode"] = re.sub(r"\s+", " ", m.group(2).strip())
                    item["city"] = m.group(3).strip()
            apply_category(Categories.LEISURE_INDOOR_PLAY, item)
            yield Request(
                url=item["website"],
                callback=self.parse_store,
                meta={"item": item},
            )

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = response.meta["item"]
        extract_google_position(item, response)
        googl = response.xpath('.//a[contains(@href, "maps.app.goo.gl")]/@href').get()
        if googl and not item.get("lat") and not item.get("geometry"):
            yield Request(
                url=googl.strip(),
                callback=self.parse_map_redirect,
                meta={"item": item},
                dont_filter=True,
            )
            return
        yield item

    def parse_map_redirect(self, response: Response, **kwargs: Any) -> Any:
        item = response.meta["item"]
        lat, lon = url_to_coords(response.url)
        if lat is not None and lon is not None:
            item["lat"] = lat
            item["lon"] = lon
        yield item
