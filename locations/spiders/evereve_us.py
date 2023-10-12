from html import unescape

from scrapy import Request

from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class EVEREVEUSSpider(AmastyStoreLocatorSpider):
    name = "evereve_us"
    item_attributes = {"brand": "EVEREVE", "brand_wikidata": "Q69891997"}
    allowed_domains = ["evereve.com"]

    def start_requests(self):
        # The request won't work without the headers supplied below.
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }
        for domain in self.allowed_domains:
            yield Request(url=f"https://{domain}/amlocator/index/ajax/", method="POST", headers=headers)

    def parse_item(self, item, location, popup_html):
        if "COMING SOON" in item["name"].upper():
            return
        popup_text = list(
            filter(
                None,
                map(unescape, map(str.strip, popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall())),
            )
        )
        if len(popup_text) == 3:
            item["addr_full"] = ", ".join([popup_text[0], popup_text[1]])
            item["phone"] = popup_text[2]
        elif len(popup_text) == 2:
            item["addr_full"] = ", ".join([popup_text[0], popup_text[1]])
        yield item
