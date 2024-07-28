from chompjs import parse_js_object
from scrapy import Selector, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BedsRUSAUSpider(Spider):
    name = "beds_r_us_au"
    item_attributes = {"brand": "Beds R Us", "brand_wikidata": "Q126179491", "extras": Categories.SHOP_BED.value}
    allowed_domains = ["bedsrus.com.au"]
    start_urls = ["https://bedsrus.com.au/find-a-store/"]

    def parse(self, response):
        js_blob = response.xpath('//script[@id="maplistko-js-extra"]').get()
        json_blob = parse_js_object(js_blob)

        for location in json_blob["KOObject"][0]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["locationUrl"].strip("/").split("/")[-1]
            item["branch"] = item["name"].replace("Beds R Us ", "")

            additional_fields = Selector(text=location["description"])
            item["addr_full"] = clean_address(additional_fields.xpath('//div[@class="address"]//text()').getall())
            item["phone"] = additional_fields.xpath('//a[contains(@href, "tel:")]/@href').get("").replace("tel:", "")

            hours_string = " ".join(
                filter(
                    None,
                    map(str.strip, additional_fields.xpath('//div[@class="section_oh_short_desc"]//text()').getall()),
                )
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
