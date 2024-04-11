import re

import scrapy

from locations.categories import Categories
from locations.items import Feature


class CrownBurgersSpider(scrapy.Spider):
    name = "crown_burgers"
    item_attributes = {"brand": "Crown Burgers", "brand_wikidata": "Q5189316", "extras": Categories.RESTAURANT.value}
    allowed_domains = ["crown-burgers.com"]
    start_urls = ("http://www.crown-burgers.com/locations.php",)
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        names = response.xpath('//div[@id="right_frame"]/p[@class="loc_nums"]')
        infos = response.xpath('//div[@id="right_frame"]/p[br]')
        maps_urls = response.xpath("//iframe/@src")
        for name, info, maps_url in zip(names, infos, maps_urls):
            maps_url = maps_url.get()
            coords = re.findall("-{0,1}[0-9]{1,3}.[0-9]+,-{0,1}[0-9]{1,3}.[0-9]+", maps_url) if maps_url else None
            yield Feature(
                ref=name.xpath("./text()[1]").get(),
                name=name.xpath("./text()[1]").get(),
                phone=info.xpath("./text()[3]").get(),
                street_address=info.xpath("./text()[1]").get(),
                lat=coords[0].split(",")[0] if coords else None,
                lon=coords[0].split(",")[1] if coords else None,
                postcode=re.findall("[0-9]{5}", info.xpath("./text()[2]").get())[0],
            )
