from scrapy import Spider
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TicketmasterAUSpider(Spider):
    name = "ticketmaster_au"
    allowed_domains = ["www.ticketmaster.com.au"]
    start_urls = ["https://www.ticketmaster.com.au/h/stateselectoutlets.html"]
    item_attributes = {
        "brand": "Ticketmaster",
        "brand_wikidata": "Q2609162",
    }
    no_refs = True

    def parse(self, response):
        for state in LinkExtractor(allow="/tcentres/").extract_links(response):
            yield Request(url=state.url, callback=self.parse_state)

    def parse_state(self, response):
        state = response.xpath(".//title/text()").get().split("|")[0].replace("Ticketmaster Outlets", "").strip()
        for location in response.xpath('.//div[@class="outletSpan"]'):
            item = Feature()
            item["state"] = state
            item["branch"] = location.xpath(".//h1/text()").get()
            item["street_address"] = clean_address(
                [location.xpath(".//h2/text()").get(), location.xpath(".//h3/text()").get()]
            )
            extract_google_position(item, location)
            item["opening_hours"] = OpeningHours()
            for day in location.xpath('.//div[@class="outletDays"]').getall():
                item["opening_hours"].add_ranges_from_string(day)
            yield item
