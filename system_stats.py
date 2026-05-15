import math
import shutil
import subprocess

try:
    import psutil
except Exception:
    psutil = None

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


def system_stats():
    if psutil:
        cpu_stats = str(psutil.cpu_percent())
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else "unknown"
        memory_in_use = convert_size(psutil.virtual_memory().used)
        total_memory = convert_size(psutil.virtual_memory().total)
        return f"Currently {cpu_stats} percent of CPU, {memory_in_use} of RAM out of total {total_memory} is being used and battery level is at {battery_percent} percent"

    total, used, free = shutil.disk_usage(".")
    memory = _windows_memory_status()
    if memory:
        return f"Disk usage is {convert_size(used)} used out of {convert_size(total)}. {memory}"
    return f"Disk usage is {convert_size(used)} used out of {convert_size(total)}, with {convert_size(free)} free."


def _windows_memory_status():
    try:
        result = subprocess.run(
            ["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/Value"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        values = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = int(value.strip())
        total_kb = values.get("TotalVisibleMemorySize")
        free_kb = values.get("FreePhysicalMemory")
        if not total_kb or free_kb is None:
            return None
        used_kb = total_kb - free_kb
        return f"RAM usage is {convert_size(used_kb * 1024)} out of {convert_size(total_kb * 1024)}."
    except Exception:
        return None

