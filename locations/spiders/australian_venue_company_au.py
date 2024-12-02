from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.algolia import AlgoliaSpider
from locations.structured_data_spider import clean_facebook, clean_instagram


class AustralianVenuCompanyAUSpider(AlgoliaSpider):
    name = "australian_venue_company_au"
    item_attributes = {
        "operator": "Australian Venue Co.",
        "operator_wikidata": "Q122380559",
        "extras": Categories.PUB.value,
    }
    api_key = "286bd36070d06e5bb729e498f0134e1f"
    app_id = "KLAM1K0ACF"
    index_name = "prod_venues"
    myfilter = "country:AU AND wp_is_private:false"
    referer = "https://www.ausvenueco.com.au/"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature.get("address_line_1"), feature.get("address_line_2")])
        item["website"] = feature.get("api_url")
        item["image"] = feature.get("image")
        item["facebook"] = clean_facebook(feature.get("facebook"))
        item["extras"]["contact:instagram"] = clean_instagram(feature.get("instagram"))
        item["opening_hours"] = OpeningHours()
        if isinstance(feature["opening_hours"].get("hours"), list):
            for day_hours in feature["opening_hours"]["hours"]:
                item["opening_hours"].add_range(
                    DAYS_EN[DAYS_3_LETTERS_FROM_SUNDAY[day_hours["open"]["day"]]],
                    day_hours["open"]["time"],
                    day_hours["close"]["time"],
                    "%H%M",
                )
        yield item
