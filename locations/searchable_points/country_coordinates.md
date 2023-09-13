# country\_coordinates.json

This file contains coordinates for each country of the world that has an ISO 3166-1 alpha-2 code assigned.

Coordinates are obtained from a Wikidata query, and generally approximate a centroid of the largest landmass of a country, or centroid of multiple largest landmasses for countries with separate landmasses.

The data within this file is useful for spiders which query APIs that expect to be supplied a coordinate that is then reverse geocoded by the API into a country.

To update this list of coordinates, execute the following Wikidata query ([link](https://query.wikidata.org/#SELECT%20%3Fisocode%20%3Flon%20%3Flat%20WHERE%20%7B%0A%20%20%3Fcountry%20wdt%3AP297%20%3Fisocode.%0A%20%20%3Fcountry%20p%3AP625%20%5B%0A%20%20%20%20psv%3AP625%20%5B%0A%20%20%20%20%20%20wikibase%3AgeoLongitude%20%3Flon%3B%0A%20%20%20%20%20%20wikibase%3AgeoLatitude%20%3Flat%3B%0A%20%20%20%20%5D%0A%20%20%5D%0A%7D%0AORDER%20BY%20ASC%28%3Fisocode%29)) and download the result as a JSON file:

`SELECT ?isocode ?lon ?lat WHERE {
  ?country wdt:P297 ?isocode.
  ?country p:P625 [
    psv:P625 [
      wikibase:geoLongitude ?lon;
      wikibase:geoLatitude ?lat;
    ]
  ]
}
ORDER BY ASC(?isocode)`
