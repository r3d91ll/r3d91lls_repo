import logging
from ..MercerClass import MercerClass

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create an instance of MercerClass
mercer = MercerClass("/var/cache/apt", min_free_space_gb=10)

# Test get_disk_space_info method
disk_space_info = mercer.get_disk_space_info()
print("Disk Space Info:", disk_space_info)

# Test check_min_free_space method
min_free_space_check = mercer.check_min_free_space()
print("Minimum Free Space Check:", min_free_space_check)

# Test generate_report method
report = mercer.generate_report()
print("Report:")
print(report)
