from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
import chompjs


class PdqUSSpider(SitemapSpider):
    name = "pdq_us"
    item_attributes = {"brand": "PDQ", "brand_wikidata": "Q87675367"}
    sitemap_urls = ["https://www.eatpdq.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/.*", "parse_store")]

    # The store pages here appear to be hand crafted HTML.
    # So, we need to look at where the 'text' is in the structure for a given heading
    def current_or_next_sibling_matching(self, label, styled_box):
        # Scenario 1: It's in the same node. https://www.eatpdq.com/locations/bradenton is the main example
        # Scenario 2: it's in the following node
        store_location = styled_box.xpath("div/div/p/span/strong[contains(text(), '" + label + "')]")
        if store_location.get():
            if store_location.xpath("../../text()").get() is not None:
                return store_location.xpath("../../text()").getall()
            else:
                return store_location.xpath("../../following-sibling::p[1]/text()").getall()

    def parse_address(self, item, styled_box):
        store_location = self.current_or_next_sibling_matching("Store Location", styled_box)
        store_address = self.current_or_next_sibling_matching("Store Address", styled_box)

        if store_location is not None and len(store_location) > 0:
            item["street_address"] = " ".join(store_location)

        if store_address is not None and len(store_address) > 0:
            item["street_address"] = " ".join(store_address)

    def parse_contact(self, item, styled_box):
        store_contact = self.current_or_next_sibling_matching("Store Contact", styled_box)

        if store_contact is not None and len(store_contact) > 0:
            if len(store_contact) == 3:
                item["phone"] = store_contact[2]
                item["email"] = store_contact[1]

    def parse_hours(self, item, styled_box):
        store_hours = self.current_or_next_sibling_matching("Hours of Operation", styled_box)

        if store_hours is not None and len(store_hours) > 0:
            if store_hours[1].strip() == "7 Days a Week":
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string("Mo-Su " + store_hours[0])
            else:
                self.logger.warn("Unparsed store hours: " + "\n".join(store_hours))

    def parse_store(self, response):
        if response.url == "https://www.eatpdq.com/locations/find-a-location":
            return

        styled_box = response.xpath('//div[@class="sqs-block html-block sqs-block-html"]')
        if styled_box:
            item = Feature()
            name = styled_box.xpath("div/div//h1/text()").get()
            if name:
                item["name"] = name.strip()

            self.parse_address(item, styled_box)
            self.parse_contact(item, styled_box)
            self.parse_hours(item, styled_box)

            if location_map := response.xpath('//div[contains(@data-block-json, "markerLat")]').get():
                json_data = chompjs.parse_js_object(location_map)["location"]

                item["lat"] = json_data["markerLat"] 
                item["lon"] = json_data["markerLng"] 

            item["ref"] = response.url
            item["website"] = response.url

            yield item
