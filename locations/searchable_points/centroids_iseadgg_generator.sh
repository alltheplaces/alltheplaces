#!/usr/bin/env bash

# Clean up any old files from the previous execution
echo 'Cleaning up any old temporary files...'
rm -Rf iseadgg_gen 2>/dev/null

# Setup new temporary working directory
echo 'Setting up new temporary working directory...'
mkdir iseadgg_gen
cd iseadgg_gen

# Check out latest dggrid source code
echo 'Checking out latest DGGRID source code...'
git clone -b master --single-branch --depth 1 \
  https://github.com/sahrk/DGGRID.git dggrid_src

# Build dggrid software
echo 'Building DGGRID software...'
cd dggrid_src
mkdir build
cd build
cmake -DCMAKE_CXX_COMPILER='/usr/bin/g++' -DCMAKE_BUILD_TYPE=Release ..
make
cd ../../
ln -s dggrid_src/build/src/apps/dggrid/dggrid dggrid

# Download and extract combined country boundaries shapefile
echo 'Downloading and extracting combined country boundaries shapefile...'
curl -s -o ne_10m_admin_0_countries_lakes.zip \
  https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries_lakes.zip
unzip ne_10m_admin_0_countries_lakes.zip

# Generate a list of ISO 3166-1 alpha-2 country codes
echo 'Generating list of ISO 3166-1 alpha-2 country codes...'
ogrinfo -sql 'SELECT DISTINCT ISO_A2_EH FROM ne_10m_admin_0_countries_lakes' \
  ne_10m_admin_0_countries_lakes.shp \
  | grep -oP '(?<== )[A-Z]{2}' \
  | tr '[:upper:]' '[:lower:]' \
  | sort \
  > country_code_list.txt

# Iterate by country to generate country-specific boundary shapefiles
echo 'Generating country-specific boundary shapefiles...'
cat country_code_list.txt \
  | xargs -I 'COUNTRY_CODE' ogr2ogr \
    -dialect sqlite \
    -sql "SELECT ST_Union(geometry) AS geom FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2_EH='COUNTRY_CODE' GROUP BY ISO_A2_EH" \
    'COUNTRY_CODE'.shp \
    ne_10m_admin_0_countries_lakes.shp

# Setup ISEADGG centroids directory in ATP repository
echo 'Setting up ISEADGG centroids directory in ATP repository...'
cd ..
mkdir iseadgg 2>/dev/null
git add iseadgg/
cd iseadgg
git rm *_centroids_iseadgg_*km_radius.csv
cd ../iseadgg_gen

# FUNCTION: Generate ISEADGG centroid lists in CSV format for each country.
# $1 is the the minimum search radius in kilometres that the centroid list is
#    intended to support. This value is calculated as
#    CEILING(MAX_INTERNODE_SPACING/2) where MAX_INTERNODE_SPACING is taken
#    from Appendix D "Statistics for Some Preset ISEA DGGs", DGGRID Manual.
# $2 is the DGGRID "dggs_type" attribute defined in the DGGRID Manual and
#    requires a value of of "ISEA3H", "ISEA4H" or "ISEA43H".
# $3 is the DGGRID "dggs_num_aperture_4_res" attribute that is only used if $1
#    is set to "ISEA43H", otherwise it should be set to "0" and it will be
#    ignored. Refer to Appendix D "Statistics for Some Preset ISEA DGGs",
#    DGGRID Manual for permitted values.
# $4 is the DGGRID "dggs_res_spec" attribute that requires a value specified
#    in Appendix D "Statistics for Some Preset ISEA DGGs", DGGRID Manual.
generate_iseadgg_centroids() {
  echo "Generating ~$1km ISEADGG centroids for each country..."
  cat country_code_list.txt \
    | xargs -I 'COUNTRY_CODE' \
      bash -c "cat > COUNTRY_CODE_centroids_iseadgg_$1km_radius.meta <<-EOF
dggrid_operation GENERATE_GRID
dggs_type $2
dggs_num_aperture_4_res $3
dggs_res_spec $4
point_output_type TEXT
point_output_file_name COUNTRY_CODE_centroids_iseadgg_$1km_radius
clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files COUNTRY_CODE.shp
EOF"
  cat country_code_list.txt \
    | xargs -I 'COUNTRY_CODE' \
      ./dggrid "COUNTRY_CODE_centroids_iseadgg_$1km_radius.meta"
  cat country_code_list.txt \
    | xargs -I 'COUNTRY_CODE' \
      bash -c "sed '1s;^;id,longitude,latitude\n;' 'COUNTRY_CODE_centroids_iseadgg_$1km_radius.txt' > '../iseadgg/COUNTRY_CODE_centroids_iseadgg_$1km_radius.csv'"
  cat country_code_list.txt \
    | xargs -I 'COUNTRY_CODE' \
      git add "../iseadgg/COUNTRY_CODE_centroids_iseadgg_$1km_radius.csv"
}

# Generate ~24km ISEADGG centroids for each country, intended for use with
# APIs accepting a search radius >=25km or >15mi.
generate_iseadgg_centroids '24' 'ISEA43H' '2' '9'

# Generate ~48km ISEADGG centroids for each country, intended for use with
# APIs accepting a search radius >=50km or >=30mi.
generate_iseadgg_centroids '48' 'ISEA43H' '1' '8'

# Generate ~79km ISEADGG centroids for each country, intended for use with
# APIs accepting a search radius >=80km or >=50mi.
generate_iseadgg_centroids '79' 'ISEA43H' '1' '7'

# Generate ~94km ISEADGG centroids for each country, intended for use with
# APIs accepting a search radius >=100km or >=60mi.
generate_iseadgg_centroids '94' 'ISEA3H' '0' '7'

# Generate ~158km ISEADGG centroids for each country, intended for use with
# APIs accepting a search radius >=160km or >=100mi.
generate_iseadgg_centroids '158' 'ISEA43H' '4' '5'

# Generate ~315km ISEADGG centroids for each country, intended for use with
# APIs accepting a search radius >=315km or >=200mi.
generate_iseadgg_centroids '315' 'ISEA43H' '3' '4'

# Generate ~458km ISEADGG centroids for each country, intended for use with
# APIs accepting a search radius >=460km or >=285mi.
generate_iseadgg_centroids '458' 'ISEA3H' '0' '4'

# Remove temporary working directory
echo 'Cleaning up temporary working directory...'
cd ..
rm -Rf iseadgg_gen 2>/dev/null
