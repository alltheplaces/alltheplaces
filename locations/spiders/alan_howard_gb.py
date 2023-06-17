import chompjs
from scrapy import Selector, Spider

from locations.items import Feature


class AlanHowardGBSpider(Spider):
    name = "alan_howard_gb"
    item_attributes = {"brand": "Alan Howard", "brand_wikidata": "Q119260364"}
    allowed_domains = ["www.alanhoward.co.uk"]
    start_urls = ["https://www.alanhoward.co.uk/stores"]

    def parse(self, response):
        raw_data = response.xpath('//script[contains(text(), "var shops = [")]/text()').get()
        locations = chompjs.parse_js_object(raw_data.split("var shops = ", 1)[1].split("];", 1)[0] + "]")
        for location in locations:
            location_info = Selector(text=location[4])
            properties = {
                "ref": location[3],
                "name": location[0],
                "lat": location[1],
                "lon": location[2],
                "addr_full": ", ".join(filter(None, location_info.xpath("//*[not(self::a)]/text()").getall())).replace(
                    ", Telephone: ", ""
                ),
                "phone": location_info.xpath('//a[contains(@href, "tel:")]/@href').get().replace("tel:", ""),
                "website": "https://www.alanhoward.co.uk" + location_info.xpath('//a[@class="anchorLink"]/@href').get(),
            }
            yield Feature(**properties)
