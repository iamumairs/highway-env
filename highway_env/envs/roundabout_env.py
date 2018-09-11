from __future__ import division, print_function, absolute_import
import numpy as np

from highway_env import utils
from highway_env.envs.abstract import AbstractEnv
from highway_env.envs.graphics import EnvViewer
from highway_env.road.lane import LineType, StraightLane, CircularLane, SineLane
from highway_env.road.road import Road, RoadNetwork
from highway_env.vehicle.control import MDPVehicle


class RoundaboutEnv(AbstractEnv):

    COLLISION_REWARD = -1
    HIGH_VELOCITY_REWARD = 0.2
    RIGHT_LANE_REWARD = 0
    LANE_CHANGE_REWARD = 0

    DEFAULT_CONFIG = {"other_vehicles_type": "highway_env.vehicle.behavior.IDMVehicle"}

    def __init__(self):
        super(RoundaboutEnv, self).__init__()
        self.config = self.DEFAULT_CONFIG.copy()
        self.make_road()
        self.make_vehicles()
        EnvViewer.SCREEN_HEIGHT = 600

    def configure(self, config):
        self.config.update(config)

    def _observation(self):
        return super(RoundaboutEnv, self)._observation()

    def _reward(self, action):
        reward = self.COLLISION_REWARD * self.vehicle.crashed \
                 + self.HIGH_VELOCITY_REWARD * self.vehicle.velocity_index / (self.vehicle.SPEED_COUNT - 1)
        return reward

    def _is_terminal(self):
        """
            The episode is over when a collision occurs or when the access ramp has been passed.
        """
        return self.vehicle.crashed

    def reset(self):
        self.make_road()
        self.make_vehicles()
        return self._observation()

    def make_road(self):
        # Circle lanes: (s)outh/(e)ast/(n)orth/(w)est (e)ntry/e(x)it.
        center = [0, 0]  # [m]
        radius = 40  # [m]
        alpha = 30  # [deg]

        net = RoadNetwork()
        radii = [radius, radius+4]
        n, c, s = LineType.NONE, LineType.CONTINUOUS, LineType.STRIPED
        line = [[c, s], [n, c]]
        for lane in [0, 1]:
            net.add_lane("se", "ex", CircularLane(center, radii[lane], rad(90-alpha), rad(alpha), line_types=line[lane]))
            net.add_lane("ex", "ee", CircularLane(center, radii[lane], rad(alpha), rad(-alpha), line_types=line[lane]))
            net.add_lane("ee", "nx", CircularLane(center, radii[lane], rad(-alpha), rad(-90+alpha), line_types=line[lane]))
            net.add_lane("nx", "ne", CircularLane(center, radii[lane], rad(-90+alpha), rad(-90-alpha), line_types=line[lane]))
            net.add_lane("ne", "wx", CircularLane(center, radii[lane], rad(-90-alpha), rad(-180+alpha), line_types=line[lane]))
            net.add_lane("wx", "we", CircularLane(center, radii[lane], rad(-180+alpha), rad(-180-alpha), line_types=line[lane]))
            net.add_lane("we", "sx", CircularLane(center, radii[lane], rad(180-alpha), rad(90+alpha), line_types=line[lane]))
            net.add_lane("sx", "se", CircularLane(center, radii[lane], rad(90+alpha), rad(90-alpha), line_types=line[lane]))

        # Access lanes: (r)oad/(s)ine
        access = 200  # [m]
        dev = 160  # [m]
        a = 5  # [m]
        delta_st = 0.21*dev  # [m]

        delta_en = dev-delta_st
        w = 2*np.pi/dev
        net.add_lane("ser", "ses", StraightLane([2, access], [2, dev/2], line_types=[s, c]))
        net.add_lane("ses", "se", SineLane([2+a, dev/2], [2+a, dev/2-delta_st], a, w, -np.pi/2, line_types=[c, c]))
        net.add_lane("sx", "sxs", SineLane([-2-a, -dev/2+delta_en], [-2-a, dev/2], a, w, -np.pi/2+w*delta_en, line_types=[c, c]))
        net.add_lane("sxs", "sxr", StraightLane([-2, dev / 2], [-2, access], line_types=[n, c]))

        net.add_lane("eer", "ees", StraightLane([access, -2], [dev / 2, -2], line_types=[s, c]))
        net.add_lane("ees", "ee", SineLane([dev / 2, -2-a], [dev / 2 - delta_st, -2-a], a, w, -np.pi / 2, line_types=[c, c]))
        net.add_lane("ex", "exs", SineLane([-dev / 2 + delta_en, 2+a], [dev / 2, 2+a], a, w, -np.pi / 2 + w * delta_en, line_types=[c, c]))
        net.add_lane("exs", "exr", StraightLane([dev / 2, 2], [access, 2], line_types=[n, c]))

        road = Road(network=net)
        self.road = road

    def make_vehicles(self):
        """
            Populate a road with several vehicles on the highway and on the merging lane, as well as an ego-vehicle.
        :return: the ego-vehicle
        """
        road = self.road
        ego_lane = road.network.get_lane(("ser", "ses", 0))
        ego_vehicle = MDPVehicle(road,
                                 ego_lane.position(90, 0),
                                 velocity=10,
                                 heading=ego_lane.heading_at(90))
        MDPVehicle.SPEED_MIN = 5
        MDPVehicle.SPEED_MAX = 20
        road.vehicles.append(ego_vehicle)
        self.vehicle = ego_vehicle

        other_vehicles_type = utils.class_from_path(self.config["other_vehicles_type"])
        for i in range(3):
            road.vehicles.append(other_vehicles_type(road,
                                                     road.network.get_lane(("we", "sx", 0)).position(20*i, 0),
                                                     velocity=10,
                                                     heading=road.network.get_lane(("we", "sx", 0)).heading_at(20*i)))


def rad(deg):
    return deg*np.pi/180
