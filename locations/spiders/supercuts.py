import scrapy
from locations.items import GeojsonPointItem
import re
from io import StringIO
from scrapy.http import HtmlResponse
from functools import partial
from datetime import datetime

default_headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/63.0.3239.84 Safari/537.36"
}


def get_hours(hour_list):
    try:
        ret = []
        for hours in hour_list:
            open_time = datetime.strptime(hours["hours"]["open"], "%I:%M %p").strftime(
                "%H:%M"
            )
            close_time = datetime.strptime(
                hours["hours"]["close"], "%I:%M %p"
            ).strftime("%H:%M")
            split_days = hours["days"].split(" - ")
            if "-" in hours["days"] and len(split_days) == 2:
                start_day, end_day = split_days
                ret.append(
                    "{} {}-{}".format(
                        "-".join([start_day[:2], end_day[:2]]), open_time, close_time
                    )
                )
            else:
                ret.append("{} {}-{}".format(hours["days"][:2], open_time, close_time))
        return "; ".join(ret)
    except:
        return None


class SuperCutsScraper(scrapy.Spider):
    name = "supercuts"
    item_attributes = {"brand": "Supercuts", "brand_wikidata": "Q7643239"}

    start_urls = ["https://www.supercuts.com/salon-directory.html"]

    def parse(self, response):
        states = [
            x.xpath("@href").extract_first()
            for x in response.css("a[href*='supercuts.com/locations/']")
        ]
        for state_url in states:
            yield scrapy.Request(state_url, callback=self.parse_cities)

    def parse_cities(self, response):
        cities = [
            x.xpath("@href").extract_first()
            for x in response.css("a[href*='locations/']")
        ]
        for city_url in cities:
            yield scrapy.Request(
                response.urljoin(city_url), callback=self.parse_locations
            )

    def parse_locations(self, response):
        locations = [
            x.xpath("@href").extract_first()
            for x in response.css("a[href*='locations/']")
        ]
        salon_base = "https://info3.regiscorp.com/salonservices/siteid/1/salon/{}"
        for location in locations:
            salon_id = location.strip(".html").split("-")[-1]
            if salon_id.isnumeric():
                yield scrapy.Request(
                    salon_base.format(salon_id),
                    callback=partial(
                        self.parse_result, trunk={"url": response.urljoin(location)}
                    ),
                )

    def parse_result(self, response, trunk={}):
        result = response.json()
        if result.get("name"):
            name = "Supercuts " + result["name"].title()
            yield GeojsonPointItem(
                lat=result["latitude"],
                lon=result["longitude"],
                name=name,
                addr_full=result["address"],
                city=result["city"],
                state=result["state"],
                postcode=result["zip"],
                phone=result["phonenumber"],
                website=trunk["url"],
                opening_hours=get_hours(result["store_hours"]),
                ref=response.url.split("/")[-1],
            )
