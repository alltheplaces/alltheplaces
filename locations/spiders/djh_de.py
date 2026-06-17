import json
import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class DjhDESpider(SitemapSpider):
    name = "djh_de"
    item_attributes = {
        "brand": "Deutsches Jugendherbergswerk",
        "brand_wikidata": "Q1205753",
        "country": "DE",
    }
    sitemap_urls = ["https://www.jugendherberge.de/sitemap.xml"]
    # Match the /portraet sub-page which is present for each hostel in the sitemap
    sitemap_rules = [
        (r"/jugendherbergen/[^/]+/portraet$", "parse"),
    ]

    def parse(self, response: Response, **kwargs):
        # Extract Vue hostel-map component JSON
        raw = response.css("hostel-map::attr(data-prop-object)").get()
        if not raw:
            return
        data = json.loads(raw)
        pins = data.get("Pins", [])
        if not pins:
            return
        pin = pins[0]

        lat = pin.get("Latitude")
        lon = pin.get("Longitude")
        if not lat or not lon:
            return

        hostel_id = str(pin.get("HostelId", ""))
        name = pin.get("Name", "")
        street = (pin.get("Address") or "").strip()
        postcode = (pin.get("PostalCode") or "").strip()
        city = (pin.get("City") or "").strip()
        state = (pin.get("State") or "").strip()

        # Phone and email from contact box
        # Tel. +49 6261 7191 · email@example.com
        phone_raw = response.css("div.contact-box__reachability span").getall()
        phone = None
        for p in phone_raw:
            text = re.sub(r"<[^>]+>", "", p).strip()
            if text.startswith("Tel."):
                phone = text.replace("Tel.", "").strip()
                break

        email = response.css("div.contact-box__reachability a[href^='mailto:']::attr(href)").get()
        if email:
            email = email.replace("mailto:", "").strip()

        # Canonical hostel URL: strip /portraet suffix
        website = re.sub(r"/portraet$", "/", response.url)

        # Ref from hostel ID
        ref = hostel_id or re.sub(r".*/jugendherbergen/([^/]+)/.*", r"\1", response.url)

        item = Feature()
        item["ref"] = ref
        item["branch"] = name
        item["lat"] = float(lat)
        item["lon"] = float(lon)
        item["street_address"] = street
        item["postcode"] = postcode
        item["city"] = city
        item["state"] = state
        item["phone"] = phone
        item["email"] = email
        item["website"] = website
        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
