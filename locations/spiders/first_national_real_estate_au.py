from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser


class FirstNationalRealEstateAUSpider(Spider):
    name = "first_national_real_estate_au"
    item_attributes = {"brand": "First National Real Estate", "brand_wikidata": "Q122888198"}
    allowed_domains = ["www.firstnational.com.au"]
    start_urls = ["https://www.firstnational.com.au/offices"]

    def parse(self, response):
        locations_js = (
            response.xpath('//script[contains(text(), "var offices = ")]/text()')
            .get()
            .split("var offices = ", 1)[1]
            .split("}];", 1)[0]
            + "}]"
        )
        for location in parse_js_object(locations_js):
            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["addr_full"] = ", ".join(
                filter(None, map(str.strip, response.xpath('//div[@id="' + location["code"] + '"]/p/text()').getall()))
            )
            item["postcode"] = response.xpath('//div[@id="' + location["code"] + '"]/@data-postcode').get()
            item["phone"] = (
                response.xpath('//div[@id="' + location["code"] + '"]/p/a[contains(@href, "tel:")]/@href')
                .get("")
                .replace("tel:", "")
            )
            item["website"] = "https://www.firstnational.com.au/contact?office_id=" + str(location["id"])
            yield item
