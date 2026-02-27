import re
from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class BrodernasSESpider(Spider):
    name = "brodernas_se"
    item_attributes = {
        "brand": "Brödernas",
        "brand_wikidata": "Q136644088",
        "country": "SE",
    }
    allowed_domains = ["brodernas.nu"]
    start_urls = ["https://www.brodernas.nu/restauranger"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for header in response.xpath('//header[contains(@class, "open-time-wrapper")]'):
            list_item = header.xpath('ancestor::div[contains(@class, "w-dyn-item")][1]')
            wrap = list_item.xpath('.//div[contains(@class, "restaurant-item-title-wrapper")]')
            if not wrap:
                continue
            wrap = wrap[0]

            name = wrap.xpath(
                './/h2[contains(@class, "restaurants") and not(contains(@class, "merinfo"))]/text()'
            ).get()
            if not name:
                continue
            name = name.strip()

            store_id = header.xpath("./@id").get()
            item = Feature()
            item["ref"] = store_id or self._slug(name)
            item["name"] = name

            link = wrap.xpath('.//a[.//h2[contains(@class, "restaurants")]]/@href').get()
            if link:
                item["website"] = response.urljoin(link)
            else:
                item["website"] = self.start_urls[0]

            addr_text = wrap.xpath(
                './/div[contains(@class, "paragraph--14") and contains(@class, "restaurants")]/text()'
            ).get()
            if addr_text:
                addr_text = addr_text.strip()
                if " | " in addr_text:
                    addr_part, email_part = addr_text.split(" | ", 1)
                    item["addr_full"] = addr_part.strip()
                    item["email"] = email_part.strip()
                else:
                    item["addr_full"] = addr_text
                if item.get("addr_full"):
                    street_match = re.match(
                        r"^(.+?),?\s*(\d{3}\s*\d{2})\s+(.+)$", item["addr_full"]
                    )
                    if street_match:
                        item["street_address"] = street_match.group(1).strip()
                        item["postcode"] = re.sub(
                            r"\s+", " ", street_match.group(2).strip()
                        )
                        item["city"] = street_match.group(3).strip()

            phone = wrap.xpath('.//a[starts-with(@href, "tel:")]/text()').get()
            if phone:
                item["phone"] = phone.strip()

            apply_category(Categories.FAST_FOOD, item)

            if link:
                yield Request(
                    url=item["website"],
                    callback=self.parse_store,
                    meta={"item": item},
                )
            else:
                yield item

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = response.meta["item"]
        extract_google_position(item, response)
        yield item

    @staticmethod
    def _slug(name: str) -> str:
        return re.sub(
            r"[^a-z0-9]+",
            "-",
            name.lower()
            .replace("å", "a")
            .replace("ä", "a")
            .replace("ö", "o"),
        ).strip("-")