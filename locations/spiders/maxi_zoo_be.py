from locations.spiders.maxi_zoo_fr import MaxiZooFRSpider


class MaxiZooBESpider(MaxiZooFRSpider):
    name = "maxi_zoo_be"
    api_key = "maxizooBE"
    website_format = "https://www.maxizoo.be/nl/stores/{}/"
