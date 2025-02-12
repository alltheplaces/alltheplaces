from locations.categories import Categories, apply_category
from locations.storefinders.lighthouse import LighthouseSpider


class KafkasGRSpider(LighthouseSpider):
    name = "kafkas_gr"
    item_attributes = {"brand_wikidata": "Q68201770"}
    start_urls = ["https://www.kafkas.gr/about-us/katastimata/"]

    def parse_item(self, item, location):
        item["ref"] = item["lat"]

        item["branch"] = item.pop("name")
        item["street_address"] = location.xpath('./div/div/ul/li/span[contains(@class, "address")]/text()').get()

        if city := location.xpath('./div/div/ul/li/span[contains(@class, "city")]/text()').get(""):
            item["city"] = city.split(", ")[1].strip()

        if postcode := location.xpath('./div/div/ul/li/span[contains(@class, "postal-code")]/text()').get(""):
            item["postcode"] = postcode.split(", ")[1].strip()

        item["street_address"] = None

        item["phone"] = location.xpath("div/div/ul/li[contains(@class, 'phone')]/a/text()").get()
        item["email"] = location.xpath("div/div/ul/li[contains(@class, 'email')]/a/text()").get()

        apply_category(Categories.SHOP_ELECTRONICS, item)

        yield item
