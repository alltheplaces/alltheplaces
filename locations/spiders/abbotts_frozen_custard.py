import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AbbottsFrozenCustardSpider(SitemapSpider):
    name = "abbotts_frozen_custard"
    item_attributes = {
        "brand": "Abbott's Frozen Custard",
        "brand_wikidata": "Q4664334",
    }
    allowed_domains = ["abbottscustard.com"]
    sitemap_urls = ["https://www.abbottscustard.com/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"/location/", "parse")]

    def parse(self, response):
        item = Feature()

        # Extract unique identifier from URL
        item["ref"] = response.url.split("/")[-2]
        item["website"] = response.url

        # Extract store name - usually in H1
        name = response.xpath("//h1/text()").get()
        if name:
            item["name"] = name.strip()

        # Extract all text content to find structured data
        all_text = response.xpath("//body//text()").getall()
        clean_text = [text.strip() for text in all_text if text.strip()]

        # Find address section
        for i, text in enumerate(clean_text):
            if text == "Address" and i + 2 < len(clean_text):
                # Next two lines should be street and city/state/zip
                item["street_address"] = clean_text[i + 1]
                city_state_zip = clean_text[i + 2]

                # Parse city, state, zip
                # Pattern: "Fairport, New York 14450"
                match = re.match(r"^(.*?),\s*([A-Za-z\s]+)\s+(\d{5})$", city_state_zip)
                if match:
                    item["city"] = match.group(1).strip()
                    state = match.group(2).strip()
                    if len(state) == 2:
                        item["state"] = state
                    else:
                        item["state"] = self.get_state_abbrev(state)
                    item["postcode"] = match.group(3)
                break

        # Find phone section
        for i, text in enumerate(clean_text):
            if text == "Phone" and i + 1 < len(clean_text):
                phone_text = clean_text[i + 1]
                # Clean phone number and format
                phone_digits = re.sub(r"[^\d]", "", phone_text)
                if len(phone_digits) == 10:
                    item["phone"] = f"{phone_digits[:3]}-{phone_digits[3:6]}-{phone_digits[6:]}"
                break

        # Find store hours section
        for i, text in enumerate(clean_text):
            if text == "Store Hours":
                # Check if it's "Call store for details"
                if i + 1 < len(clean_text) and "Call store" in clean_text[i + 1]:
                    break

                # Parse hours
                oh = OpeningHours()
                j = i + 1
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

                while j < len(clean_text) and clean_text[j] in days:
                    day = clean_text[j]
                    if j + 1 < len(clean_text):
                        time_text = clean_text[j + 1]
                        # Pattern: "12:00 PM - 8:00 PM"
                        time_match = re.match(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", time_text)
                        if time_match:
                            open_time, close_time = time_match.groups()
                            # Add time format to match the spaces in the time string
                            oh.add_range(day, open_time, close_time, time_format="%I:%M %p")
                            j += 2  # Skip to next day
                        else:
                            j += 1
                    else:
                        j += 1

                if str(oh):  # Check if any hours were added
                    item["opening_hours"] = oh
                break

        # Set country
        item["country"] = "US"

        # All Abbott's locations are ice cream shops
        apply_category(Categories.ICE_CREAM, item)

        # Add parent venue information for locations inside other restaurants
        ref = item["ref"].lower()
        name_lower = item.get("name", "").lower()

        if "bill-grays" in ref or "bill gray" in name_lower:
            item["located_in"] = "Bill Gray's"
            item["located_in_wikidata"] = "Q4909199"
        elif "tom-wahls" in ref or "tom wahl" in name_lower:
            item["located_in"] = "Tom Wahl's"
            item["located_in_wikidata"] = "Q7817965"

        yield item

    def get_state_abbrev(self, state_name):
        """Convert full state name to abbreviation"""
        states = {
            "new york": "NY",
            "massachusetts": "MA",
            "florida": "FL",
            "texas": "TX",
            "louisiana": "LA",
            "south carolina": "SC",
            "north carolina": "NC",
            "tennessee": "TN",
        }
        return states.get(state_name.lower())
