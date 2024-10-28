import json

from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AvalonUSSpider(SitemapSpider):
    name = "avalon_us"
    item_attributes = {"brand": "Avalon", "brand_wikidata": "Q64665938"}
    sitemap_urls = [
        "https://www.avaloncommunities.com/arc/outboundfeeds/avb-sitemap/?outputType=xml&_website=avalon-communities"
    ]
    sitemap_rules = [(r"^https:\/\/www\.avaloncommunities\.com\/[\w-]+/[\w-]+-apartments/[\w-]+/$", "parse")]

    def parse(self, response):
        script = response.xpath("//script[@id='fusion-metadata']/text()").get()
        start = script.find("Fusion.globalContent=") + len("Fusion.globalContent=")
        end = script.find(";Fusion.globalContentConfig", start)
        location = json.loads(script[start:end])
        item = DictParser.parse(location)
        item["ref"] = location["communityId"]
        item["brand"] = location["classification"]
        item["image"] = response.css("img.communitybanner-img::attr(src)").get()

        oh = OpeningHours()
        for line in location["officeHours"]:
            oh.add_ranges_from_string(line)
        item["extras"]["opening_hours:office"] = oh.as_opening_hours()

        features = {f["icon"].removesuffix(".svg") for f in location["features"]}
        apply_yes_no(Extras.AIR_CONDITIONING, item, "/attribute-icons/airconditioning" in features)
        apply_yes_no(Extras.AIR_CONDITIONING, item, "airconditioning" in features)
        apply_yes_no(Extras.WHEELCHAIR, item, "adaaccessible" in features)
        apply_yes_no(Extras.WIFI, item, "highspeedwifi" in features)
        apply_yes_no(Extras.INDOOR_SEATING, item, "lounge" in features)
        apply_yes_no(Extras.PARCEL_PICKUP, item, "packageacceptance" in features)
        apply_yes_no(Extras.PETS_ALLOWED, item, "petfriendly" in features)
        apply_yes_no(Extras.SWIMMING_POOL, item, "pool" in features)
        if "smokefree" in features:
            apply_yes_no(Extras.SMOKING, item, False, False)

        yield item
