import re

from unidecode import unidecode

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class MatchFRSpider(JSONBlobSpider, PlaywrightSpider):
    name = "match_fr"
    item_attributes = {"brand": "Match", "brand_wikidata": "Q513977"}
    start_urls = ["https://api-drive.drive.supermarchesmatch.fr/api/v2/sites/search?allsites=true"]
    locations_key = "data"
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def pre_process_data(self, feature):
        feature.update(feature.pop("site"))

    def post_process_item(self, item, response, feature):
        item["ref"] = feature["code"]
        item["branch"] = feature["libelle"]
        item["street_address"] = merge_address_lines([feature["adresse1"], feature["adresse2"], feature["adresse3"]])
        item["postcode"] = feature["codePostal"]
        item["city"] = feature["ville"]
        slug = re.sub(r"\W+", "-", unidecode(feature["libelle"]).lower()).strip("-")
        item["website"] = f"https://www.supermarchesmatch.fr/fr/details-magasin/{feature['code']}/{slug}"

        item["opening_hours"] = OpeningHours()
        for key, hours in feature.items():
            if key.startswith("horaire") and key != "horairesExceptionnels" and hours:
                item["opening_hours"].add_range(sanitise_day(key.removeprefix("horaire"), DAYS_FR), *hours.split("-"))
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
