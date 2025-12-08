from locations.categories import Categories, PaymentMethods, Sells, apply_category, apply_yes_no
from locations.hours import CLOSED_IT, DAYS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


def clean_strings(iterator):
    return list(filter(bool, map(str.lower, map(str.strip, iterator))))


class CoopAlleanzaITSpider(JSONBlobSpider):
    name = "coop_alleanza_it"
    item_attributes = {
        "brand": "Coop Alleanza 3.0",
        "brand_wikidata": "Q21189584",
    }
    allowed_domains = ["www.coopalleanza3-0.it"]
    start_urls = ["https://www.coopalleanza3-0.it/storeLocatorServlet/?operation=getStores"]

    custom_name = {
        "Minimercato": "Minimercato Coop",
        "Supermercato": "Supermercato Coop",
        "affiliati": "Coop",
        "amici affiliato": "Amici di casa coop",
    }

    def pre_process_data(self, location):
        location["branch"] = location["title"].replace(" - Affiliato Coop Alleanza 3.0", "").strip()
        location["name"] = self.custom_name.get(location["storeType"], location["storeType"])
        location["website"] = (
            f"https://www.coopalleanza3-0.it/fare-spesa/elenco-negozi/dettaglio-negozio/{location['detailsPage']}.html"
        )

    store_types = {
        "Amici di casa coop": Categories.SHOP_PET,
        "Extracoop": Categories.SHOP_SUPERMARKET,
        "Ipercoop": Categories.SHOP_SUPERMARKET,
        "Minimercato": Categories.SHOP_SUPERMARKET,
        "Minimercato Coop": Categories.SHOP_SUPERMARKET,
        "Supermercato": Categories.SHOP_SUPERMARKET,
        "Supermercato Coop": Categories.SHOP_SUPERMARKET,
        "Superstore Coop": Categories.SHOP_SUPERMARKET,
        "affiliati": Categories.SHOP_SUPERMARKET,
        "amici affiliato": Categories.SHOP_PET,
    }

    def post_process_item(self, item, response, location):
        item["branch"] = location["title"].replace(" - Affiliato Coop Alleanza 3.0", "").strip()
        item["state"] = location["district"]
        item["extras"] = {}
        apply_category(self.store_types.get(location["storeType"], Categories.SHOP_SUPERMARKET), item)
        if location["storeType"] not in self.store_types:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_store_types/{location['storeType']}")
        yield response.follow(item["website"], cb_kwargs={"item": item}, callback=self.parse_store_extra)

    def parse_store_extra(self, response, item):
        if phone := response.css('.telephone-fax a[href*="tel:"]::attr(href)').get():
            item["phone"] = f"+39 {phone.split(':')[-1]}"
        if fax := response.css('.telephone-fax p:contains("Fax:")::text').get():
            item["extras"]["fax"] = f"+39 {fax.split(':')[-1].strip()}"

        hours = clean_strings(response.css(".orari *::text").getall())
        oh = OpeningHours()
        for day, hour in zip(hours[0::2], hours[1::2]):
            oh.add_ranges_from_string(
                f"{day} {hour}",
                days=DAYS_IT,
                named_day_ranges=NAMED_DAY_RANGES_IT,
                named_times=NAMED_TIMES_IT,
                closed=CLOSED_IT,
            )
        if oh:
            item["opening_hours"] = oh

        self.apply_payment_methods(response, item)
        self.apply_departments(response, item)

        item["street_address"] = item.pop("addr_full", None)
        yield item

    payment_methods = {
        "american express": PaymentMethods.AMERICAN_EXPRESS,
        "assegni": PaymentMethods.CHEQUE,
        "banco posta": PaymentMethods.BANCOPOSTA,
        "bancoposta": PaymentMethods.BANCOPOSTA,
        "bancomat": PaymentMethods.BANCOMAT,
        "bancomat pay": PaymentMethods.BANCOMAT,
        "pagobancomat": PaymentMethods.BANCOMAT,
        "carte di credito": PaymentMethods.CREDIT_CARDS,
        "diners": PaymentMethods.DINERS_CLUB,
        "maestro": PaymentMethods.MAESTRO,
        "mastercard": PaymentMethods.MASTER_CARD,
        "postepay": PaymentMethods.POSTEPAY,
        "satispay": PaymentMethods.SATISPAY,
        "visa": PaymentMethods.VISA,
        "visa electron": PaymentMethods.VISA_ELECTRON,
        "unicard": PaymentMethods.VISA_ELECTRON,
    }

    def apply_payment_methods(self, response, item):
        available_methods = clean_strings(
            response.xpath('//*[@data-component="relationStorePaymentCardsComponent"]//p/text()').getall()
        )
        apply_yes_no(PaymentMethods.CASH, item, True)
        for method in available_methods:
            if category := self.payment_methods.get(method):
                apply_yes_no(category, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/ignored_payment_method/{method}")

    known_departments = {
        "coop salute": dict(dispensing="no", **Categories.PHARMACY.value),
        "parafarmacia": dict(dispensing="no", **Categories.PHARMACY.value),
        "viaggi coop": Categories.SHOP_TRAVEL_AGENCY,
        "abbigliamento e calzature": {Sells.CLOTHES.value: "yes"},
        "abbigliamento": {Sells.CLOTHES.value: "yes"},
        "ottica coop": {Sells.EYEGLASSES.value: "yes", Sells.CONTACT_LENSES.value: "yes"},
        "ottica": {Sells.EYEGLASSES.value: "yes", Sells.CONTACT_LENSES.value: "yes"},
        "pet food e care": {Sells.PET_SUPPLIES.value: "yes"},
        "libri": {Sells.BOOKS.value: "yes"},
        "libreria": {Sells.BOOKS.value: "yes"},
        "gioielleria": {Sells.JEWELRY.value: "yes"},
        "elettrodomestici": {Sells.ELECTRONICS.value: "yes"},
        "edicola": {Sells.NEWSPAPERS.value: "yes"},
    }

    def apply_departments(self, response, item):
        departments = clean_strings(
            response.xpath('//*[@data-component="relationStoreDepartmentComponent"]//p/text()').getall()
        )
        for department in departments:
            if category := self.known_departments.get(department):
                apply_category(category, item)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/ignored_department/{department}")
