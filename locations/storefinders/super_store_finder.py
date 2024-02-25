import html
import re
from urllib.parse import urlparse

from scrapy import Request, Selector, Spider
from scrapy.http import Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.hours import OpeningHours
from locations.items import Feature

# Official documentation for Super Store Finder:
# https://superstorefinder.net/support/knowledgebase/
#
# To use this store finder, specify allowed_domains = [x, y, ..]
# (either one or more domains such as example.net) and the default
# path for the Super Store Finder API endpoint will be used.
# In the event the default path is different, you can alternatively
# specify one or more start_urls = [x, y, ..].
#
# If clean ups or additional field extraction is required from the
# XML source data, override the parse_item function. Two parameters
# are passed, item (an ATP "Feature" class) and location (a Scrapy
# "Selector" class that has selected the XML node for a particular
# location).


class SuperStoreFinderSpider(Spider, AutomaticSpiderGenerator):
    def start_requests(self):
        if len(self.start_urls) > 0:
            for url in self.start_urls:
                yield Request(url=url)
        else:
            for allowed_domain in self.allowed_domains:
                yield Request(url=f"https://{allowed_domain}/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php")

    def parse(self, response, **kwargs):
        for location in response.xpath("//store/item"):
            properties = {
                "ref": location.xpath("./storeId/text()").get(),
                "name": location.xpath("./location/text()").get(),
                "lat": location.xpath("./latitude/text()").get(),
                "lon": location.xpath("./longitude/text()").get(),
                "addr_full": html.unescape(re.sub(r"\s+", " ", location.xpath("./address/text()").get())),
                "phone": location.xpath("./telephone/text()").get(),
                "email": location.xpath("./email/text()").get(),
                "website": location.xpath("./website/text()").get(),
            }

            # In the event that the brand doesn't use store
            # identifiers, fall back to using the sort order of the
            # returned results for a unique identifier of each
            # store.
            if not properties["ref"]:
                properties["ref"] = location.xpath("./sortord/text()").get()

            hours_string = location.xpath("./operatingHours/text()").get()
            if hours_string:
                hours_string = hours_string.replace("<div>", " ").replace("</div>", " ").strip()
                properties["opening_hours"] = OpeningHours()
                properties["opening_hours"].add_ranges_from_string(hours_string)

            yield from self.parse_item(Feature(**properties), location) or []

    def parse_item(self, item: Feature, location: Selector, **kwargs):
        yield item

    def storefinder_exists(response: Response) -> bool | Request:
        # Example: https://soulpattinson.com.au/
        if response.xpath('//script[contains(@src, "/wp-content/plugins/superstorefinder-wp")]').get():
            return True

        return False

    def extract_spider_attributes(response: Response) -> dict | Request:
        return {
            "allowed_domains": [urlparse(response.url).netloc],
        }
