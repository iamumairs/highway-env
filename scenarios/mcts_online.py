from highway.agent.mcts import MCTSAgent
from highway.road.road import Road
from highway.simulation import Simulation
from highway.vehicle.control import MDPVehicle
from highway.vehicle.behavior import IDMVehicle
from highway.vehicle.dynamics import Obstacle


def main():
    road = Road.create_random_road(lanes_count=2, lane_width=4.0, vehicles_count=0, vehicles_type=IDMVehicle)
    sim = Simulation(road, ego_vehicle_type=MDPVehicle, agent_type=MCTSAgent)

    t = 0
    while not sim.done:
        sim.process()
        t += 1
        if t == 30*10:
            print('Added obstacle')
            road.vehicles.append(Obstacle(road, [sim.vehicle.position[0] + 100., sim.vehicle.position[1]]))
    sim.quit()


if __name__ == '__main__':
    main()
