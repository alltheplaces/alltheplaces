from locations.categories import Categories
from locations.storefinders.lighthouse import LighthouseSpider


class KafkasGRSpider(LighthouseSpider):
    name = "kafkas_gr"
    item_attributes = {"brand": "Kafkas", "brand_wikidata": "Q68201770", "extras": Categories.SHOP_ELECTRONICS.value}
    start_urls = ["https://www.kafkas.gr/about-us/katastimata/"]

    def parse_item(self, item, location):
        item["ref"] = item["lat"]

        item["name"] = location.xpath("div/*[contains(@class, 'name')]/text()").get()
        item["street"] = location.xpath("div/div/ul/li/span[contains(@class, 'address')]/text()").get()

        city = location.xpath("div/div/ul/li/span[contains(@class, 'city')]/text()").get()
        if city:
            item["city"] = city.split(", ")[1]

        postal = location.xpath("div/div/ul/li/span[contains(@class, 'postal-code')]/text()").get()
        if postal:
            item["postcode"] = postal.split(", ")[1]

        item["street_address"] = None

        item["phone"] = location.xpath("div/div/ul/li[contains(@class, 'phone')]/a/text()").get()
        item["email"] = location.xpath("div/div/ul/li[contains(@class, 'email')]/a/text()").get()

        yield item
