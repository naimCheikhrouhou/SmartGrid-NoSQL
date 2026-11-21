import random
from cassandra.cluster import Cluster
from pymongo import MongoClient, ASCENDING, DESCENDING
from config import *

# ---------- Cassandra ----------
cluster = Cluster(CASSANDRA_HOSTS) #connect to cassandra container
session = cluster.connect()
session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
""")
session.set_keyspace(KEYSPACE)
session.execute("""
    CREATE TABLE IF NOT EXISTS readings_by_meter_day (
        meter_id    text,
        day         date,
        ts          timestamp,
        voltage     double,
        current     double,
        power_kw    double,
        energy_kwh  double,
        PRIMARY KEY ((meter_id, day), ts)
    ) WITH CLUSTERING ORDER BY (ts DESC)
""")
print("Cassandra: keyspace + table ready")

# ---------- MongoDB ----------
mongo = MongoClient(MONGO_URI)[MONGO_DB]
mongo.meters.drop()
mongo.meters.create_index([("meter_id", ASCENDING)], unique=True)
mongo.alerts.create_index([("meter_id", ASCENDING), ("ts", DESCENDING)])

zones = ["North", "South", "East", "West", "Center"]
docs = []
for i in range(1, 21):
    mid = f"M{i:03d}"
    if i <= 15:
        docs.append({
            "meter_id": mid, "type": "consumer",
            "zone": random.choice(zones),
            "tariff": random.choice(["residential", "commercial"]),
            "contract_kva": random.choice([6, 9, 12]),
        })
    else:
        cap = random.choice([3, 5, 8])
        docs.append({
            "meter_id": mid, "type": "solar",
            "zone": random.choice(zones),
            "panel_capacity_kw": cap,
            "inverter": {"brand": random.choice(["SMA", "Huawei", "Fronius"]),
                         "efficiency": round(random.uniform(0.94, 0.98), 3)},
        })
mongo.meters.insert_many(docs)
print(f"MongoDB: {len(docs)} meters seeded")