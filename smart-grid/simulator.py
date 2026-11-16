import math, random, time, argparse
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from config import *


class MeterSim:
    def __init__(self, doc):
        self.id = doc["meter_id"]
        self.type = doc["type"]
        if self.type == "solar":
            self.peak_kw = doc["panel_capacity_kw"] * doc["inverter"]["efficiency"]
        else:
            self.peak_kw = doc["contract_kva"] * 0.5
        self.energy_kwh = 0.0  # cumulative counter, like a real meter

    def _power(self, ts):
        h = ts.hour + ts.minute / 60 + ts.second / 3600
        if self.type == "solar":
            if 6 <= h <= 19:
                bell = math.sin(math.pi * (h - 6) / 13) ** 1.5
                return max(0.0, bell * self.peak_kw * random.uniform(0.7, 1.0))
            return 0.0
        morning = math.exp(-((h - 7.5) ** 2) / (2 * 1.2 ** 2))
        evening = math.exp(-((h - 20) ** 2) / (2 * 2.0 ** 2))
        base = 0.15 + 0.5 * morning + 1.0 * evening
        return max(0.05, self.peak_kw * base * random.uniform(0.9, 1.1))

    def read(self, ts, dt_seconds):
        power = self._power(ts)
        voltage = random.gauss(230, 2)

        # rare anomalies (for the alert step)
        if random.random() < 0.005:
            kind = random.choice(["sag", "spike", "surge"])
            if kind == "sag":
                voltage = random.uniform(190, 205)
            elif kind == "spike":
                voltage = random.uniform(255, 270)
            else:
                power *= 1.8

        self.energy_kwh += power * dt_seconds / 3600
        return {
            "meter_id": self.id,
            "ts": ts,
            "voltage": round(voltage, 2),
            "current": round(power * 1000 / voltage, 3),
            "power_kw": round(power, 3),
            "energy_kwh": round(self.energy_kwh, 4),
        }


def load_meters():
    db = MongoClient(MONGO_URI)[MONGO_DB]
    return [MeterSim(d) for d in db.meters.find({}, {"_id": 0})]


def stream_realtime(sims, interval=1.0):
    """Infinite stream: one batch (all meters) per interval."""
    while True:
        ts = datetime.now(timezone.utc)
        yield [m.read(ts, interval) for m in sims]
        time.sleep(interval)


def stream_replay(sims, hours, step):
    """Fast replay: simulated time advances `step` seconds per batch."""
    end = datetime.now(timezone.utc)
    ts = end - timedelta(hours=hours)
    while ts < end:
        yield [m.read(ts, step) for m in sims]
        ts += timedelta(seconds=step)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["realtime", "replay"], default="replay")
    p.add_argument("--hours", type=float, default=24)
    p.add_argument("--step", type=int, default=60, help="seconds between readings")
    args = p.parse_args()

    sims = load_meters()
    print(f"{len(sims)} meters loaded")

    if args.mode == "realtime":
        for batch in stream_realtime(sims):
            r = batch[0]
            print(r["meter_id"], r["ts"].strftime("%H:%M:%S"),
                  f'{r["voltage"]} V  {r["power_kw"]} kW')
    else:
        total, by_hour = 0, {}
        for batch in stream_replay(sims, args.hours, args.step):
            for r in batch:
                total += 1
                if r["meter_id"] in ("M001", "M016"):
                    by_hour.setdefault((r["meter_id"], r["ts"].hour), []).append(r["power_kw"])
        print(f"{total} readings generated")
        for mid in ("M001", "M016"):
            print(f"\n{mid} average kW per hour (UTC):")
            for h in range(24):
                v = by_hour.get((mid, h))
                if v:
                    print(f"  {h:02d}h  {sum(v)/len(v):5.2f} " + "#" * int(sum(v)/len(v) * 4))