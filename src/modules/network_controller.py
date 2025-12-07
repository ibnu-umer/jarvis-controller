import psutil
import socket

from core.registry import action
from core.base_module import BaseModule



class NetworkControllerModule(BaseModule):

    @action(name="list_interfaces")
    def list_interfaces(self) -> list:
        interfaces = []
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for iface, st in stats.items():
            interfaces.append({
                "name": iface,
                "is_up": st.isup,
                "speed": st.speed,
                "mtu": st.mtu,
                "addresses": [
                    a.address for a in addrs.get(iface, []) if a.family in (socket.AF_INET, socket.AF_INET6)
                ]
            })
        return self.success("Listed Interfaces", data=interfaces)
    

    @action(name="get_interface_info", params={"interface_name"})
    def get_interface_info(self, interface_name: str) -> dict:
        stats = psutil.net_if_stats().get(interface_name)
        addrs = psutil.net_if_addrs().get(interface_name)

        if not stats or not addrs:
            return {"error": "Interface not found"}

        iface_info = {"name": interface_name, "is_up": stats.isup, "speed": stats.speed, "mtu": stats.mtu}

        for a in addrs:
            if a.family == socket.AF_INET:
                iface_info["ipv4"] = a.address
                iface_info["subnet"] = a.netmask
            elif a.family == psutil.AF_LINK:
                iface_info["mac"] = a.address

        return self.success("Fetched Interface info", data=iface_info)
    

    @action(name="get_ip", params={"interface_name"})
    def get_ip(self, interface_name: str) -> str:
        addrs = psutil.net_if_addrs().get(interface_name)
        if not addrs:
            return ""
        for a in addrs:
            if a.family == socket.AF_INET:
                return a.address
        return ""
