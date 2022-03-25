import scrapy
from locations.items import GeojsonPointItem
import re
import json

regex = r"\[{.*}\]"


class BlazePizzaSpider(scrapy.Spider):
    name = "blazepizza"
    item_attributes = {"brand": "Blaze Pizza"}
    allowed_domains = ["www.blazepizza.com"]
    start_urls = ["http://www.blazepizza.com/locations/"]

    def parse(self, response):
        script = response.xpath('//script[contains(., "var currentStates")]/text()')[
            0
        ].extract()

        data = re.search(regex, script).group()
        data = json.loads(data)

        for i in data:
            if i["Location"]["coming_soon"] == "N":
                ref = i["Location"]["location_id"]
                street = i["Location"]["address"]
                city = i["Location"]["city"]
                state = i["Location"]["state"]
                postcode = i["Location"]["zip"]
                country = i["Location"]["country"]
                phone = i["Location"]["phone"]
                name = i["Location"]["title"]
                lat = float(i["Location"]["lat"])
                lon = float(i["Location"]["lon"])
                website = i["Location"]["online_order_url"].replace("\\", "")
                addr_full = "{} {}, {} {} {}".format(
                    street, city, state, postcode, country
                )

                yield GeojsonPointItem(
                    ref=ref,
                    street=street,
                    city=city,
                    state=state,
                    postcode=postcode,
                    country=country,
                    addr_full=addr_full,
                    phone=phone,
                    name=name,
                    lat=lat,
                    lon=lon,
                    website=website,
                )
