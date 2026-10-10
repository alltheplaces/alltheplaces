import re

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Store details (name, address, phone, coordinates) are embedded directly in a
# Google Maps JS block on the store locator page, one line per store, e.g.:
# var myLatlng37 = new google.maps.LatLng(33.379208,-86.81016);var pinImg37 = ...
# pinImg37.alt = "Riverchase Galleria ~ 2400 Riverchase Galleria ~ Hoover, AL 35244 ~ (205) 982-4337";
# ...marker37.addListener("gmp-click", function() { window.location = "https://www.vonmaur.com/StorePage.aspx?ID=37";});
STORE_PATTERN = re.compile(
    r"var myLatlng(\d+) = new google\.maps\.LatLng\(([\-0-9.]+),([\-0-9.]+)\);"
    r'.*?pinImg\1\.alt = "([^"]*)".*?StorePage\.aspx\?ID=\1'
)
CITY_STATE_ZIP_PATTERN = re.compile(r"^(?P<city>.+), (?P<state>[A-Z]{2}) (?P<postcode>\d{5}(?:-\d{4})?)$")


class VonMaurUSSpider(Spider):
    name = "von_maur_us"
    item_attributes = {"brand": "Von Maur", "brand_wikidata": "Q7941483", "name": "Von Maur"}
    allowed_domains = ["www.vonmaur.com"]
    start_urls = ["https://www.vonmaur.com/Stores.aspx"]
    # The store locator returns "Access Denied" outside the US (see GitHub issue #804).
    requires_proxy = True
    # robots.txt disallows all crawling except for a handful of named search engine bots.
    # The site is also slow to respond, so allow more time than the default timeout.
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 90}

    def parse(self, response: Response):
        for store_id, lat, lon, alt_text in STORE_PATTERN.findall(response.text):
            branch, street_address, city_state_zip, phone = alt_text.split(" ~ ")
            city = state = postcode = None
            if m := CITY_STATE_ZIP_PATTERN.match(city_state_zip):
                city, state, postcode = m["city"], m["state"], m["postcode"]

            yield Request(
                f"https://www.vonmaur.com/StorePage.aspx?ID={store_id}",
                callback=self.parse_store,
                cb_kwargs={
                    "ref": store_id,
                    "lat": lat,
                    "lon": lon,
                    "branch": branch,
                    "street_address": street_address,
                    "city": city,
                    "state": state,
                    "postcode": postcode,
                    "phone": phone,
                },
            )

    def parse_store(self, response: Response, **kwargs):
        item = Feature(**kwargs, website=response.url)

        item["opening_hours"] = OpeningHours()
        # Markup for this block varies between stores (<br>-separated text, or a <p> per line), so read the
        # text nodes directly rather than relying on either markup shape.
        hour_lines = [
            line.strip()
            for line in response.xpath('//div[@class="divStoreInfoBoxHours"]//text()').getall()
            if re.match(r"^[A-Za-z-]+:", line.strip())
        ]
        item["opening_hours"].add_ranges_from_string(" ".join(hour_lines))

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
