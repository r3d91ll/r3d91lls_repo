#!/bin/bash

# Change to the directory containing Dr.Tyrell
cd "$(dirname "$0")/Dr.Tyrell"

# Backup Dr.Tyrell directory
echo "Creating backup of Dr.Tyrell directory..."
tar -czf ../Dr.Tyrell_backup_$(date +%Y%m%d%H%M%S).tar.gz .

# Create new directory structure
echo "Creating new directory structure..."
mkdir -p BaseInstructionSets/OperatingSystems BaseInstructionSets/ProgrammingLanguages BaseInstructionSets/ConfigurationManagement BaseInstructionSets/VersionControl BaseInstructionSets/CloudPlatforms
mkdir -p Projects/AtlasProject/InstructionSets/ClassInstructions Projects/AtlasProject/InstructionSets/FunctionInstructions
mkdir -p Projects/UbikProtocol/InstructionSets
mkdir -p Utilities/BASH Utilities/PythonUtilities

# Move existing files to new structure
echo "Moving existing files to new structure..."
mv BASH/* Utilities/BASH/
mv Project\ Atlas/Docs/* Projects/AtlasProject/
mv Project\ Atlas/Python3.6 Projects/AtlasProject/
mv Project\ Atlas/TitanScript Projects/AtlasProject/
mv UbikProtocol/* Projects/UbikProtocol/

# Remove now-empty directories
echo "Removing empty directories..."
rmdir BASH Project\ Atlas UbikProtocol

echo "Directory reorganization complete."
