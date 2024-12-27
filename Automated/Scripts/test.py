import psutil

def get_core_count():
    total_cores = psutil.cpu_count(logical=True)  # Logical cores (includes hyperthreading)
    physical_cores = psutil.cpu_count(logical=False)  # Physical cores
    print(f"Logical cores: {total_cores}, Physical cores: {physical_cores}")

if __name__ == "__main__":
    get_core_count()