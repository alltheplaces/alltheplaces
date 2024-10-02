from locations.spiders.sae_institute_au import SaeInstitueAUSpider


class SaeInstituteUKSpider(SaeInstitueAUSpider):
    name = "sae_institute_uk"
    start_urls = ["https://www.sae.edu/gbr/contact-us/"]
