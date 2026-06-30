
#!/bin/bash

# python3 /usr/share/sumo/tools/detector/edgeDataFromFlow.py  -b 39346 -e 40511 -d ../detectors.det.xml -f flows.csv -o edgeData.xml -i 1 --time-scale 1

python3 /usr/share/sumo/tools/randomTrips.py -n ../A5.net.xml -r randomRoutes.rou.xml -b 39346 -e 40511 --trip-attributes="departLane=\"best_prob\" departSpeed=\"avg\"" --fringe-factor max --random-routing-factor 10 -v

python3 /usr/share/sumo/tools/routeSampler.py -r randomRoutes.rou.xml -d cleanEdgeData.xml -o sampledRoutes.rou.xml --attributes="departLane=\"best_prob\" departSpeed=\"avg\"" --mismatch-output mismatch2.xml
