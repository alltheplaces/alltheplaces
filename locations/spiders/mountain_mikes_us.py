from scrapy import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider

AMENITIES = {
    "Arcade": None,
    "Big Screen TVs": "television",
    "Buffet": None,
    "Craft Beer": "drink:beer",
    "Free WiFi": Extras.WIFI,
    "Full Bar": Extras.BAR,
    "Party Room": None,
    "Patio Seating": Extras.OUTDOOR_SEATING,
    "Wine": "drink:wine",
}


class MountainMikesUSSpider(StructuredDataSpider):
    name = "mountain_mikes_us"
    item_attributes = {"brand": "Mountain Mike's", "brand_wikidata": "Q6925120"}
    start_urls = ["https://www.mountainmikespizza.com/locations/"]

    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response):
        for location in response.xpath("//div[starts-with(@class, 'location_block')]"):
            yield Request(
                location.xpath("*/div[@class='loc_name']/a/@href").get(),
                callback=self.parse_location,
                cb_kwargs={"lat": location.xpath("@data-lat").get(), "lon": location.xpath("@data-long").get()},
            )

    def parse_location(self, response, lat, lon):
        for item in self.parse_sd(response):
            item["ref"] = response.xpath("//button/@data-storecode").get()
            if item["ref"] is None:
                # coming soon
                break

            item["addr_full"] = item.pop("street_address")
            item["branch"] = response.xpath("//meta[@property='og:title']/@content").get()
            del item["image"]
            item["lat"] = lat
            item["lon"] = lon
            del item["name"]
            item["website"] = response.url
            item["extras"]["website:orders"] = response.css(".heading_order_cta::attr(href)").get("").strip()

            for social in response.xpath("//div[@id='loc_social']/a[starts-with(@class, 'social_icon')]"):
                item["extras"][f"contact:{social.xpath('@class').get().split()[1]}"] = social.xpath("@href").get()

            for amenity in response.xpath("//div[@class='amenity']/div[@class='label']/text()").getall():
                if amenity in AMENITIES:
                    if AMENITIES[amenity] is not None:
                        apply_yes_no(AMENITIES[amenity], item, True)
                elif amenity == "Catering":
                    apply_category(Categories.CRAFT_CATERER, item)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_amenity/{amenity}")

            yield item

    def pre_process_data(self, ld_data, **kwargs):
        if "openingHours" in ld_data:
            ld_data["openingHours"] = [
                f"{days} {hours}"
                for rule in ld_data["openingHours"]
                for days, hours in zip(rule.split()[0::2], rule.split()[1::2])
            ]
