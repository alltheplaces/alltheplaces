import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su",
}


class LidlDESpider(scrapy.Spider):
    name = "lidl_de"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954", "country": "DE"}
    allowed_domains = ["lidl.de"]
    handle_httpstatus_list = [404]
    start_urls = ["https://www.lidl.de/f/"]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for item in hours:
            if item.split():
                try:
                    day = DAY_MAPPING[item.split()[0]]
                    hour = item.split()[1]
                    opening_hours.add_range(
                        day=day,
                        open_time=hour.split("-")[0],
                        close_time=hour.split("-")[1],
                    )
                except KeyError:
                    pass

        return opening_hours.as_opening_hours()

    def parse_details(self, response):

        lidlShops = response.css(".ret-o-store-detail")

        for shop in lidlShops:
            shopAddress = shop.css(".ret-o-store-detail__address::text").extract()
            street = shopAddress[0]
            postalCode = shopAddress[1].split()[0]
            city = shopAddress[1].split()[1]
            openingHours = shop.css(
                ".ret-o-store-detail__opening-hours::text"
            ).extract()
            services = response.css(".ret-o-store-detail__store-icon-wrapper")[0]
            link = services.css('a::attr("href")').get()
            coordinates = link.split("pos.")[1].split("_L")[0]
            latitude = coordinates.split("_")[0]
            longitude = coordinates.split("_")[1]

            properties = {
                "ref": latitude + longitude,
                "street_address": street,
                "postcode": postalCode,
                "city": city,
                "lat": latitude,
                "lon": longitude,
            }

            hours = self.parse_hours(openingHours)

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)

    def parse(self, response):

        cities = response.css(".ret-o-store-detail-city").css("a::attr(href)")

        for city in cities:
            city = f"https://www.lidl.de{city.get()}"

            yield scrapy.Request(url=city, callback=self.parse_details)
