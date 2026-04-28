from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class BurgerKingUYSpider(Spider):
    name = "burger_king_uy"
    item_attributes = {"brand": "Burger King", "brand_wikidata": "Q177054"}
    start_urls = ["https://www.burgerking.com.uy/restaurantes/"]

    def parse(self, response):
        for location in response.xpath("//div[@data-lat]"):
            raw_name = location.xpath(".//h5/text()").get("").strip()

            item = {
                # ref: name used because site lacks IDs and contains overlapping lat/lon pairs
                "ref": f"{raw_name}",
                "branch": raw_name.replace("SHOPP.", "").strip(),
                "lat": location.attrib.get("data-lat"),
                "lon": location.attrib.get("data-lon"),
                "addr_full": location.xpath('.//div[@class="title-rest"]/p/text()').get().strip(),
                "phone": location.xpath('.//div[contains(@class, "phone-rest")]//text()').getall()[1].strip(),
            }

            apply_category(Categories.FAST_FOOD, item)

            yield Feature(**item)
