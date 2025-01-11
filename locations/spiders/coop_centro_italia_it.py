from scrapy.http import FormRequest

from locations.categories import Categories, Sells, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class CoopCentroItaliaITSpider(JSONBlobSpider):
    name = "coop_centro_italia_it"
    api_domain = "https://storelocator.stagingfattoria.it"
    BRAND_COOP = {"brand": "Coop Centro Italia", "brand_wikidata": "Q3689971"}
    BRAND_SUPERCONTI = {"brand": "Superconti", "brand_wikidata": "Q69381940"}

    def start_requests(self):
        data = {"grant_type": "client_credentials", "client_id": "fatt0r!a", "client_secret": "fattM4tt!922"}
        yield FormRequest(f"{self.api_domain}/api/get-token", formdata=data, callback=self.after_token)

    def after_token(self, response):
        token = response.json()["access_token"]
        forms = [{"access_token": token}, {"access_token": token, "insegna": "superconti"}]
        for form in forms:
            yield FormRequest(f"{self.api_domain}/api/stores", formdata=form, callback=self.parse)

    def pre_process_data(self, location):
        geoloc = {}
        for key, value in location["postmeta"].items():
            if key.startswith("sl_store__"):
                key = key[10:]
            if key.startswith("geolocation"):
                geoloc[key[12:]] = value
            elif key != "id":
                location[key] = value
        geoloc["indirizzo"] = location["address_search"]
        location["geolocation"] = geoloc
        location["address"] = geoloc

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_SUPERMARKET, item)
        self.apply_branch_info(item, response, location)
        self.apply_opening_hours(item, response, location)
        self.apply_departments(item, response, location)
        yield item

    def apply_branch_info(self, item, response, location):
        item["branch"] = item.pop("name")
        if "type_coop_ci" in location:
            item.update(self.BRAND_COOP)
            item["name"] = [t["name"] for t in location["type_coop_ci"].values()][0]
            item["website"] = "https://www.coopcentroitalia.it/negozi/" + location["frontend_url"]
        else:
            item.update(self.BRAND_SUPERCONTI)
            item["name"] = [t["name"] for t in location["type_superconti"].values()][0]
            item["website"] = "https://www.superconti.eu/punti-vendita/" + location["store_slug"]
        if ft_img := location.get("featured_image"):
            item["image"] = ft_img
        elif gall := location.get("gallery"):
            item["image"] = [img for img in gall.values()][0]

    def apply_opening_hours(self, item, response, location):
        oh = OpeningHours()
        oh.add_ranges_from_string(
            location["geolocation"]["h"],
            days=DAYS_IT,
            named_day_ranges=NAMED_DAY_RANGES_IT,
            named_times=NAMED_TIMES_IT,
            closed=CLOSED_IT,
        )
        item["opening_hours"] = oh

    known_departments = {
        "coop salute": dict(dispensing="no", **Categories.PHARMACY.value),
        "abbigliamento": {Sells.CLOTHES.value: "yes"},
        "coop ottica": {Sells.EYEGLASSES.value: "yes", Sells.CONTACT_LENSES.value: "yes"},
        "pet store": {Sells.PET_SUPPLIES.value: "yes"},
        "pet food sfuso": {Sells.PET_SUPPLIES.value: "yes"},
        "edicola": {Sells.NEWSPAPERS.value: "yes"},
    }

    def apply_departments(self, item, response, location):
        for key in ["dep_superconti", "serv_superconti", "dep_coop_ci", "serv_coop_ci"]:
            for dep in location.get(key, {}).values():
                if known := self.known_departments.get(dep["name"].lower()):
                    apply_category(known, item)
