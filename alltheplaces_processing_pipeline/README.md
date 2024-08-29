# AllThePlaces Data Processing

## Introduction

The AllThePlaces Data Processing project is designed to ensure that All The Places (ATP) data is consistently stored, up-to-date, accurate, and comprehensive. This data is essential for Points of Interest (POI) applications, providing valuable insights and analysis. The project involves automated steps to fetch, process, and manage ATP data, ensuring its reliability and completeness.

## Project Overview

### Objective

The primary goal of the ATP Data Processing project is to maintain high-quality ATP data by automating the extraction, transformation, and validation processes. This ensures that the data remains relevant and usable for various POI-related applications.

### Key Components

1. **Data Extraction**: Automatically retrieve the latest ATP data from the AllThePlaces API.
2. **Data Processing**: Convert the extracted data into a format suitable for POI applications.
3. **Spider Management**: Identify and manage broken or missing spiders within the ATP dataset.
4. **Spider Configuration**: Configure and run spiders on the Zyte Scrapy Cloud platform to fill gaps in the data.

## Processing Stages

### 1. Retrieve the Latest Dataset

- Fetch the most recent ATP data from the AllThePlaces API.

### 2. Process ATP Data

- Save the ATP data in a ZIP file to Google Cloud Storage (GCS).
- Unzip the file to access individual GeoJSON files.
- Convert each GeoJSON file into JSON Lines format, tailored specifically to the ATP data structure.
- **Output**: The processed ATP data files are stored in a specified GCS bucket as JSON Lines.

### 3. Identify Broken or Missing Spiders

- List all spider names from the reference GitHub repository. The spider names are derived from their corresponding Python file names.
- Compare the list of all spiders with the list of spiders that returned non-empty data in the current run.
- Identify spiders that are missing or broken (those returning empty data).
- **Output**: A list of spiders that are missing in alltheplaces data.

### 4. Configure Spiders on Zyte Scrapy Cloud

- Trigger the "[Run Selected Spiders](https://github.com/huq-industries/alltheplaces/blob/master/.github/workflows/run-selected-spiders.yml)" GitHub Action workflow to run missing or broken spiders on Zyte Scrapy Cloud.
- The workflow sets up the environment, validates the spiders, and schedules them for execution using the `shub` command.
- Logs the results of successful, failed, and invalid spider runs.
- **Output**: Successfully executed spiders, ensuring a complete and comprehensive ATP dataset.

## Project Maintenance

The ATP spiders and configurations are maintained in a dedicated GitHub repository at [huq-induestries/alltheplaces](https://github.com/huq-industries/alltheplaces). This repository is synced daily with the main [AllThePlaces repository](https://github.com/alltheplaces/alltheplaces) also using github workflows. Each sync ensures that the latest spider configurations are deployed to the Zyte Scrapy Cloud platform under the `alltheplaces-prod` project also using github workflows. This project is then used to run the remaining spiders in the last step.

The ATP spiders and configurations are maintained in a dedicated GitHub repository at [huq-induestries/alltheplaces](https://github.com/huq-industries/alltheplaces). This repository is synced daily with the main [AllThePlaces repository](https://github.com/alltheplaces/alltheplaces) through [GitHub workflows](https://github.com/huq-industries/alltheplaces/tree/master/.github/workflows). These workflows also deploy the latest spider configurations to the Zyte Scrapy Cloud platform under the alltheplaces-prod project. This setup ensures that the most up-to-date spiders are available for running in the final step of the data processing pipeline.


## Setup

To run the ATP Data Processing project, you need to have the following configurations:

- **GITHUB_TOKEN**: Required to access the GitHub repository, retrieve the list of spiders, and trigger the workflow after spider synchronization.
- **SCRAPYCLOUD_API_KEY**: Needed to authenticate and run spiders on the Zyte Scrapy Cloud platform.
- **SCRAPYCLOUD_PROJECT_ID**: Specifies the project ID on Zyte Scrapy Cloud where the spiders will be executed.
- **GCP_CONN_ID**:  Specifies the connection ID for Google Cloud Platform within Airflow.

> **Note:** If you are using a Composer environment, ensure that you allocate at least 3 GB of RAM to process the All The Places data in memory effectively.



