import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FonehouseGBSpider(CrawlSpider):
    name = "fonehouse_gb"
    item_attributes = {
        "brand": "fonehouse",
        "brand_wikidata": "Q130535827",
        "country": "GB",
    }

    start_urls = ["https://www.fonehouse.co.uk/store-finder"]
    rules = [Rule(LinkExtractor(allow=r"/stores/([^/]+)$"), callback="parse")]
    # wanted_types = ["LocalBusiness"]

    def parse(self, response):
        ldjson = response.xpath('//script[@type="application/ld+json"]/text()[contains(.,\'"LocalBusiness"\')]').get()
        data = json.decoder.JSONDecoder(strict=False).raw_decode(ldjson, ldjson.index("{"))[0]
        oh = OpeningHours()
        hours = data.get("openingHoursSpecification")
        for day in hours:
            if day["opens"] == day["closes"]:
                continue
            oh.add_range(day.get("dayOfWeek")[0][:2].capitalize(), day.get("opens"), day.get("closes"))

        properties = {
            "ref": response.url,
            "name": data.get("name"),
            "branch": data.pop("name").removeprefix("Fonehouse").strip(),
            "phone": data.get("telephone"),
            "email": data.get("email"),
            "street_address": data.get("address", {}).get("streetAddress"),
            "city": data.get("address", {}).get("addressLocality"),
            "state": data.get("address", {}).get("addressCountry"),
            "country": "GB",
            "postcode": data.get("address", {}).get("postalCode"),
            "lat": data.get("geo", {}).get("latitude"),
            "lon": data.get("geo", {}).get("longitude"),
            "image": data.get("image"),
            "website": response.url,
            "opening_hours": oh,
        }
        item = Feature(**properties)
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
