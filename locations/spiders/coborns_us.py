import re
from urllib.parse import urlsplit

import scrapy

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature

LIQUOR_ANNEX = re.compile(r"liquor|wine\s*&?\s*spirits", re.IGNORECASE)


class CobornsUSSpider(scrapy.Spider):
    name = "coborns_us"
    # Coborn's Incorporated operates several distinct retail banners, all built on the
    # same Sitefinity CMS platform and sharing the same RenderSEO location API/tenant key.
    banners = {
        "coborns.com": {"name": "Coborn's", "brand": "Coborn's"},
        "cashwise.com": {"name": "Cash Wise Foods", "brand": "Cash Wise Foods", "liquor_name": "Cash Wise Liquor"},
        "shopmarketplacefoods.com": {"name": "Marketplace Foods", "brand": "Marketplace Foods"},
        # Hornbacher's has a Wikidata entity, but no NSI brand entry exists yet, so the
        # "brand" tag is left unset to avoid shipping an untraceable brand claim.
        "hornbachers.com": {
            "name": "Hornbacher's",
            "brand_wikidata": "Q5904043",
            "liquor_name": "Hornbacher's Wine & Spirits",
        },
    }
    start_urls = [f"https://{domain}/stores" for domain in banners]
    renderseo_api = "https://api.renderseo.com:8443/api/v1/5CBVjiS9zqntMi7bTNS9/locations/{}?view=sloc"

    def parse(self, response):
        domain = urlsplit(response.url).netloc.removeprefix("www.")
        banner = self.banners[domain]
        for card in response.css(".card[data-store-id]"):
            store_id = card.attrib["data-store-id"]
            detail_url = card.css("a.btn-primary::attr(href)").get()
            branch = card.css(".card-header::text").get("").strip()
            if not detail_url:
                continue
            yield response.follow(
                detail_url,
                callback=self.parse_store,
                meta={"store_id": f"{domain}_{store_id}", "banner": banner, "branch": branch},
            )

    def parse_store(self, response):
        item = Feature()
        item["ref"] = response.meta["store_id"]
        item["website"] = response.url
        item["branch"] = response.meta["branch"]
        banner = dict(response.meta["banner"])
        liquor_name = banner.pop("liquor_name", None)
        item.update(banner)
        extract_google_position(item, response)

        if LIQUOR_ANNEX.search(item["branch"]):
            # A standalone liquor-only annex under the same corporate operator, not the
            # grocery banner itself, so it gets its own name and no unverified brand tag.
            item["name"] = liquor_name or f"{item['name']} Liquor"
            item.pop("brand", None)
            item.pop("brand_wikidata", None)
            apply_category(Categories.SHOP_ALCOHOL, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)

        yield scrapy.Request(
            self.renderseo_api.format(response.meta["store_id"].split("_", 1)[1]),
            callback=self.parse_renderseo,
            meta={"item": item},
        )

    def parse_renderseo(self, response):
        item = response.meta["item"]
        data = response.json().get("item")
        if not data:
            return

        item["street_address"] = data.get("fullAddressLine") or " ".join(data.get("addressLines") or [])
        item["city"] = data.get("city")
        item["state"] = data.get("state")
        item["postcode"] = data.get("postalCode")
        item["country"] = data.get("country") or "US"
        if phones := data.get("phoneNumbers"):
            item["phone"] = phones[0]

        if (hours := data.get("businessHours")) and len(hours) == 7:
            oh = OpeningHours()
            for day, day_hours in zip(DAYS_FROM_SUNDAY, hours):
                if day_hours and len(day_hours) == 2:
                    oh.add_range(day, day_hours[0], day_hours[1])
            item["opening_hours"] = oh

        yield item
