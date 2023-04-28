import re

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class MySizeAUSpider(Spider):
    name = "my_size_au"
    item_attributes = {"brand": "My Size", "brand_wikidata": "Q117948728"}
    allowed_domains = ["www.mysize.com.au"]
    start_urls = ["https://www.mysize.com.au/store-locator/"]

    def parse(self, response):
        locations = response.xpath('//div[contains(@class, "tab-content")]')
        for location in locations:
            print(location)
            properties = {
                "ref": location.xpath("h2[1]/strong/text()").get().strip(),
                "name": location.xpath("h2[1]/text()").get().strip(),
                "lat": location.xpath('div[contains(@class, "hidden")]/text()').get().split(",", 1)[0].strip(),
                "lon": location.xpath('div[contains(@class, "hidden")]/text()').get().split(",", 1)[1].strip(),
                "addr_full": re.sub(r"\s+", " ", ", ".join(location.xpath("p[1]/text()").getall()[:-1])).strip(),
                "phone": re.sub(r"\s+", " ", location.xpath("p[1]/text()").getall()[-1]).strip(),
            }
            if image_src := location.xpath("p//img/@src").get():
                properties["image"] = "https://www.mysize.com.au/" + image_src.split("?", 1)[0]
            hours_string = " ".join(location.xpath("table/tbody/tr/td//text()").getall())
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
