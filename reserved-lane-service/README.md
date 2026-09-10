# Reserved Lane Simulation Service

SUMO simulation service for evaluating the A5 paid reserved lane. An *analysis tool*: a user submits parameters, four SUMO scenarios run, and a results tables is displayed.

## API

### Submit a simulation

```
POST /api/v1/simulation
Content-Type: application/json

{
  "paying_percentage": 0.2,
  "price": 1.0,
  "traffic_scale": 2.0
}
```

Returns `202 Accepted`

```json
{ "job_id": "...", "status": "pending" }
```

### Poll for the result

```
GET /api/v1/simulation/{job_id}
```

```json
{
  "job_id": "...",
  "status": "done",
  "result": {
    "real": { "total_vehicles": 1234, "lane2_vehicles": 10, "lane2_usage_perc": "0.81%", "revenue": 0, "avg_speeds": {"320209307_0": 68.2, "320209307_1": 71.4, "320209307_2": 0.0} },
    "allOpen": { ... },
    "closedLane": { ... },
    "closedLaneFast": { ... }
  },
  "error": null
}
```

`status` `pending`, `running`, `done`, `failed`.

## Structure
```
src/
  api/routes.py                  - FastAPI routes (submit / poll)
  models/simulation.py           - request/response Pydantic models
  services/simulation/
    scenario.py                  - one TraCI run for one scenario
    statistics.py                - aggregates results
    runner.py                    - 4 scenarios processes
    jobs.py                      - async job store + bounded concurrency
  settings/simulator.py          - SUMO file paths and parameters
  main.py                        - FastAPI app + uvicorn entrypoint
templates/index.html             - simulation control page
chart/                           - Helm chart (Deployment, Service, Ingress)
```

## Required simulation files

- `A5.net.xml`
- `routes/vehicleRoutes.rou.xml`, `routes/vehicleRoutes2.rou.xml`
- `detectors.det.xml`, `polygons.poly.xml`

## Running locally

```
uv sync
uv run python -m src.main
```

Then open localhost.

With minikube:

```
minikube addons enable ingress
eval $(minikube docker-env)
docker build -t reserved-lane-simulator:local .
helm install reserved-lane ./chart \
  --set image.repository=reserved-lane-simulator \
  --set image.tag=local \
  --set image.imagePullPolicy=Never \
  --set ingress.host=reserved-lane.local
```

```
minikube ip
# add to /etc/hosts:
# <that ip>  reserved-lane.local
```

```
kubectl get pods
kubectl logs -f <podNAME>
kubectl get ingress
```

Open browser in http://reserved-lane.local/reserved-lane/
Click Start Simulation. Wait for results.


## Deploying

Deploy with the Helm chart in `chart/`:

```bash
helm install reserved-lane ./chart \
  --set image.repository=<your-registry>/reserved_lane_simulator \
  --set image.tag=<version>
```

### Key configurable values

| Value | Default | Description |
|---|---|---|
| `replicaCount` | `1` | Number of pods |
| `image.repository` | `atnog-harbor.av.it.pt/dt4mob/reserved_lane_simulator` | Container image |
| `image.tag` | `latest` | Image tag |
| `host` | `dt4mob.av.it.pt` | Ingress hostname |
| `ingress.enabled` | `true` | Create an Ingress resource |
| `service.port` | `443` | Service port |
| `service.targetPort` | `8000` | Container port |

Override values at install time with `--set` or a custom YAML file (`helm install ... -f custom-values.yaml`).

### Upgrade / Uninstall

```bash
helm upgrade reserved-lane ./chart --set image.tag=<new-version>
helm uninstall reserved-lane
```

