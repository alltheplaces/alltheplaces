import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature


class LandiCHSpider(SitemapSpider):
    name = "landi_ch"
    allowed_domains = ["www.landi.ch"]
    sitemap_urls = ["https://www.landi.ch/de/sitemap.xml"]
    sitemap_follow = ["/de/"]
    sitemap_rules = [(r"https://www\.landi\.ch/places/de/", "parse")]
    categories = {
        "2": Categories.SHOP_MOTORCYCLE,
        "auto": Categories.SHOP_CAR_REPAIR,
        "autohilfe": Categories.SHOP_CAR_REPAIR,
        "automobile": Categories.SHOP_CAR_REPAIR,
        "autotechnik": Categories.SHOP_CAR_REPAIR,
        "bikecenter": Categories.SHOP_MOTORCYCLE,
        "bikes": Categories.SHOP_MOTORCYCLE,
        "bimoto": Categories.SHOP_MOTORCYCLE_REPAIR,
        "cycles": Categories.SHOP_MOTORCYCLE,
        "fahrzeugtechnik": Categories.SHOP_CAR_REPAIR,
        "garage": Categories.SHOP_CAR_REPAIR,
        "laden": Categories.SHOP_SUPERMARKET,
        "landgarage": Categories.SHOP_CAR_REPAIR,
        "landi": Categories.SHOP_COUNTRY_STORE,
        "mofag": Categories.SHOP_MOTORCYCLE,
        "moto": Categories.SHOP_MOTORCYCLE,
        "motobene": Categories.SHOP_MOTORCYCLE_REPAIR,
        "motobike": Categories.SHOP_MOTORCYCLE,
        "motopower": Categories.SHOP_MOTORCYCLE,
        "motorcycles": Categories.SHOP_MOTORCYCLE,
        "motorrad": Categories.SHOP_MOTORCYCLE,
        "motos": Categories.SHOP_MOTORCYCLE,
        "motoshop": Categories.SHOP_MOTORCYCLE,
        "pneu": Categories.SHOP_CAR_REPAIR,
        "probike": Categories.SHOP_MOTORCYCLE,
        "rad": Categories.SHOP_MOTORCYCLE,
        "reincar": Categories.SHOP_CAR_REPAIR,
        "roues": Categories.SHOP_MOTORCYCLE,
        "schlossgarage": Categories.SHOP_CAR_REPAIR,
        "toeffklinik": Categories.SHOP_MOTORCYCLE_REPAIR,
        "zweirad": Categories.SHOP_MOTORCYCLE,
        "zweiradtechnik": Categories.SHOP_MOTORCYCLE_REPAIR,
        "zweiradwerkstatt": Categories.SHOP_MOTORCYCLE_REPAIR,
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 60}

    def parse(self, response):
        lat, lon = self.parse_lat_lon(response)
        props = {
            "email": self.parse_email(response),
            "fax": self.parse_fax(response),
            "lat": lat,
            "lon": lon,
            "image": self.parse_image(response),
            "opening_hours": self.parse_opening_hours(response),
            "phone": self.parse_phone(response),
            "ref": response.url.split("/")[-1],
        }
        props.update(self.parse_name_brand(response))
        props.update(self.parse_address(response))
        props.update(self.parse_website(response))
        extras = props["extras"] = self.parse_service(response)
        for key in ["fax", "source:website"]:
            extras[key] = props.pop(key, "")
        extras = {k: v for (k, v) in extras.items() if v}
        item = Feature(**props)
        self.set_category(item)
        yield item

    @staticmethod
    def parse_address(response):
        addr = {"country": "CH"}
        divs = response.css("div.place-info").xpath("div/text()").getall()
        divs = list(filter(None, [d.strip() for d in divs]))
        if len(divs) >= 2:
            addr["street_address"] = " ".join(divs[-2].split())
        if len(divs) >= 1:
            addr["postcode"], addr["city"] = divs[-1].split(" ", 1)
        return addr

    @staticmethod
    def parse_email(response):
        email = None
        if c := response.css("div.place-contacts"):
            email = c.xpath('//dt[normalize-space()="E-Mail:"]/following-sibling::dd/a/@href').get()
        return email.strip().removeprefix("mailto:") if email else None

    @staticmethod
    def parse_fax(response):
        fax = None
        if c := response.css("div.place-contacts"):
            fax = c.xpath('//dt[normalize-space()="Fax:"]/following-sibling::dd/text()').get()
        return fax.strip() if fax else None

    @staticmethod
    def parse_image(response):
        if img := response.css("img.place-image").xpath("@src").get():
            return response.urljoin(img.split("?")[0])
        else:
            return None

    @staticmethod
    def parse_lat_lon(response):
        match = re.search(r'ref="https://maps.google.com\?daddr=([\d\.]+),([\d\.]+)"', response.text)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        else:
            return (None, None)

    @staticmethod
    def parse_name_brand(response):
        if response.url.split("/")[-1].startswith("landi-"):
            return {
                "brand": "Landi",
                "brand_wikidata": "Q1803010",
                "name": "Landi",
            }
        return {
            "name": response.css("div.place-info").xpath("div/strong/text()").get(),
        }

    @staticmethod
    def parse_opening_hours(response):
        hours = OpeningHours()
        h = response.css(".place-openinghours").xpath("dl[1]").get()
        for entry in h.split("<dt>"):
            if day := DAYS_DE.get(entry.split("</dt>")[0]):
                for open_time, close_time in re.findall(r"<dd>(\d\d:\d\d) - (\d\d:\d\d)</dd>", entry):
                    hours.add_range(day, open_time, close_time)
        return hours.as_opening_hours()

    @staticmethod
    def parse_phone(response):
        ph = response.css("span.custom-icon-phone").xpath("../@href").get()
        return ph.removeprefix("tel:") if ph else None

    @staticmethod
    def parse_service(response):
        s = {}
        text = response.text
        if 'alt="icon-Hauslieferdienst"' in text:
            s["delivery"] = "yes"
        if 'alt="icon-Rasenm&#228;her-Service"' in text:
            s["service:lawnmower:repair"] = "yes"
        if 'alt="icon-Roller-Service"' in text:
            s["service:scooter:repair"] = "yes"
        if 'alt="icon-Velo- und E-Bike-Service"' in text:
            s["service:bicycle:repair"] = "yes"
        return s

    @staticmethod
    def parse_website(response):
        if url := response.css("span.custom-icon-world").xpath("../@href").get():
            return {"website": url, "source:website": response.url}
        else:
            return {"website": response.url}

    def set_category(self, item):
        for word in item["ref"].lower().split("-"):
            if cat := self.categories.get(word):
                apply_category(cat, item)
                return
        apply_category(Categories.SHOP_DOITYOURSELF, item)
