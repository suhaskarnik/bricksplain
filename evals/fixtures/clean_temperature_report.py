# Databricks notebook source
# MAGIC %md
# MAGIC ## Daily temperature summary
# MAGIC Reads one day of temperature readings and shows the minimum, maximum and mean per station.

# COMMAND ----------

dbutils.widgets.text("day", "2024-01-01")
day = dbutils.widgets.get("day")
MIN_VALID_C = -60.0
MAX_VALID_C = 60.0

# COMMAND ----------

readings = spark.table("weather.readings").filter(F.col("day") == day)
valid = readings.filter(F.col("temp_c").between(MIN_VALID_C, MAX_VALID_C))
rejected = readings.count() - valid.count()
assert rejected == 0, f"{rejected} readings outside {MIN_VALID_C}..{MAX_VALID_C}"

# COMMAND ----------

summary = valid.groupBy("station").agg(
    F.min("temp_c").alias("min_c"),
    F.max("temp_c").alias("max_c"),
    F.mean("temp_c").alias("mean_c"),
)
display(summary.orderBy("station"))
