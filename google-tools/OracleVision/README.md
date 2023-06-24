Absolutely, here's your updated `README.md` file:

---

# OracleVision.py

**OracleVision.py** is a Python script designed to organize your Google Photos library by creating albums based on specific photo metadata fields: `cameraMake` and `creationTime`. Inspired by the wisdom of the Oracle from The Matrix, OracleVision.py gives you the power to foresee the changes that will be made to your photo library before they occur.

## Features

- **Scan Google Photos library:** OracleVision.py fetches the metadata of your photos from your Google Photos account and calculates the number of new albums that would be created.

- **Preview changes:** Before any changes are made, OracleVision.py provides a summary of the proposed album organization and asks for your confirmation to proceed.

- **Create Albums:** On confirmation, OracleVision.py creates new albums named according to the `cameraMake` and `creationTime` (limited to the month and year) metadata of each photo and adds the corresponding photos to these albums.

- **Generate Rollback Script:** After the process is completed, OracleVision.py generates a Python rollback script which can be run to undo the changes made to the album organization.

## How to Use

Before running OracleVision.py, ensure you have obtained the necessary OAuth2 credentials from the Google Developer Console and saved them to a file named 'credentials.json'.

To get the credentials:

1. Visit the Google API Console at the following URL: https://console.developers.google.com/
2. Create a new project or select an existing one.
3. Under "Library", look for "Photos Library API" and enable it for your project.
4. Go to the "Credentials" tab and click on "Create Credentials". Choose "OAuth client ID".
5. Configure your OAuth consent screen and save it.
6. Back in "Create credentials", select "Desktop app" as the application type, give it a name and create it.
7. Download the credentials and save them as 'credentials.json' in the same directory as this script.

Once you have the credentials:

1. Clone this repository or download the script.
2. Run `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib` in your terminal to install the necessary dependencies.
3. Run `python OracleVision.py` in your terminal.
4. Authenticate with your Google account when prompted.
5. Review the changes summary and enter 'Y' when asked for confirmation to proceed.
6. After the script completes, a rollback script `rollback_script.py` will be generated. Run this script if you wish to undo the album organization changes made by OracleVision.py.

**Note:** The `delete_album()` function in the rollback script is a placeholder. As of the last update (September 2021), Google Photos API does not support deleting albums. You would have to manually remove any unwanted albums through the Google Photos interface.

## License

OracleVision.py is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

OracleVision.py is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.

## Disclaimer

This script is provided as-is, and it is up to the user to review the script and adjust it according to their needs. The developer of this script is not responsible for any loss of data or other adverse effects.

---

"You didn't come here

 to make the choice. You've already made it. You're here to try to understand *why* you made it." - The Oracle, The Matrix

---
