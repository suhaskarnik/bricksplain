# Databricks notebook source
# MAGIC %md
# MAGIC ## Turbine failure features
# MAGIC Builds a feature table from vibration readings and trains a failure model.

# COMMAND ----------

dbutils.widgets.text("seed", "42")
dbutils.widgets.text("window_h", "24")
seed = int(dbutils.widgets.get("seed"))
window_h = int(dbutils.widgets.get("window_h"))
LABEL = "failed_within_7d"
FEATURES = ["vib_mean", "vib_max", "temp_mean", "hours_since_service", LABEL]

# COMMAND ----------

# MAGIC %run ../shared/ml_helpers

# COMMAND ----------

raw = spark.read.format("delta").load("/mnt/iot/vibration_readings")
raw = raw.filter(F.col("quality_flag") == "OK")
agg = raw.groupBy("turbine_id").agg(
    F.mean("vibration").alias("vib_mean"),
    F.max("vibration").alias("vib_max"),
    F.mean("temp_c").alias("temp_mean"),
)
feat = agg.join(spark.table("iot.service_log"), "turbine_id", "left")

# COMMAND ----------

pdf = feat.toPandas()
scaler = StandardScaler().fit(pdf[FEATURES])
pdf[FEATURES] = scaler.transform(pdf[FEATURES])
train, test = train_test_split(pdf, test_size=0.2)

# COMMAND ----------

model = GradientBoostingClassifier().fit(train[FEATURES], train[LABEL])
print(model.score(test[FEATURES], test[LABEL]))
# model = GradientBoostingClassifier(n_estimators=500, learning_rate=0.05)

# COMMAND ----------

out = spark.createDataFrame(pdf)
out.write.format("delta").mode("overwrite").saveAsTable("iot.turbine_features")
