import re

from scrapy import Request

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Coordinates on the /location sub-page default to this bogus placeholder
# (somewhere off the coast of Nova Scotia) when the real value hasn't been
# set for a property, so it must be discarded rather than used.
BROKEN_DEFAULT_LOCATION = ("45.088530", "-64.367951")


class BulgariHotelsSpider(StructuredDataSpider):
    name = "bulgari_hotels"
    item_attributes = {"brand": "Bulgari Hotels & Resorts", "brand_wikidata": "Q91602871"}
    start_urls = [
        f"https://www.bulgarihotels.com/en_US/{slug}"
        for slug in ["rome", "milan", "paris", "london", "dubai", "bali", "tokyo", "beijing", "shanghai"]
    ]

    def pre_process_data(self, ld_data, **kwargs):
        if address := ld_data.get("address"):
            if address.get("addressCountry") == "UAE":
                address["addressCountry"] = "United Arab Emirates"
                # Dubai has no postal code system, so "00000" is a placeholder.
                address["postalCode"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.HOTEL, item)

        # The postcode from JSON-LD is sometimes truncated (e.g. Tokyo's
        # "0028" instead of "104-0028"); prefer a fuller value found in the
        # street address if one is present there.
        if item.get("postcode") and item.get("street_address"):
            if m := re.search(r"\b(\d{3}-\d{4})\b", item["street_address"]):
                item["postcode"] = m.group(1)

        yield Request(
            url=response.urljoin(f"{response.url}/location"),
            callback=self.parse_location,
            cb_kwargs={"item": item},
        )

    def parse_location(self, response, item):
        lat = response.xpath("//div[@data-location-latitude]/@data-location-latitude").get()
        lon = response.xpath("//div[@data-location-longitude]/@data-location-longitude").get()
        if lat and lon and (lat, lon) != BROKEN_DEFAULT_LOCATION:
            item["lat"] = lat
            item["lon"] = lon
        yield item
