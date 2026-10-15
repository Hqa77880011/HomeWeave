import copy

import numpy as np


METHODS = [
    "homeweave",
    "tunnel_only",
    "independent_nodes",
    "shuffled_timing",
    "one_end",
    "no_real_embedding",
]


def compile_episode(template, rng, start=0.0):
    times = {}
    pending = list(template)
    slots = []
    while pending:
        ready = [
            node
            for node in pending
            if all(edge["parent"] in times for edge in node.get("parents", []))
        ]
        if not ready:
            raise ValueError("Cyclic episode template")
        for node in sorted(ready, key=lambda n: n["id"]):
            parents = node.get("parents", [])
            lower = max([times[e["parent"]] + e["min"] for e in parents] + [start])
            upper = min(
                [times[e["parent"]] + e["max"] for e in parents] + [start + node.get("window", 10)]
            )
            if lower > upper:
                raise ValueError("Infeasible multi-parent timing intersection")
            times[node["id"]] = float(rng.uniform(lower, upper))
            slots.append(
                {
                    "time": times[node["id"]],
                    "direction": node["direction"],
                    "capacity": node["capacity"],
                }
            )
            pending.remove(node)
    return sorted(slots, key=lambda slot: (slot["time"], slot["direction"]))


def generate(rng, count):
    for index in range(count):
        topic = rng.randrange(2)
        template = [
            {"id": "trigger", "direction": 0, "capacity": 256, "window": 0.1},
            {
                "id": "reply",
                "direction": 1,
                "capacity": 256,
                "window": 10,
                "parents": [{"parent": "trigger", "min": 0.1, "max": 0.4}],
            },
            {
                "id": "followup",
                "direction": 0,
                "capacity": 256,
                "window": 10,
                "parents": [{"parent": "reply", "min": 0.1, "max": 0.4}],
            },
        ]
        messages = [
            {
                "id": str(i),
                "time": i * 0.5 + rng.random() * 0.1,
                "direction": (i + topic) % 2,
                "bytes": rng.randint(40, 200),
                "deadline": 0.7,
            }
            for i in range(12)
        ]
        yield {
            "id": str(index),
            "family": f"home-{index}",
            "template": template,
            "messages": messages,
            "topic": topic,
            "duration": 8.0,
            "seed": rng.randrange(2**31),
            "cell_bytes": 256,
        }


def run_case(case, method):
    rng = np.random.default_rng(case["seed"])
    slots = []
    for start in np.arange(0, case["duration"] - 1.0, 0.5):
        slots.extend(compile_episode(case["template"], rng, float(start)))
    if method == "independent_nodes":
        for slot in slots:
            slot["time"] = float(rng.uniform(0, case["duration"]))
    elif method == "shuffled_timing":
        times = [slot["time"] for slot in slots]
        rng.shuffle(times)
        for slot, t in zip(slots, times):
            slot["time"] = t
    elif method == "one_end":
        slots = [slot for slot in slots if slot["direction"] == 0]
    elif method == "tunnel_only":
        slots = []
    slots.sort(key=lambda slot: slot["time"])
    messages = [
        {**message, "remaining": message["bytes"], "delivered_at": None}
        for message in copy.deepcopy(case["messages"])
    ]
    events = [(slot["time"], 0, slot) for slot in slots]
    events.extend((m["time"] + m["deadline"], 1, m) for m in messages)
    trace = []
    overflow = 0
    for t, kind, payload in sorted(events, key=lambda e: (e[0], e[1])):
        if kind == 0:
            capacity = payload["capacity"]
            if method != "no_real_embedding":
                eligible = sorted(
                    [
                        m
                        for m in messages
                        if m["time"] <= t
                        and m["remaining"] > 0
                        and m["direction"] == payload["direction"]
                    ],
                    key=lambda m: (m["time"] + m["deadline"], m["time"], m["id"]),
                )
                for message in eligible:
                    sent = min(capacity, message["remaining"])
                    message["remaining"] -= sent
                    capacity -= sent
                    if not message["remaining"]:
                        message["delivered_at"] = t
                    if capacity == 0:
                        break
            trace.append([t, payload["direction"], payload["capacity"], False])
        elif payload["remaining"]:
            message = payload
            transmit = message["time"] if method == "tunnel_only" else t
            cells = int(np.ceil(message["remaining"] / case["cell_bytes"]))
            trace.append([transmit, message["direction"], cells * case["cell_bytes"], True])
            message["remaining"] = 0
            message["delivered_at"] = transmit
            overflow += 1
    feature = np.zeros((2, 16))
    for t, direction, size, _ in trace:
        feature[direction, min(15, int(t / case["duration"] * 16))] += size
    return {
        "trace": sorted(trace),
        "messages": messages,
        "overflow": overflow,
        "features": feature.ravel().tolist(),
        "attack_label": case["topic"],
    }


def score(case, result):
    delays = [
        m["delivered_at"] - m["time"] for m in result["messages"] if m["delivered_at"] is not None
    ]
    original_bytes = sum(m["bytes"] for m in case["messages"])
    total_bytes = sum(event[2] for event in result["trace"])
    return {
        "command_success": sum(
            m["delivered_at"] is not None and m["delivered_at"] <= m["time"] + m["deadline"] + 1e-9
            for m in result["messages"]
        )
        / len(result["messages"]),
        "byte_ratio": total_bytes / original_bytes,
        "total_bytes": total_bytes,
        "overflow_fraction": result["overflow"] / len(result["messages"]),
        "mean_delay": float(np.mean(delays)) if delays else None,
        "p95_delay": float(np.quantile(delays, 0.95)) if delays else None,
        "legal_effects": len(delays),
    }
