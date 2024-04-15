#!/usr/bin/python3

try:
    from sensor import Sensor
except:
    from .sensor import Sensor

    
from typing import Type

class IVehicleState():
    def update_sensor(self, sensor_name:str, values, time:float): pass
    def update_sensor_status_str(self, sensor_name:str, status:str): pass
    def __getitem__(self, key:str): pass
    @property
    def all_sensors_working(self) -> tuple[bool, list]: pass


class IVehicleStateContainer():
    @property
    def vehicle_state(self) -> Type[IVehicleState]: pass
    


class MockVehicleStateContainer(IVehicleStateContainer):
    def __init__(self) -> None:
        self._vehicle_state = VehicleState("Mock", "Nowhere")
    
    @property
    def vehicle_state(self) -> Type[IVehicleState]:
        return self._vehicle_state



class VehicleState(IVehicleState):
    LATLON = "LATLON"
    ABSOLUTE = "ABSOLUTE"
    PERCENT = "PERCENT"

    def __init__(self, name: str, reference_frame: str):
        """
        The base vehicle object that contains the common things every vehicle needs to have.
        name: just a string to identify the vehicle
        reference_frame: the reference frame of position stuffs
        """
        # name of the vehicle and the reference frame that
        # all its attributes work with
        # the reference frame could be 'odom', could be "utm_XY_Z"
        self._reference_frame = reference_frame
        self._name = name

        
        # x,y,height
        # where height is above sea --> negative when under water
        self._position = Sensor("position",
                                self._reference_frame,
                                3)

        # yaw pitch roll
        self._orientation_euler = Sensor("orientation_euler",
                                         self._reference_frame,
                                         3,
                                         ["roll", "pitch", "yaw"])

        # global position, lat lon heading
        # separate from the above because this'll likely come
        # from gps fixes and not DR
        self._global_position = Sensor("global_position",
                                       VehicleState.LATLON,
                                       2,
                                       ["lat", "lon"])
        
        self._global_heading_deg = Sensor("global_heading_deg",
                                          VehicleState.LATLON,
                                          1)
        
        self._battery = Sensor("battery", VehicleState.ABSOLUTE, 2, ["V", "%"])

        self.sensors = {}
        for k,v in vars(self).items():
            if type(v) == Sensor:
                self.sensors[v._name] = v

    @property
    def all_sensors_working(self) -> tuple[bool, list]:
        not_working = [v.name for k,v in self.sensors.items() if not v.working]
        all_working = len(not_working) == 0
        return (all_working, not_working)
    

    def __str__(self) -> str:
        s = f"Vehicle:{self._name}\n"
        for sensor_name, sensor in self.sensors.items():
            s += "- " + sensor.__str__() + "\n"
        return s
    
    
    def __getitem__(self, key: str) -> Sensor:
        return self.sensors[key]


    # These could be convenient to write some generic "update" functions for ROS
    # related reasons later.
    def update_sensor(self, sensor_name:str, values, time:float):
        """
        sensor_name: the name of the sensor object that you can find in the constructors
        values, time: passed straight to the sensor object
        """
        self.sensors[sensor_name].update(values, time)


    def update_sensor_status_str(self, sensor_name:str, status:str):
        self.sensors[sensor_name].update_status_str(status)



class UnderwaterVehicleState(VehicleState):
    def __init__(self, name: str, reference_frame: str):
        """
        Extends the base vehicle to include underwater-related basics
        """

        self._altitude = Sensor("altitude", VehicleState.ABSOLUTE, 1)
        self._leak = Sensor("leak", VehicleState.ABSOLUTE, 1)
        self._vbs = Sensor("vbs", VehicleState.PERCENT, 1)
        self._lcg = Sensor("lcg", VehicleState.PERCENT, 1)
        self._thrusters = Sensor("thrusters", VehicleState.ABSOLUTE, 2)
        
        super().__init__(name, reference_frame)



if __name__ == "__main__":
    v = UnderwaterVehicleState("test vehicle", "utm123")
    print(v["position"].working)
    v.update_sensor("position", [1,2,3], 0)
    print(v["position"].working)
    v.update_sensor("lcg", [10], 0)
    print(v)
    v.update_sensor("position", [2,3,4], 1)
    print(v)

    print(v.all_sensors_working)
    v.update_sensor("orientation_euler", [1,2,3], 0)
    v.update_sensor("global_position", [1,2], 0)
    v.update_sensor("global_heading_deg", [1], 0)
    v.update_sensor("battery", [1,2], 0)
    v.update_sensor("altitude", [1], 0)
    v.update_sensor("leak", [False], 0)
    v.update_sensor("vbs", [1], 0)
    v.update_sensor("thrusters", [1,2], 0)
    print(v.all_sensors_working)

    print([(s._name, s.working) for _,s in v.sensors.items()])