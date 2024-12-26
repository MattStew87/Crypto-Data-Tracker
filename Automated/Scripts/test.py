import psutil

def check_core_usage():
    for core_id, usage in enumerate(psutil.cpu_percent(percpu=True)):
        print(f"Core {core_id}: {usage}% usage")

if __name__ == "__main__":
    check_core_usage()
