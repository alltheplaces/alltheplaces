from locations.spiders.sae_institute_au import SaeInstituteAUSpider


class SaeInstituteGBSpider(SaeInstituteAUSpider):
    name = "sae_institute_gb"
    start_urls = ["https://www.sae.edu/gbr/contact-us/"]
