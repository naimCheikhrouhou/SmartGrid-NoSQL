CASSANDRA_HOSTS = ["127.0.0.1"]
KEYSPACE = "smartgrid"
REDIS_HOST, REDIS_PORT = "127.0.0.1", 6379
MONGO_URI = "mongodb://127.0.0.1:27017"
MONGO_DB = "smartgrid"

# alert thresholds (used in Step 5)
VOLTAGE_MIN, VOLTAGE_MAX = 207.0, 253.0   # about ±10% of 230 V
POWER_MAX_KW = 8.0
