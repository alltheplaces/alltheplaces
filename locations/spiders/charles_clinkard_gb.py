import scrapy
import re

# from locations.hours import OpeningHours
from locations.items import Feature
from locations.categories import Categories, apply_category



class CharlesClinkardGBSpider(scrapy.Spider):
    name = "charles_clinkard_gb"
    item_attributes = {
        "brand": "Charles Clinkard",
        "extras": Categories.SHOP_SHOES.value,
    }
    allowed_domains = [
        "www.charlesclinkard.co.uk",
    ]
    start_urls = ("https://www.charlesclinkard.co.uk/map",)

    def parse(self, response):
        urls = response.xpath('//a[@class="store-locator__store__link button"]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        # oh = OpeningHours()
        map_data = response.xpath(
            '//script[contains(text(), "google.maps.LatLng")]/text()'
        ).extract_first()
        coordinates = re.search(r"var myLatlng = new google\.maps\.LatLng\((.*)\)", map_data).group(1)
        lat, lon = coordinates.split(",")


        properties = {
            "branch": response.xpath("//h1/text()").extract_first(),
            "addr_full": ", ".join(
                response.xpath('//div[@class="col l-col-16 store-locator__store__col"]/div/p/span/text()').extract()
            ),
            "phone": response.xpath(
                '//div[@class="col l-col-16 store-locator__store__col"]/div/span/a[contains(@href, "tel:")]/text()'
            ).extract_first(),
            "ref": response.url.replace("https://www.charlesclinkard.co.uk/map/", ""),
            "website": response.url,
            "lat": lat,
            "lon": lon,
            # "opening_hours": oh.as_opening_hours(),
        }
        yield Feature(**properties)
