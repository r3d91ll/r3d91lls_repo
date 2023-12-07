import os
import shutil
import subprocess
import logging
import json


class MercerClass:
    def __init__(self, path, min_free_space_gb=None):
        self.path = path
        self.min_free_space_gb = min_free_space_gb

    def get_disk_space_info(self):
        try:
            total, used, free = shutil.disk_usage(self.path)
            return {"total": total, "used": used, "free": free}
        except Exception as e:
            logging.error(f"Error getting disk space info: {e}")
            return None

    def check_min_free_space(self):
        """ Check if the free space meets the minimum requirement. """
        if self.min_free_space_gb is None:
            logging.warning("Minimum free space threshold not set.")
            return False

        disk_space_info = self.get_disk_space_info()
        if disk_space_info is None:
            return False

        free_space_gb = disk_space_info["free"] / (1024 ** 3)
        return free_space_gb >= self.min_free_space_gb

    def get_mount_point(self):
        """ Get the mount point of the specified directory. """
        mount_output = subprocess.check_output(['df', '-P', self.path]).decode('utf-8')
        mount_lines = mount_output.strip().split('\n')
        mount_info = mount_lines[1].split()
        return mount_info[-1]
    
    def find_largest_files(self, num_files):
        """ Find the largest files at the mount point. """
        mount_point = self.get_mount_point()
        excluded_dirs = ['proc', 'dev', 'sys', 'media', 'tmp', 'run']
        file_sizes = []
        for dirpath, dirnames, filenames in os.walk(mount_point):
            # Exclude directories
            dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    file_sizes.append((file_path, file_size))
                except FileNotFoundError:
                    continue

        return sorted(file_sizes, key=lambda x: x[1], reverse=True)[:num_files]

    def generate_report(self):
        """ Generate a comprehensive report including the free space check and largest files. """
        disk_space_info = self.get_disk_space_info()
        free_space_check = self.check_min_free_space() if self.min_free_space_gb is not None else "Not Applicable"
        largest_files = [] if free_space_check else self.find_largest_files(10)

        # Convert file sizes to gigabytes
        largest_files = [(file_path, file_size / (1024 ** 3)) for file_path, file_size in largest_files]

        report = {
            "disk_space_info": {k: v / (1024 ** 3) for k, v in disk_space_info.items()},
            "minimum_free_space_required_gb": self.min_free_space_gb,
            "free_space_check_passed": free_space_check,
            "largest_files": largest_files
        }
        return json.dumps(report, indent=4)
