# NetworkController Module

`NetworkController` provides advanced control and monitoring for network interfaces, connectivity, and online interactions. It is designed to handle network state, interface configuration, Wi-Fi/Bluetooth management, connectivity tests, and simple network automation.

---

## **1. Network Interfaces & Status**

| Function | Parameters | Description |
|----------|------------|-------------|
| `list_interfaces()` | None | Returns all network interfaces and their statuses. |
| `get_interface_info(interface_name)` | `interface_name: str` | Retrieves detailed info: IP, MAC, subnet, gateway, DNS. |
| `enable_interface(interface_name)` | `interface_name: str` | Enables the specified network interface. |
| `disable_interface(interface_name)` | `interface_name: str` | Disables the specified network interface. |
| `get_ip(interface_name)` | `interface_name: str` | Returns the current IP address of the interface. |

---

## **2. Wi-Fi Management**

| Function | Parameters | Description |
|----------|------------|-------------|
| `list_wifi_networks()` | None | Returns available Wi-Fi networks. |
| `connect_wifi(ssid, password)` | `ssid: str`, `password: str` | Connects to a Wi-Fi network. |
| `disconnect_wifi()` | None | Disconnects from current Wi-Fi network. |
| `get_wifi_status()` | None | Returns current Wi-Fi status and connected SSID. |

---

## **3. Bluetooth Management**

| Function | Parameters | Description |
|----------|------------|-------------|
| `list_paired_devices()` | None | Returns all paired Bluetooth devices. |
| `pair_device(device_address)` | `device_address: str` | Pairs with a Bluetooth device. |
| `unpair_device(device_address)` | `device_address: str` | Unpairs a Bluetooth device. |
| `get_bluetooth_status()` | None | Returns current Bluetooth status (on/off, paired devices). |

---

## **4. Connectivity & Network Tests**

| Function | Parameters | Description |
|----------|------------|-------------|
| `ping(host, count=4)` | `host: str`, `count: int` | Performs ICMP ping to check connectivity. |
| `traceroute(host)` | `host: str` | Returns the network path to the host. |
| `check_internet()` | None | Checks if there is an active internet connection. |
| `download_speed_test()` | None | Measures download speed. |
| `upload_speed_test()` | None | Measures upload speed. |

---

## **5. Advanced Network Controls**

| Function | Parameters | Description |
|----------|------------|-------------|
| `set_static_ip(interface_name, ip, subnet, gateway, dns=None)` | `interface_name: str`, `ip: str`, `subnet: str`, `gateway: str`, `dns: str|None` | Sets static IP configuration for the interface. |
| `reset_interface(interface_name)` | `interface_name: str` | Resets the interface to default configuration. |
| `monitor_traffic(interface_name, duration)` | `interface_name: str`, `duration: int` | Monitors traffic (bytes sent/received) for a period. |

---

## **Use Cases**

- Automated switching between Wi-Fi networks based on availability or signal strength.
- Monitoring network interfaces and traffic for troubleshooting or analytics.
- Running connectivity checks and internet speed tests automatically.
- Controlling Bluetooth connections and pairing devices for IoT or automation purposes.
- Setting static IPs for servers or local network configuration automatically.
- Integrating network checks into pipelines or system automation scripts.

---

**Notes:**

- All functions should handle exceptions gracefully and return meaningful error messages.
- Supports both Windows and cross-platform functions where possible.
- Can be integrated with automation pipelines or schedulers for network tasks.

