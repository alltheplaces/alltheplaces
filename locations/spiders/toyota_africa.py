import re

from chompjs import parse_js_object
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.hours import DAYS_ES, DAYS_FR, DAYS_PT, DELIMITERS_ES, DELIMITERS_FR, DELIMITERS_PT, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES

# See https://www.toyota-africa.com/countries
# Many are a common format, not including the following:
# Algeria, Angola, Burundi,Cabo Verde, Djibouti, Ghana, Egypt, Ethiopia, Gabon, Libya, Mayotte, Malawi
# Mauritius, Morocco, https://toyotanigeria.com/, Reunion, Seychelles, Somalia, Sudan, Tanzania, Tunisia, Zambia

# South Africa, Lesotho, Namibia, Botswana, Eswatini - all under toyota_sacu


class ToyotaAfricaSpider(CrawlSpider):
    name = "toyota_africa"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.toyota.bj/fr/concession/toyota-benin-cfao-motors",
        "https://www.toyota.bf/fr/concession/toyota-burkina-faso-cfao-motors",
        "https://toyota.cami-cfao.com/fr/concession/toyota-cameroun-cami",
        "https://toyota.cfaomotors-centrafrique.com/fr/concession/toyota-centrafrique-cfao-motors",
        "https://toyota.cfaomotors-tchad.com/fr/concession/toyota-tchad-cfao-motors",
        "https://www.toyota.ci/fr/concession/toyota-cote-divoire-cfao-motors"
        "https://www.toyota.cg/fr/concession/toyota-congo-cfao-motors",
        "https://www.toyota-rdc.com/fr/concession/toyota-rdc-cfao-motors",
        "https://toyota.cfaomotors-guineeequatoriale.com/fr/concession/toyota-guinee-equatoriale-cfao-motors",
        "https://www.toyota.gm/en/dealership/toyota-gambia-cfao-motors",
        "https://toyota.cfaomotors-guinee.com/fr/concession/toyota-guinee-cfao-motors",
        "https://toyota.cfaomotors-guineebissau.com/fr/concession/toyota-guinee-bissau-cfao-motors",
        "https://www.toyotakenya.ke/en/dealership/toyota-kenya",
        "https://toyota.cica-motors-liberia.com/en/dealership/toyota-liberia-cica-motors",
        "https://www.toyota-sicam.mg/fr/concession/toyota-madagascar-sicam",
        "https://toyota.cfaomotors-mali.com/fr/concession/toyota-mali-cfao-motors",
        "https://www.toyota-mauritanie.com/fr/concession/toyota-mauritanie-cmda",
        "https://www.toyota.co.mz/pt/concessao/toyota-mocambique",
        "https://toyota.cfaomotors-niger.com/fr/concession/toyota-niger-cfao-motors",
        "https://www.toyotabycfao.ng/en/dealership",
        "https://www.toyotarwanda.com/en/dealership/toyota-rwanda",
        "https://www.toyota.sn/fr/concession/toyota-senegal-cfao-motors",
        "https://toyota.cica-motors-sierraleone.com.sl/en/dealership/toyota-sierra-leone-cica-motors",
        "https://www.toyota.tg/fr/concession/toyota-togo-cfao-motors",
        "https://www.toyota.co.ug/en/dealership/toyota-uganda",
        "https://www.toyota.co.zw/en/dealership/toyota-zimbabwe",
    ]
    allowed_domains = [
        "toyota.bj",
        "toyota.bf",
        "toyota.cami-cfao.com",
        "toyota.cfaomotors-centrafrique.com",
        "toyota.cfaomotors-tchad.com",
        "toyota.ci",
        "toyota.cg",
        "toyota-rdc.com",
        "toyota.cfaomotors-guineeequatoriale.com",
        "toyota.gm",
        "toyota.cfaomotors-guinee.com",
        "toyota.cfaomotors-guineebissau.com",
        "toyotakenya.ke",
        "toyota.cica-motors-liberia.com",
        "toyota-sicam.mg",
        "toyota.cfaomotors-mali.com",
        "toyota-mauritanie.com",
        "toyota.co.mz",
        "toyota.cfaomotors-niger.com",
        "toyotabycfao.ng",
        "toyotarwanda.com",
        "toyota.sn",
        "toyota.cica-motors-sierraleone.com.sl",
        "toyota.tg",
        "toyota.co.ug",
        "toyota.co.zw",
    ]
    rules = [
        Rule(LinkExtractor(allow=r".*\/(dealership|concession|concessao)\/toyota[-\w]+?\/.+$"), callback="parse"),
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.toyotabycfao\.ng\/en\/dealership\/toyota-[-\w]+$"), callback="parse"
        ),
    ]
    no_refs = True

    def parse(self, response):
        item = Feature()
        item["name"] = response.xpath('.//div[@id="dealership"]/.//h2/text()').get()

        # Drop authorised mechanics
        if (
            not item["name"].lower().startswith("toyota")
            and not item["name"].lower().startswith("cfao")
            and not item["name"].lower().startswith("glmc")
        ):
            return

        item["phone"] = response.xpath('.//div[@class="contact-info"]/.//a[contains(@href, "tel")]/@href').get()
        item["addr_full"] = clean_address(response.xpath('.//div[@class="location-info"]/div/text()').getall())
        item["website"] = response.url

        extract_google_position(item, response)
        if item.get("lat") is None and item.get("lon") is None:
            item["lat"], item["lon"] = parse_js_object(
                response.xpath('.//script[contains(text(), "var map_markers")]/text()').get()
            )[0][1:3]

        item["opening_hours"] = OpeningHours()
        time_string = " ".join(
            response.xpath('.//div[@class="concession-schedules"]/div[@class="item"]/text()').getall()
        )
        if "/en/" in response.url:
            time_string = time_string.replace(": from", " ")
            time_string = re.sub(r"(\d{1,2})h(\d\d)", r"\1:\2", time_string)
            time_string = re.sub(r"(\d{1,2})h(?!\d)", r"\1:00", time_string)
            item["opening_hours"].add_ranges_from_string(time_string)
        elif "toyota.cfaomotors-guineeequatoriale.com" in response.url:
            time_string = time_string.replace(" y ", ", ")
            time_string = time_string.replace(" de ", " ")
            item["opening_hours"].add_ranges_from_string(time_string, days=DAYS_ES, delimiters=DELIMITERS_ES)
        elif "/pt/" in response.url or "toyota.cfaomotors-guineebissau.com" in response.url:
            time_string = time_string.replace(" e ", ", ")
            time_string = time_string.replace(" das ", " ")
            time_string = re.sub(r"(\d)\s\/\s(\d)", r"\1 - \2", time_string)
            time_string = re.sub(r"(\d{1,2})h(\d\d)", r"\1:\2", time_string)
            time_string = re.sub(r"(\d{1,2})h(?!\d)", r"\1:00", time_string)
            item["opening_hours"].add_ranges_from_string(time_string, days=DAYS_PT, delimiters=DELIMITERS_PT)
        elif "/fr/" in response.url:
            time_string = time_string.replace(" et ", ", ")
            time_string = time_string.replace(",,", ",")
            time_string = re.sub(r"(\d)\s\/\s(\d)", r"\1 - \2", time_string)
            time_string = time_string.replace("/", " ")
            time_string = re.sub(r"(\d{1,2})h(\d\d)", r"\1:\2", time_string)
            time_string = re.sub(r"(\d{1,2})h(?!\d)", r"\1:00", time_string)
            time_string = time_string.replace(" de ", " ")
            item["opening_hours"].add_ranges_from_string(time_string, days=DAYS_FR, delimiters=DELIMITERS_FR)
        yield item
