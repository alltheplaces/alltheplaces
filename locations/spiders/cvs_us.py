import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.spiders.schnucks_us import SchnucksUSSpider
from locations.spiders.target_us import TargetUSSpider
from locations.spiders.tesco_gb import set_located_in
from locations.structured_data_spider import StructuredDataSpider

CVS = {"name": "CVS Pharmacy", "brand": "CVS Pharmacy", "brand_wikidata": "Q2078880"}

PHARMACY_BRANDS = {
    "CVS Pharmacy": CVS,
    "CVS HealthHub": CVS,
    "CVS Pharmacy y más": CVS | {"name": "CVS Pharmacy y más"},
    "Longs Drugs": {"brand": "Longs Drugs", "brand_wikidata": "Q16931196"},
    "Navarro": {"name": "Navarro", "brand": "Navarro", "brand_wikidata": "Q6982161"},
}


class CvsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cvs_us"
    allowed_domains = ["www.cvs.com"]
    sitemap_urls = ["https://www.cvs.com/sitemap/store-details.xml"]

    def parse(self, response):
        if response.css("link[rel~=canonical]").attrib["href"] == "https://www.cvs.comundefined":
            # Weird garbage, seemingly for closed locations
            return
        yield from super().parse(response)

    def post_process_item(self, item, response, ld_data, **kwargs):
        props = response.xpath("//@sd-props").get()
        if not props:
            return  # Some urls get redirected to the city page
        data = json.loads(props)
        store_info = data["cvsStoreDetails"]["storeInfo"]
        item["lat"] = store_info["latitude"]
        item["lon"] = store_info["longitude"]
        item["ref"] = store_info["storeId"]

        item["name"] = None
        item["image"] = None
        item["street_address"] = item.get("street_address", "").removeprefix("at ")

        # OSM generally wants to model a separate node for the shop, pharmacy,
        # and clinic; this data is a little too messy for that, so just collect
        # the store's distinguishing attributes as properties on a single feature.
        item["extras"]["departments"] = ";".join(sorted(store_info["identifier"]))
        store_type = data["cvsStoreTypeImage"]["altText"]
        # A pharmacy category still can be applied as it's present for all locations.
        apply_category(Categories.PHARMACY, item)

        # There are multiple pharmacy brands owned by CVS
        if brand := PHARMACY_BRANDS.get(store_type):
            item.update(brand)
        elif store_type == "CVS Pharmacy at Target":
            item.update(CVS)
            set_located_in(TargetUSSpider.item_attributes, item)
        elif store_type == "Schnucks":
            item.update(CVS)
            set_located_in(SchnucksUSSpider.item_attributes, item)
        else:
            self.crawler.stats.inc_value("atp/cvs_us/unmapped_store_type/{}".format(store_type))
            item["extras"]["store_type"] = store_type
            # Default to CVS Pharmacy
            item.update(CVS)

        hours = {}
        for dept in data["cvsStoreDetails"]["hours"]["departments"]:
            dept_name = dept["name"]
            try:
                hours[f"opening_hours:{dept_name}"] = self.parse_hours(dept["regHours"])
            except Exception as e:
                self.logger.warning(f"Failed to parse hours for '{dept_name}': {hours}, {e}")
                self.crawler.stats.inc_value("atp/cvs_us/hours/failed")

        item["extras"].update(hours)

        # Most stores have retail, with the exception of those located inside
        # Target, or bad data. We've defined specific opening_hours above; pick
        # one and promote it to the unqualified key.
        if default := hours.get("opening_hours:retail") or hours.get("opening_hours:pharmacy"):
            item["opening_hours"] = default

        yield item

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for row in hours:
            if row["startTime"] == "Open 24 Hours":
                row["startTime"] = "12:00 AM"
            if row["endTime"] == "Open 24 Hours":
                row["endTime"] = "11:59 PM"

            if {"breakStart", "breakEnd"} <= row.keys():
                intervals = [
                    (row["startTime"], row["breakStart"]),
                    (row["breakEnd"], row["endTime"]),
                ]
            else:
                intervals = [
                    (row["startTime"], row["endTime"]),
                ]
            for open_time, close_time in intervals:
                opening_hours.add_range(row["weekday"], open_time, close_time, "%I:%M %p")
        return opening_hours.as_opening_hours()
