import phonenumbers
from phonenumbers import NumberParseException
from scrapy import Selector, Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES


class PaulROSpider(Spider):
    name = "paul_ro"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    start_urls = ["https://www.paul.ro/en/our-shops?ajax=1&all=1"]
    country = "RO"

    def parse(self, response):
        for location in response.xpath(".//marker"):
            item = Feature()
            item["ref"] = location.xpath("@id_store").get()
            item["branch"] = location.xpath("@name").get().replace("Paul ", "").replace("PAUL ", "")
            item["lat"] = location.xpath("@lat").get()
            item["lon"] = location.xpath("@lng").get()
            item["phone"] = location.xpath("@phone").get()
            addr_lines = location.xpath(".//@address").get().replace("<br />", "<br>").split("<br>")
            try:
                ph = phonenumbers.parse(addr_lines[-1], self.country)
                if phonenumbers.is_valid_number(ph):
                    addr_lines.remove(addr_lines[-1])
            except NumberParseException:
                pass
            item["addr_full"] = clean_address(addr_lines)
            if hours_text := location.xpath(".//@other").get():
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(Selector(text=hours_text).xpath("string(.)").get())
            yield item
