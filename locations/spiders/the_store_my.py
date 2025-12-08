from scrapy import Spider

from locations.categories import Categories
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature


class TheStoreMYSpider(Spider):
    name = "the_store_my"
    item_attributes = {"brand": "The Store", "brand_wikidata": "Q96679754", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.tstore.com.my"]
    start_urls = ["https://www.tstore.com.my/storelocator.php"]

    def parse(self, response):
        for location in response.xpath('//div[@class="thumbnail"]'):
            properties = {
                "ref": location.xpath("./img/@src").get().split("_")[-1].split(".")[-2].split("/")[-1].split(".", 1)[0],
                "name": location.xpath('./div[@class="caption"]/h4/text()').get(),
                "addr_full": list(
                    filter(
                        None, map(str.strip, location.xpath('./div[@class="caption"]/small[last()]//text()').getall())
                    )
                )[0],
                "phone": list(
                    filter(
                        None, map(str.strip, location.xpath('./div[@class="caption"]/small[last()]//text()').getall())
                    )
                )[1]
                .split(",")[0]
                .strip(),
                "image": "https://www.tstore.com.my/" + location.xpath("./img/@src").get(),
                "opening_hours": OpeningHours(),
            }

            if len(location.xpath('./div[@class="caption"]/small')) == 2:
                properties["city"] = location.xpath('./div[@class="caption"]/small[1]/text()').get()

            google_maps_url = location.xpath('./div[@class="caption"]/div[@class="social-icon"]/a/@href').get()
            properties["lat"], properties["lon"] = url_to_coords(google_maps_url)

            hours_text = list(
                filter(None, map(str.strip, location.xpath('./div[@class="caption"]/small[last()]//text()').getall()))
            )[-1]
            hours_text = hours_text.replace("(", " ").replace(")", " ")
            properties["opening_hours"].add_ranges_from_string(hours_text)

            yield Feature(**properties)
