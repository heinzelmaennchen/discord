import pickle
import os
import aiohttp
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request


def init_service():
    API_NAME = 'photoslibrary'
    API_VERSION = 'v1'
    CLIENT_SECRET_FILE = 'storage/auth/client_secret_photo_wlc_discord.json'
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata', 'https://www.googleapis.com/auth/photoslibrary.appendonly']
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    return service


def Create_Service(client_secret_file, api_name, api_version, *scopes):
    #print(client_secret_file, api_name, api_version, scopes, sep='-')
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]

    cred = None

    pickle_file = f'storage/auth/token_{API_SERVICE_NAME}_{API_VERSION}.pickle'
    # print(pickle_file)

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)
    #print(f'cred: {cred}')
    #print(f'cred expired: {cred.expired}')
    #print(f'cred refreshtoken: {cred.refresh_token}')
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred, static_discovery=False)
        #print(API_SERVICE_NAME, 'service created successfully')
        return service
    except Exception as e:
        print(e)
    return None


def get_albumId(album_title, service):
    album_id = None
    response = service.albums().list().execute()
    #print(f'Album-Liste: {response}\n')
    if response != {}:
        for album in response['albums']:
            if album['title'] == album_title:
                album_id = album['id']
    return album_id


def create_album(album_title, service):
    request_body = {'album': {'title': album_title}}
    album = service.albums().create(body=request_body).execute()
    return album['id']


async def upload_image_to_album(album_id, img, upload_file_name, token,
                                service):
    upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
    headers = {
        'Authorization': 'Bearer ' + token.token,
        'Content-type': 'application/octet-stream',
        'X-Goog-Upload-Protocol': 'raw',
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(upload_url, data=img, headers=headers) as r:
            if r.status == 200:
                uploadtoken = await r.text('utf-8')

    new_media_item = [{
        'simpleMediaItem': {
            'fileName': upload_file_name,
            'uploadToken': uploadtoken
        }
    }]
    request_body = {'albumId': album_id, 'newMediaItems': new_media_item}
    upload_response = service.mediaItems().batchCreate(
        body=request_body).execute()
    mediaItem = upload_response['newMediaItemResults'][0]['mediaItem']
    return mediaItem
