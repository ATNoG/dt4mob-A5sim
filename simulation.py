""" 
A5 proof of concept

traci script to create a paid lane simulation for congested scenarios

vehicle types: slow and fast

fast should be able to change lane into the closed one to go faster -> needs to change type from fast to faster to go into closed

need a ui so users can select the percentage of fast cars that change into faster and go into closed lane
"""

import os
import sys
import random
import argparse
import multiprocessing

if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

import traci

def run_simulation(scenario, scale_traffic, perc, price, port, return_dict):
    ## 4 diff sims
    # all lanes, real traffic
    # all lanes, factor traffic
    # 2 lanes open, 1 lane closed with some cars already on it
    # 2 lanes open, 1 closed but with 50% of fast cars going into it
    print(f"{scenario} x {scale_traffic} with {perc*100:.2f}% and {price}€ at {port}")

    perc2 = perc/0.8 if perc > 0 else 0.0

    if scenario == "real":
        traci.start([
        "sumo-gui",
        "-n", "A5.net.xml",              
        "-r", "routes/vehicleRoutes.rou.xml", 
        "--additional-files", "detectors.det.xml,polygons.poly.xml",
        "--begin", "39346", 
        "--end", "40000",
        "--time-to-teleport", "-1",
        "--statistics-output", f"output/stats_{scenario}_{scale_traffic}_{perc:.2f}.xml",
        "--step-length", "0.1",
        "--output-prefix", f"{scenario}_{perc:.2f}_",
        "-g", "viewgui.xml",
        "--start",
        "--quit-on-end",
        ], port=port)
        
    
    elif scenario == "closedLane":
        traci.start([
            "sumo-gui",
            "-n", "A5.net.xml",              
            "-r", "routes/vehicleRoutes2.rou.xml", 
            "--additional-files", "detectors.det.xml,polygons.poly.xml",
            "--begin", "39346", 
            "--end", "40000",
            "--time-to-teleport", "-1",
            "--scale", str(scale_traffic),
            "--statistics-output", f"output/stats_{scenario}_{scale_traffic}_{perc:.2f}.xml",
            "--step-length", "0.1",
            "--output-prefix", f"{scenario}_{scale_traffic}_{perc:.2f}_",
            "-g", "viewgui.xml",
            "--start",
            "--quit-on-end",
        ], port=port)

    else: 
        traci.start([
            "sumo-gui",
            "-n", "A5.net.xml",              
            "-r", "routes/vehicleRoutes.rou.xml", 
            "--additional-files", "detectors.det.xml,polygons.poly.xml",
            "--begin", "39346", 
            "--end", "40000",
            "--time-to-teleport", "-1",
            "--scale", str(scale_traffic),
            "--statistics-output", f"output/stats_{scenario}_{scale_traffic}_{perc:.2f}.xml",
            "--step-length", "0.1",
            "--output-prefix", f"{scenario}_{scale_traffic}_{perc:.2f}_",
            "-g", "viewgui.xml",
            "--start",
            "--quit-on-end",
        ], port=port)

    if scenario == "closedLane" or scenario == "closedLaneFast":
        traci.lane.setDisallowed("320209307_2", ["custom1", "custom2"])
        traci.lane.setDisallowed("49166745_2", ["custom1", "custom2"])
    
    all_vehicles = set()
    lane_2_vehicles = set()
    detected_ids_seen = set()
    processed_vids = set()

    # {lane_id: [sum_of_speeds, count_of_samples]}
    lane_speed_data = {}
    target_lanes = ["320209307_0", "320209307_1", "320209307_2"]
    for lid in target_lanes:
        lane_speed_data[lid] = [0.0, 0]
        
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        sim_time = traci.simulation.getTime()

        if sim_time >= 40000: break

        vehicle_ids = traci.vehicle.getIDList()
        # detector_ids = traci.inductionloop.getIDList()

        for vid in vehicle_ids:
            all_vehicles.add(vid)

            pos = traci.vehicle.getPosition(vid)      # (x, y) coordinates (m)
            lane_id = traci.vehicle.getLaneID(vid)    # lane ID
            speed = traci.vehicle.getSpeed(vid)       # speed (m/s)
            typeid = traci.vehicle.getTypeID(vid)     # fast, slow  

            if lane_id in lane_speed_data:
                lane_speed_data[lane_id][0] += speed 
                lane_speed_data[lane_id][1] += 1    

            if pos[0] > 400 and pos[0] < 700 and vid not in processed_vids and typeid == "custom2" and scenario == "closedLaneFast":
                processed_vids.add(vid)
                if random.random() < min(perc2, 1.0):
                    traci.vehicle.setType(vid, "passenger")
                    traci.vehicle.changeLane(vid, 2, 1000.0)
                        
            if lane_id.endswith("_2"):
                lane_2_vehicles.add(vid)

        for did in ["toll_2"]: # , "after_toll_2", "end_toll_2"
            for v in traci.inductionloop.getLastStepVehicleIDs(did):
                detected_ids_seen.add(v)
                
    traci.close()

    total_v = len(all_vehicles)
    lane2_v = len(lane_2_vehicles)
    lane2_d = len(detected_ids_seen)

    avg_speeds = {}
    for lid, data in lane_speed_data.items():
        total_speed = data[0]
        samples = data[1]
        avg_speeds[lid] = round(total_speed / samples, 2) if samples > 0 else 0.0
        # convert from m/s to km/h
        avg_speeds[lid] = round(avg_speeds[lid] * 3.6, 2)

    return_dict[scenario] = {
        "total_vehicles": total_v,
        "lane2_vehicles": len(lane_2_vehicles),
        "lane2_usage_perc": f"{(lane2_v/total_v)*100:.2f}%" if total_v > 0 else "0%",
        "revenue": round(price * lane2_d, 2) if scenario not in ["real", "allOpen"] else 0,
        "avg_speeds": avg_speeds
    }

def main(perc: float, price: float, scale_traffic: float) -> None:
    scenarios = [
        ("real", 0.0),
        ("allOpen", 0.0),
        ("closedLane", 0.0),
        ("closedLaneFast", perc)
    ]

    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    processes = []
    
    for i, (scenario, s_perc) in enumerate(scenarios):
        p = multiprocessing.Process(target=run_simulation, args=(scenario, scale_traffic, s_perc, price, 8813+i, return_dict))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    
    return dict(return_dict)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)

    parser = argparse.ArgumentParser("Script for running sumo with TraCI.")
    parser.add_argument("--perc", type=float, default=0.2, help="Percentage of vehicles that can change to lane 2")
    parser.add_argument("--price", type=float, default=1.00, help="Price for using the paid lane")
    parser.add_argument("--scale_traffic", type=float, default=2.0, help="Scale factor for traffic volume")
    args = parser.parse_args()

    main(args.perc, args.price, args.scale_traffic)
