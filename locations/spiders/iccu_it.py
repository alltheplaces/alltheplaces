import io
import json
import re
import zipfile

import phonenumbers as pn

from locations.categories import Categories, apply_category
from locations.items import set_social_media
from locations.json_blob_spider import JSONBlobSpider


class IccuITSpider(JSONBlobSpider):
    name = "iccu_it"
    allowed_domains = ["opendata.anagrafe.iccu.sbn.it"]
    start_urls = ["https://opendata.anagrafe.iccu.sbn.it/opendata.zip"]
    countries = ["it"]

    dataset_attributes = {
        "attribution": "not required",
        "contact:email": "ic-cu.anagrafe@beniculturali.it",
        "license": "CC0",
        "license:website": "https://creativecommons.org/publicdomain/zero/1.0/deed.it",
        "license:wikidata": "Q6938433",
        "use:commercial": "yes",
        "use:openstreetmap": "yes",
        "website": "https://anagrafe.iccu.sbn.it/it/open-data/",
    }

    item_attributes = {
        "country": "IT",
        "extras": Categories.LIBRARY.value,
    }

    def extract_json(self, response):
        with zipfile.ZipFile(io.BytesIO(response.body)) as feed_zip:
            with feed_zip.open("biblioteche.json") as feed_file:
                biblioteche = json.load(feed_file)["biblioteche"]
        return filter(IccuITSpider.filter_library, biblioteche)

    @staticmethod
    def filter_library(library):
        stato = library["stato-registrazione"]
        return stato is None or not (
            stato in ["Biblioteca non più esistente", "Biblioteca non censita"]
            or stato.startswith("Altri istituti")
            or stato.startswith("Biblioteca confluita")
        )

    def pre_process_data(self, feature: dict) -> None:
        addr = feature.pop("indirizzo")
        feature["indirizzo"] = (addr.get("via-piazza") or "").strip()
        if frazione := addr.get("frazione"):
            feature["citta"] = frazione
        else:
            feature["comune"] = addr["comune"]["nome"]
        feature["provincia"] = addr["provincia"]["nome"]
        if coords := addr.get("coordinate"):
            feature["latitude"] = coords[0]
            feature["longitude"] = coords[1]
        feature["cap"] = addr["cap"]
        feature["nome"] = feature["denominazioni"].pop("ufficiale").strip()

    regex_for_ministero_cleanup = re.compile(
        r"^Ministero\s*(?:"
        + r"|".join(
            [
                r"dell[’']istruzione(?: e del merito|(?:,? dell[’']universit(?:à|a'))? e della ricerca)?",
                r"della cultura",
                r"della difesa",
                r"della giustizia",
                r"dell[’']economia e delle finanze",
                r"dell[’']interno",
            ]
        )
        + r")\s*[\\.,-]\s*(.+)",
        flags=re.I,
    )

    def post_process_item(self, item, response, location: dict):
        extras = item["extras"]
        if "archivio" in item["name"].lower():
            extras["amenity"] = "archive"

        if ente := (location.get("ente") or "").strip():
            ente = re.sub(self.regex_for_ministero_cleanup, r"\1", ente)
            item["operator"] = ente

        for ref, val in location["codici-identificativi"].items():
            if val:
                extras[f"ref:{ref}"] = val
        item["ref"] = extras["ref:isil"]

        extras["official_name"] = item["name"]
        for name in location["denominazioni"]["alternative"]:
            if name := name.strip():
                apply_category({"alt_name": name}, item)
        for name in location["denominazioni"]["precedenti"]:
            if name := name.strip():
                apply_category({"old_name": name}, item)

        extras.update(
            {
                "access": "permit" if location["accesso"]["riservato"] else "yes",
                "wheelchair": "yes" if location["accesso"]["portatori-handicap"] else "no",
            }
        )
        if updated := location.get("data-aggiornamento"):
            extras["source:iccu:updated"] = updated

        self.add_contacts(item, location)

        yield item

    def add_contacts(self, item, location: dict):
        contatti = location["contatti"]
        if len(contatti) == 0:
            return
        for contact in contatti:
            self.add_contact(item, contact)

    contact_match = {
        "telex_value": re.compile(r"\d{1,6}(\s*[A-Z].+)?$", flags=re.I),
        "pec_value": re.compile(
            r".+@[a-z0-9\.-]*(pec|legalmail|(posta)?cert(ificata)?)[a-z0-9\.-]*\\.[a-z0-9\.-]+$", flags=re.I
        ),
        "pec_alt_value": re.compile(r"[^@]*pec[^@]*@[a-z0-9\.-]+\.[a-z0-9\.-]+$", flags=re.I),
        "mail_value": re.compile(r"^.+@.+$", flags=re.I),
        "ip_urls": re.compile(r"^(https?://)?([\d]{1,3}[\./]?){4}/", flags=re.I),
        "common_urls": re.compile(r"^(http|www|[^/]+.(it|eu|com|org|net|site)(/|$))", flags=re.I),
        "facebook_url": re.compile(r"^(?:@|(?:https?://)?(?:[^\.]+\.)?facebook\.com/+)([^?]+)(?:\?.*)?$", flags=re.I),
        "instagram_url": re.compile(r"^(?:@|(?:https?://)?(?:www\.)?instagram\.com/+)([^?/]+)(?:/|\?)?.*$", flags=re.I),
        "twitter_url": re.compile(r"^(?:@|(?:https?://)?(?:www\.)?(?:twitter|x)\.com/+)([^?/]+)(?:/|\?)?.*$", flags=re.I),
        "phone_value": re.compile(r"^(\+39|3|0)[\d /-]{6,26}"),
    }

    def add_contact(self, item, contact):
        valore = (contact["valore"] or "").strip(';:" \t(\n')
        tipo = (contact["tipo"] or "").strip()
        note = (contact["note"] or "").strip()

        if not valore:
            return
        if tipo == "Telex" or self.contact_match["telex_value"].match(valore):
            return

        if self.add_mail(item, valore):
            return
        if self.add_url(item, tipo, valore, note):
            return
        if self.add_phone(item, tipo, valore):
            return
        self.crawler.stats.inc_value(f"atp/{self.name}/unknown_contact_values")


    def add_mail(self, item, valore):
        # email and PEC (italian certified email)
        if self.contact_match["pec_value"].match(valore) or self.contact_match["pec_alt_value"].match(valore):
            apply_category({"contact:pec": valore}, item)
            return True
        if self.contact_match["mail_value"].match(valore):
            if item["email"]:
                apply_category({"contact:email": valore}, item)
            else:
                item["email"] = valore
            return True
        return False

    def add_url(self, item, tipo, valore, note):
        # urls and social media
        valore = valore.replace(r"h+t+p(s)?[;:]/+\s*", r"http\1://")
        if self.contact_match["ip_urls"].match(valore):
            return True # avoid urls that are IPs
        if self.contact_match["common_urls"].match(valore):
            tipo = "website"
        if self.contact_match["facebook_url"].match(valore):
            if valore.startswith("@") and "facebook" not in note.lower():
                pass
            else:
                valore = self.contact_match["facebook_url"].sub(r"https://www.facebook.com/\1", valore)
                set_social_media(item, "facebook", valore)
                return True
        if self.contact_match["instagram_url"].match(valore):
            if "/invites/contact" in valore.lower():
                return  # not usable instagram links
            if valore.startswith("@") and "instagram" not in note.lower():
                pass
            else:
                valore = self.contact_match["instagram_url"].sub(r"https://www.instagram.com/\1", valore)
                set_social_media(item, "instagram", valore)
                return True
        if self.contact_match["twitter_url"].match(valore):
            if valore.startswith("@") and "instagram" not in note.lower():
                pass
            else:
                valore = self.contact_match["twitter_url"].sub(r"https://x.com/\1", valore)
                set_social_media(item, "twitter", valore)
                return True
        if tipo == "website":
            if item["website"]:
                apply_category({"contact:website": valore}, item)
            else:
                item["website"] = valore
            return True
        return False

    def add_phone(self, item, tipo, valore):
        # phone and fax
        valore = valore.replace(r"^(\+39\s*)?(\+|00)\s*3\s*9[\.:;\s\)]*", "+39 ")
        if not self.contact_match["phone_value"].match(valore):
            return False
        if tipo != "Fax" and not valore.endswith("fax"):
            tipo = "phone"
        else:
            tipo = "fax"
        valore = valore.replace(r"[\.\s\(\)]", "").replace(r"(int(erno)?|digitare|fax)\d*$", "")

        if valore.endswith("omune"):
            # some phone/fax numbers are not for the library, but for the townhall
            return True
        try:
            valore = pn.format_number(pn.parse(valore, "IT"), pn.PhoneNumberFormat.INTERNATIONAL)
        except pn.phonenumberutil.NumberParseException:
            # avoid formatting and leave to people interpret it
            self.crawler.stats.inc_value(f"atp/{self.name}/invalid_phone_number")
        if tipo == "phone" and not item[tipo]:
            item[tipo] = valore
        else:
            apply_category({f"contact:{tipo}": valore}, item)
