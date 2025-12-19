from enum import Enum


class Licenses(Enum):
    CC0 = {
        "license": "Creative Commons Zero",
        "license:website": "https://creativecommons.org/publicdomain/zero/1.0/",
        "license:wikidata": "Q6938433",
        "attribution": "optional",
    }
    CC4 = {
        "license": "Creative Commons Attribution 4.0 International",
        "license:website": "http://creativecommons.org/licenses/by/4.0/",
        "license:wikidata": "Q20007257",
        "attribution": "required",
    }
    GB_OGLv3 = {
        "license": "Open Government Licence v3.0",
        "license:website": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "license:wikidata": "Q99891702",
        "attribution": "required",
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0.",
        "use:commercial": "permit",
    }
