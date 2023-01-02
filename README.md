![Vinícius Mesquita / DALEE - theropod, jurassic landscape, digital art, hight quality](Logo.png)

# ${\color{red}T} im {\color{red}e}\ Se {\color{red}r} ies\ Extracti {\color{red}o} n\ for\ {\color{red}Po} lygonal\ {\color{red}Da} ta$

### Name
- T(h)eroPoDa - Time Series Extraction for Polygonal Data ⬛

### Description
- Toolkit created to extract Time Series information from Sentinel 2 🛰 data stored in Earth Engine [![image](https://user-images.githubusercontent.com/13785909/209228496-9fe31adc-a7cb-47c3-b476-64d82541f139.png)](https://earthengine.google.com/)

### Author
- Vinícius Vieira Mesquita - vieiramesquita@gmail.com

### Version
- 1.0.5

### How to use

- At this version of TheroPoDa (1.0.5), you could extract a series of NDVI data from Sentinel 2 for a Feature Collection of polygons simplily by adjusting some variables at the end of the Google Colab code below:

| variable      | usage                                               | example  |
|:-------------:|:--------------------------------------------------: |:---------|
| asset         | Choosed Earth Engine Vector Asset                   | users/vieiramesquita/LAPIG_FieldSamples/lapig_goias_fieldwork_2022_50m |
| id_field      | Vector column used as ID (use unique identifiers!) | ID_POINTS |
| output_name   | Output filename                                     | LAPIG_Pasture_S2_NDVI_Monitoring_FieldWork.csv |


[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vieiramesquita/TheroPoDa/blob/main/TheroPoDa.ipynb)

### Roadmap

- Implement arguments to choose other zonal reducers (i.e. median, percentile, min, max, variance, etc.)
- Implement arguments to choose other satellite data series (i.e. Landsat series)
- Implement a visualization of the processed data (or samples of it)
