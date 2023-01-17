from scrapy import Selector, Spider

from locations.items import Feature


class TelenorDKSpider(Spider):
    name = "telenor_dk"
    item_attributes = {"brand": "Telenor", "brand_wikidata": "Q845632"}
    start_urls = [
        "https://www.telenor.dk/da/custom/FindNearestShopBlock/GetShops/2bd5f376-3f79-475b-aa1e-b45174b9a2f3/?blockId=1590"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def parse(self, response):
        for store in response.json():
            item = Feature()

            item["lon"] = store["longitude"]
            item["lat"] = store["latitude"]
            item["name"] = store["title"]
            item["extras"]["type"] = store["type"]

            html = Selector(text=store["html"])

            address = html.xpath(
                '//div[@class="border--bottom padding-trailer"]/div[@class="margin-trailer--small"][1]/p/text()'
            ).getall()
            item["addr_full"] = ", ".join(address)
            item["street_address"] = address[0]
            item["postcode"], item["city"] = address[1].split(" ", maxsplit=1)

            item["phone"] = html.xpath('//p[contains(text(), "Telefon:")]/text()').get().replace("Telefon:", "")
            if slug := html.xpath('//a[contains(@href, "find-butik")]/@href').get():
                item["ref"] = slug
                item["website"] = f"https://www.telenor.dk{slug}"
            if email := html.xpath('//p[contains(text(), "@telenor.dk")]/text()').get():
                item["email"] = email.strip()

            yield item
