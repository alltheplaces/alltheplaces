import html
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.algolia import AlgoliaSpider
from locations.structured_data_spider import clean_facebook, clean_instagram


class AustralianVenueCompanyAUSpider(AlgoliaSpider):
    name = "australian_venue_company_au"
    item_attributes = {"operator": "Australian Venue Co.", "operator_wikidata": "Q122380559"}
    api_key = "286bd36070d06e5bb729e498f0134e1f"
    app_id = "KLAM1K0ACF"
    index_name = "prod_venues"
    myfilter = "country:AU AND wp_is_private:false"
    referer = "https://www.ausvenueco.com.au/"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = html.unescape(item["name"])
        item["street_address"] = merge_address_lines([feature.get("address_line_1"), feature.get("address_line_2")])
        item["website"] = feature.get("api_url")
        item["image"] = feature.get("image")
        set_social_media(item, SocialMedia.FACEBOOK, clean_facebook(feature.get("facebook")))
        set_social_media(item, SocialMedia.INSTAGRAM, clean_instagram(feature.get("instagram")))
        item["opening_hours"] = OpeningHours()
        if isinstance(feature["opening_hours"].get("hours"), list):
            for day_hours in feature["opening_hours"]["hours"]:
                item["opening_hours"].add_range(
                    DAYS[day_hours["open"]["day"] - 1], day_hours["open"]["time"], day_hours["close"]["time"], "%H%M"
                )
        apply_category(Categories.PUB, item)
        yield item
