from locations.storefinders.rio_seo import RioSeoSpider


class ScrubsAndBeyondUSSpider(RioSeoSpider):
    name = "scrubs_and_beyond_us"
    item_attributes = {
        "brand_wikidata": "Q119972011",
        "brand": "Scrubs & Beyond",
    }
    end_point = "https://maps.scrubsandbeyond.com"

    def post_process_feature(self, feature, location):
        feature["opening_hours"] = self.parse_hours(location["hours_set:primary"])
        # Unit number is duplicated across the first two lines
        feature["street_address"] = location["address_1"]
        yield feature
