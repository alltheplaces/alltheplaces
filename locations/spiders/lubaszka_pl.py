from scrapy import Spider

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class LubaszkaPLSpider(Spider):
    name = "lubaszka_pl"
    item_attributes = {"brand": "Galeria Wypieków Lubaszka", "brand_wikidata": "Q108586693"}
    start_urls = ["https://www.lubaszka.pl/sklepy"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # robots.txt causes 404 redirect loop

    def parse(self, response, **kwargs):
        for shop_id in response.xpath("//div[contains(@id, 'address_')]/@id").getall():
            street_address = (
                response.xpath(f"//div[@id='{shop_id}']/div[@class='row']/div[1]/text()").getall()[0].strip()
            )
            post_code_city = (
                response.xpath(f"//div[@id='{shop_id}']/div[@class='row']/div[1]/text()").getall()[1].strip()
            )
            post_code = post_code_city.split(" ")[0]
            city = " ".join(post_code_city.split(" ")[1:])
            phone = response.xpath(f"//div[@id='{shop_id}']/div[@class='row']/div[2]/text()").getall()[1].strip()
            opening_hours = OpeningHours()
            for opening_hours_line in response.xpath(f"//div[@id='{shop_id}']/p[2]/text()").getall()[1:]:
                opening_hours.add_ranges_from_string(opening_hours_line.strip(), days=DAYS_PL)
            properties = {
                "ref": shop_id.removeprefix("address_"),
                "street_address": street_address,
                "postcode": post_code,
                "city": city,
                "phone": phone,
                "opening_hours": opening_hours,
            }
            location_link = response.xpath(f"//div[@id='{shop_id}']/p/a/@href").get()
            if "/@" in location_link:
                coordinates = location_link.split("/@")[1].split(",")
                properties["lat"] = coordinates[0]
                properties["lon"] = coordinates[1]
            feature = Feature(**properties)
            yield feature
