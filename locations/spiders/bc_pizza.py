import re

from geonamescache import GeonamesCache
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class BcpizzaSpider(CrawlSpider):
    name = "bcpizza"
    item_attributes = {"brand": "BC Pizza", "brand_wikidata": "Q117600284"}
    allowed_domains = ["bc.pizza"]
    start_urls = ["https://bc.pizza/locations/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"\/locations\/[-\w]+\/$"),
            callback="parse",
        )
    ]

    def parse(self, response):
        name = response.xpath('//div[@class="wpb_wrapper"]/h1/text()').get()
        address_full = response.xpath('//div[@class="wpb_text_column wpb_content_element"]//p/text()').get()
        address = response.xpath('string(//div[@class="wpb_text_column wpb_content_element"]//p)').get()
        if address == address_full:
            address = response.xpath('//div[@class="wpb_text_column wpb_content_element"]//p[2]/text()').get()
        city_state_postcode = address.replace(address_full, "").replace("\n", "")
        postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", city_state_postcode)[0]
        city = city_state_postcode.split(",")[0]
        state = city_state_postcode.split(",")[1].replace(postcode, "").strip()
        for item in GeonamesCache().get_us_states().keys():
            if state == GeonamesCache().get_us_states()[item]["name"]:
                state = item
                break
        phone = response.xpath('//a[contains(@href, "tel")]/text()').get()
        facebook = response.xpath('//a[@class="vc_icon_element-link"]/@href').get()

        days = response.xpath('//table[contains(@class, "op-table")]//tr')
        oh = OpeningHours()
        for i, day in enumerate(days):
            dd = day.xpath(f"//tr[{i + 1}]//th/text()").get()
            hh = day.xpath(f"//tr[{i + 1}]//span/text()").get()
            if hh == "Closed":
                continue
            open_time, close_time = hh.split(" – ")
            oh.add_range(day=dd, open_time=open_time, close_time=close_time, time_format="%I:%M %p")

        properties = {
            "ref": response.url,
            "name": name,
            "city": city,
            "state": state,
            "postcode": postcode,
            "street_address": address_full,
            "phone": phone,
            "facebook": facebook,
            "website": response.url,
            "opening_hours": oh,
        }

        extract_google_position(properties, response)

        yield Feature(**properties)
