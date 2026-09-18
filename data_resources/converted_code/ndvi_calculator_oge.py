import oge

# Initialize OGE
oge.initialize()
service = oge.Service()

# -----------------------
# Winter-season image
# -----------------------
winter_lc08 = service.getCoverage(
    coverageID="LC08_L1TP_119038_20230104_20230111_02_T1",
    productID="LC08_C02_L1"
)
winter_lc08_d = service.getProcess("Coverage.toFloat").execute(winter_lc08)

# -----------------------
# Summer-season image (placeholder, to be replaced later)
# -----------------------
summer_lc08 = service.getCoverage(
    coverageID="TODO_SUMMER_COVERAGE_ID",
    productID="LC08_C02_L1"
)
summer_lc08_d = service.getProcess("Coverage.toFloat").execute(summer_lc08)

# -----------------------
# Winter Landsat 8 bands
# -----------------------
winter_red = service.getProcess("Coverage.selectBands").execute(winter_lc08_d, ["B4"])
winter_green = service.getProcess("Coverage.selectBands").execute(winter_lc08_d, ["B3"])
winter_nir = service.getProcess("Coverage.selectBands").execute(winter_lc08_d, ["B5"])
winter_swir1 = service.getProcess("Coverage.selectBands").execute(winter_lc08_d, ["B6"])

# -----------------------
# Summer Landsat 8 bands
# -----------------------
summer_red = service.getProcess("Coverage.selectBands").execute(summer_lc08_d, ["B4"])
summer_green = service.getProcess("Coverage.selectBands").execute(summer_lc08_d, ["B3"])
summer_nir = service.getProcess("Coverage.selectBands").execute(summer_lc08_d, ["B5"])
summer_swir1 = service.getProcess("Coverage.selectBands").execute(summer_lc08_d, ["B6"])

# -----------------------
# 1. NDVI = (NIR - Red) / (NIR + Red)
# -----------------------
winter_ndvi_numerator = service.getProcess("Coverage.subtract").execute(winter_nir, winter_red)
winter_ndvi_denominator = service.getProcess("Coverage.add").execute(winter_nir, winter_red)
winter_ndvi = service.getProcess("Coverage.divide").execute(winter_ndvi_numerator, winter_ndvi_denominator)

summer_ndvi_numerator = service.getProcess("Coverage.subtract").execute(summer_nir, summer_red)
summer_ndvi_denominator = service.getProcess("Coverage.add").execute(summer_nir, summer_red)
summer_ndvi = service.getProcess("Coverage.divide").execute(summer_ndvi_numerator, summer_ndvi_denominator)

ndvi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["blue", "lightblue", "green", "yellow", "red"]
}

winter_ndvi.styles(ndvi_vis).getMap("Winter NDVI")
summer_ndvi.styles(ndvi_vis).getMap("Summer NDVI")

# -----------------------
# 2. GNDVI = (NIR - Green) / (NIR + Green)
# -----------------------
winter_gndvi_numerator = service.getProcess("Coverage.subtract").execute(winter_nir, winter_green)
winter_gndvi_denominator = service.getProcess("Coverage.add").execute(winter_nir, winter_green)
winter_gndvi = service.getProcess("Coverage.divide").execute(winter_gndvi_numerator, winter_gndvi_denominator)

summer_gndvi_numerator = service.getProcess("Coverage.subtract").execute(summer_nir, summer_green)
summer_gndvi_denominator = service.getProcess("Coverage.add").execute(summer_nir, summer_green)
summer_gndvi = service.getProcess("Coverage.divide").execute(summer_gndvi_numerator, summer_gndvi_denominator)

gndvi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["blue", "lightblue", "green", "yellow", "red"]
}

winter_gndvi.styles(gndvi_vis).getMap("Winter GNDVI")
summer_gndvi.styles(gndvi_vis).getMap("Summer GNDVI")

# -----------------------
# 3. NDMI = (NIR - SWIR1) / (NIR + SWIR1)
# -----------------------
winter_ndmi_numerator = service.getProcess("Coverage.subtract").execute(winter_nir, winter_swir1)
winter_ndmi_denominator = service.getProcess("Coverage.add").execute(winter_nir, winter_swir1)
winter_ndmi = service.getProcess("Coverage.divide").execute(winter_ndmi_numerator, winter_ndmi_denominator)

summer_ndmi_numerator = service.getProcess("Coverage.subtract").execute(summer_nir, summer_swir1)
summer_ndmi_denominator = service.getProcess("Coverage.add").execute(summer_nir, summer_swir1)
summer_ndmi = service.getProcess("Coverage.divide").execute(summer_ndmi_numerator, summer_ndmi_denominator)

ndmi_vis = {
    "min": -1,
    "max": 1,
    "palette": ["brown", "yellow", "lightgreen", "green", "darkgreen"]
}

winter_ndmi.styles(ndmi_vis).getMap("Winter NDMI")
summer_ndmi.styles(ndmi_vis).getMap("Summer NDMI")

# Set the map center
oge.mapclient.centerMap(120.5, 32.0, 9)
