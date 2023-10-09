from scrapy import Spider

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class LubaszkaPLSpider(Spider):
    name = "lubaszka_pl"
    item_attributes = {"brand": "Galeria Wypieków Lubaszka", "brand_wikidata": "Q108586693"}
    start_urls = ["https://www.lubaszka.pl/sklepy"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # robots.txt causes 404 redirect loop

    def parse(self, response, **kwargs):
        for shopId in response.xpath("//div[contains(@id, 'address_')]/@id").getall():
            streetAddress = response.xpath(f"//div[@id='{shopId}']/div[@class='row']/div[1]/text()").getall()[0].strip()
            postCodeCity = response.xpath(f"//div[@id='{shopId}']/div[@class='row']/div[1]/text()").getall()[1].strip()
            postCode = postCodeCity.split(" ")[0]
            city = " ".join(postCodeCity.split(" ")[1:])
            phone = response.xpath(f"//div[@id='{shopId}']/div[@class='row']/div[2]/text()").getall()[1].strip()
            openingHours = OpeningHours()
            for openingHoursLine in response.xpath(f"//div[@id='{shopId}']/p[2]/text()").getall()[1:]:
                openingHours.add_ranges_from_string(openingHoursLine.strip(), days=DAYS_PL)
            properties = {
                "ref": shopId.removeprefix("address_"),
                "street_address": streetAddress,
                "postcode": postCode,
                "city": city,
                "phone": phone,
                "opening_hours": openingHours,
            }
            locationLink = response.xpath(f"//div[@id='{shopId}']/p/a/@href").get()
            if "/@" in locationLink:
                coordinates = locationLink.split("/@")[1].split(",")
                properties["lat"] = coordinates[0]
                properties["lon"] = coordinates[1]
            feature = Feature(**properties)
            yield feature
