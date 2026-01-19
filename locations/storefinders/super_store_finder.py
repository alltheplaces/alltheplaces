import re
from html import unescape
from typing import AsyncIterator, Iterable

from scrapy import Selector, Spider
from scrapy.http import Request, TextResponse

from locations.hours import OpeningHours
from locations.items import Feature


class SuperStoreFinderSpider(Spider):
    """
    Official documentation for Super Store Finder is available at:
    https://superstorefinder.net/support/knowledgebase/

    To use this store finder, specify allowed_domains = ["example.net"] and
    the default path for the Super Store Finder API endpoint will be used. In
    the event the default path is different, you can alternatively specify
    start_urls = ["https://example.net/custom-path/wp-content/plugins/
                   superstorefinder-wp/ssf-wp-xml.php"].

    If clean ups or additional field extraction is required from the XML
    source data, override the parse_item function. Two parameters are passed:
      item: an ATP "Feature" class
      location: a Scrapy "Selector" class that has selected the XML node for
      a particular location

    Note that some variants of this spider exist, where a url such as
    https://flippinpizza.com/wp-content/uploads/ssf-wp-uploads/ssf-data.json
    is available.
    """

    allowed_domains: list[str] = []
    start_urls: list[str] = []

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) == 0 and len(self.allowed_domains) == 1:
            yield Request(
                url=f"https://{self.allowed_domains[0]}/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php"
            )
        elif len(self.start_urls) == 1:
            yield Request(url=self.start_urls[0])
        else:
            raise ValueError(
                "Specify one domain name in the allowed_domains list attribute or one URL in the start_urls list attribute."
            )

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.xpath("//store/item"):
            properties = {
                "ref": location.xpath("./storeId/text()").get(),
                "name": location.xpath("./location/text()").get(),
                "lat": location.xpath("./latitude/text()").get(),
                "lon": location.xpath("./longitude/text()").get(),
                "addr_full": unescape(re.sub(r"\s+", " ", location.xpath("./address/text()").get())),
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

    def parse_item(self, item: Feature, location: Selector) -> Iterable[Feature]:
        yield item
