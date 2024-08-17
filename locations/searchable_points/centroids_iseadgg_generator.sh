#!/usr/bin/env bash

# Clean up any old files from the previous execution
echo 'Cleaning up any old temporary files...'
rm -Rf iseadgg_gen 2>/dev/null

# Setup new temporary working directory
echo 'Setting up new temporary working directory...'
mkdir iseadgg_gen
cd iseadgg_gen

# Check out and build latest dggrid
echo 'Checking out latest DGGRID source code...'
git clone -b master --single-branch --depth 1 https://github.com/sahrk/DGGRID.git dggrid_src
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
curl -s -o ne_10m_admin_0_countries_lakes.zip https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries_lakes.zip
unzip ne_10m_admin_0_countries_lakes.zip

# Iterate by country to generate country-specific boundary shapefiles
echo 'Generating country-specific boundary shapefiles...'
ogrinfo -sql 'SELECT DISTINCT ISO_A2 FROM ne_10m_admin_0_countries_lakes' ne_10m_admin_0_countries_lakes.shp | grep -oP '(?<== )[A-Z]{2}' | tr '[:upper:]' '[:lower:]' | sort > country_code_list.txt
cat country_code_list.txt | xargs -I '{}' ogr2ogr -sql "SELECT OGR_GEOMETRY AS GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='{}'" '{}'.shp ne_10m_admin_0_countries_lakes.shp

# Generate ~48km ISEADGG centroids
echo 'Generating ~48km ISEADGG centroids for each country...'
cat country_code_list.txt | xargs -I '{}' bash -c 'cat > {}_centroids_iseadgg_48km_radius.meta <<-EOF
dggrid_operation GENERATE_GRID
dggs_type ISEA43H
dggs_num_aperture_4_res 1
dggs_res_spec 8
point_output_type TEXT
point_output_file_name {}_centroids_iseadgg_48km_radius
clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files {}.shp
EOF'
cat country_code_list.txt | xargs -I '{}' ./dggrid '{}_centroids_iseadgg_48km_radius.meta'
cat country_code_list.txt | xargs -I '{}' bash -c 'sed "1s;^;id,longitude,latitude\n;" "{}_centroids_iseadgg_48km_radius.txt" > "../{}_centroids_iseadgg_48km_radius.csv"'

# Remove temporary working directory
echo 'Cleaning up temporary working directory...'
cd ..
rm -Rf iseadgg_gen 2>/dev/null
