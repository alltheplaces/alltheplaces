import html
import re
import scrapy

from locations.items import GeojsonPointItem


class AnthonysSpider(scrapy.Spider):
    name = "anthonys"
    item_attributes = {"brand": "Anthony's Coal Fired Pizza", "country": "US"}
    allowed_domains = ["wp.acfp.com"]
    start_urls = ["https://wp.acfp.com/wp-json/wp/v2/locations?per_page=100"]

    def parse(self, response):
        for store in response.json():
            address = re.match(
                r"<p>(\d+) ([-. \w]+)<\/p>\n<p>([ \w]+), (\w{2}) (\d+)<\/p>",
                store["acf"]["page"]["info"]["address"],
            )
            item = GeojsonPointItem(
                {
                    "lat": store["acf"]["coords"]["latitude"],
                    "lon": store["acf"]["coords"]["longitude"],
                    "name": html.unescape(store["title"]["rendered"]),
                    "addr_full": html.unescape(
                        store["acf"]["page"]["info"]["address"]
                        .replace("\n", "")
                        .replace("<p>", "")
                        .replace("</p>", ", ")
                    ).strip(", "),
                    "phone": store["acf"]["page"]["info"]["tel"],
                    "website": "https://acfp.com/locations/" + store["slug"],
                    "ref": store["id"],
                }
            )

            if address:
                item["housenumber"] = address.group(1)
                item["street"] = address.group(2)
                item["street_address"] = address.group(1) + " " + address.group(2)
                item["city"] = address.group(3)
                item["state"] = address.group(4)
                item["postcode"] = address.group(5)

            yield item
