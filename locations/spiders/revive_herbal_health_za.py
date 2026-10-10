from urllib.parse import unquote

from scrapy import Spider

from locations.items import Feature


class ReviveHerbalHealthZASpider(Spider):
    name = "revive_herbal_health_za"
    item_attributes = {
        "brand_wikidata": "Q116498098",
        "brand": "Revive Herbal Health",
    }
    allowed_domains = [
        "reviveherbalhealth.co.za",
    ]
    start_urls = ["https://reviveherbalhealth.co.za/store-locator/"]

    def parse(self, response):
        phone_links = response.xpath('//a[starts-with(@href, "tel:")]')

        for phone in phone_links:
            store = phone.xpath('ancestor::*[.//h2[contains(@class, "elementor-heading-title")]][1]')

            if not store:
                continue

            location = self.clean(store.xpath('.//h2[contains(@class, "elementor-heading-title")]/text()').get())

            text_values = [
                text
                for text in map(
                    self.clean,
                    store.xpath('.//div[contains(@class, "elementor-widget-text-editor")]//p//text()').getall(),
                )
                if text
            ]

            if not text_values:
                continue
            item = Feature()
            item["city"] = location
            item["branch"] = text_values[0]
            item["addr_full"] = item["ref"] = text_values[-1]
            item["phone"] = unquote(phone.attrib.get("href", "").removeprefix("tel:")).strip()

            yield item

    @staticmethod
    def clean(value):
        return " ".join(value.split()) if value else ""
