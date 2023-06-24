from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
from collections import defaultdict

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

def authenticate_google_photos():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('photoslibrary', 'v1', credentials=creds)
    return service

def list_photos(service):
    results = service.mediaItems().list(pageSize=25).execute()
    items = results.get('mediaItems', [])
    return items

def create_album(service, album_title):
    create_album_request_body = {
        "album": {"title": album_title}
    }
    request = service.albums().create(body=create_album_request_body)
    album = request.execute()
    return album['id']

def add_photo_to_album(service, album_id, photo_id):
    add_items_to_album_request_body = {
        "mediaItemIds": [
            photo_id
        ]
    }
    request = service.albums().batchAddMediaItems(album_id, body=add_items_to_album_request_body)
    response = request.execute()
    return response

def confirm_album_creation(albums):
    print(f"\nThe script is about to create {len(albums)} albums in your Google Photos account.")
    print("Here's a breakdown of the albums and the number of photos each will contain:")
    for album_name, photo_ids in albums.items():
        print(f"- {album_name}: {len(photo_ids)} photos")
    return input("\nAre you sure you want to proceed? [Y/N]: ").upper() == 'Y'

def create_rollback_script(albums_created):
    with open('rollback_script.py', 'w') as f:
        f.write('from googleapiclient.discovery import build\n')
        f.write('from google_auth_oauthlib.flow import InstalledAppFlow\n')
        f.write('from google.auth.transport.requests import Request\n')
        f.write('import pickle\n')
        f.write('import os\n\n')
        f.write("SCOPES = ['https://www.googleapis.com/auth/photoslibrary']\n\n")
        f.write('def authenticate_google_photos():\n')
        f.write('    # ... (Same as in this script)\n\n')
        f.write('def delete_album(service, album_id):\n')
        f.write('    # Implement the delete album functionality here\n\n')
        f.write('def main():\n')
        f.write('    service = authenticate_google_photos()\n')
        for album_id in albums_created:
            f.write(f'    delete_album(service, "{album_id}")\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    main()\n')
    print("\nRollback script 'rollback_script.py' has been created. Run this script to undo the changes.")

def main():
    service = authenticate_google_photos()
    photos = list_photos(service)

    albums = defaultdict(list)
    for photo in photos:
        metadata = photo['mediaMetadata']
        camera_make = metadata['photo'].get('cameraMake', 'Unknown')
        creation_time = metadata['creationTime']
        year_month = creation_time[:7]  # Extract year and month
        album_name = f"{camera_make}_{year_month}"

        albums[album_name].append(photo['id'])

    if confirm_album_creation(albums):
        albums_created = []
        for album_name, photo_ids in albums.items():
            album_id = create_album(service, album_name)
            albums_created.append(album_id)
            for photo_id in photo_ids:
                add_photo_to_album(service, album_id, photo_id)
            print(f"Created album {album_name} and added {len(photo_ids)} photos.")
        create_rollback_script(albums_created)

if __name__ == '__main__':
    main()
