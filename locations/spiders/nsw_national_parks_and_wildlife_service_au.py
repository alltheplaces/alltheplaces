from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class NswNationalParksAndWildlifeServiceAUSpider(SitemapSpider, StructuredDataSpider):
    name = "nsw_national_parks_and_wildlife_service_au"
    item_attributes = {
        "state": "New South Wales",
        "operator": "NSW National Parks and Wildlife Service",
        "operator_wikidata": "Q108872274",
    }
    allowed_domains = ["www.nationalparks.nsw.gov.au"]
    sitemap_urls = ["https://www.nationalparks.nsw.gov.au/sitemap.xml"]
    sitemap_rules = [
        (
            r"^https:\/\/www\.nationalparks\.nsw\.gov\.au\/camping-and-accommodation\/(?:accommodation|campgrounds)\/[\w\-]+$",
            "parse_sd",
        )
    ]
    wanted_types = ["Accommodation", "Campground"]

    def post_process_item(self, item, response, ld_data):
        item.pop("email", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        if "/campgrounds/" in response.url:
            apply_category(Categories.TOURISM_CAMP_SITE, item)
            apply_category({"reservation": "required"}, item)
            for campground_detail in response.xpath('//table[contains(@class, "itemDetails")]/tr'):
                if campground_detail.xpath('./th[contains(text(), "Number of campsites")]'):
                    capacity = campground_detail.xpath("./td/text()").get()
                    apply_category({"capacity:pitches": capacity}, item)
                elif campground_detail.xpath('./th[contains(text(), "Camping type")]'):
                    camping_types = campground_detail.xpath("./td/text()").get().lower()
                    apply_yes_no(
                        Extras.TENT_SITES,
                        item,
                        "tent" in camping_types or "camping beside my vehicle" in camping_types,
                        False,
                    )
                    apply_yes_no(
                        Extras.CARAVAN_SITES,
                        item,
                        "camper trailer site" in camping_types or "caravan site" in camping_types,
                        False,
                    )
                    apply_yes_no(
                        Extras.MOTOR_VEHICLES,
                        item,
                        "camping beside my vehicle" in camping_types
                        or "camper trailer site" in camping_types
                        or "caravan site" in camping_types,
                        False,
                    )
                elif campground_detail.xpath('./th[contains(text(), "Facilities")]'):
                    facilities = campground_detail.xpath("./td/text()").get().lower()
                    apply_yes_no(Extras.BARBEQUES, item, "barbecue facilities" in facilities, False)
                    apply_yes_no(Extras.PICNIC_TABLES, item, "picnic tables" in facilities, False)
                    apply_yes_no(Extras.TOILETS, item, "toilets" in facilities, False)
                    apply_yes_no(Extras.DRINKING_WATER, item, "drinking water" in facilities, False)
                    apply_yes_no(Extras.SHOWERS, item, "showers" in facilities, False)
        else:
            # Other types of accommodation are extremely varied and
            # are difficult to tag accurately:
            # * One cabin, house or hut without an on-site manager.
            # * A cabin, house or hut with multiple rooms where
            #   each room can be booked separately. There could be
            #   common facilities and an on-site manager.
            # * A group of cabins or huts. There could be common
            #   facilities and an on-site manager.
            # * A hotel.
            # * Lightstation cottages that may have an on-site
            #   manager to provide services.
            # * And more!
            # Due to this complexity and very basic accommodation
            # tagging standards of OSM, an attempt is not yet made
            # to capture details about these other accommodation
            # types.
            apply_category({"tourism": "yes"}, item)
            apply_category({"reservation": "required"}, item)
        yield item
