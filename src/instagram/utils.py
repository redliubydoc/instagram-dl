import requests

from pathlib import Path
from common.utils import download_binary


def build_headers(config, driver):

    csrftoken = ""
    cookies_string = ""
    user_agent = driver.execute_script("return navigator.userAgent;")

    for cookie in driver.get_cookies():
        cookies_string += cookie["name"] + "=" + cookie["value"] + "; "

        if cookie["name"] == "csrftoken":
            csrftoken = cookie["value"]

    headers = config["headers"]
    headers["user-agent"] = user_agent
    headers["referer"] = driver.execute_script("return location.href")
    headers["cookie"] = cookies_string
    headers["x-ig-app-id"] = config["instagram"]["app_id"]
    headers["x-csrftoken"] = csrftoken
    headers["x-ig-www-claim"] = driver.execute_script("return window.sessionStorage.getItem(\"www-claim-v2\");")

    return headers


def scrap_web_profile_info(config, driver, user_name):

    # open profile page
    driver.get(f"https://www.instagram.com/{user_name}/")

    # get web profile info
    web_profile_info_endpoint = config["instagram"]["web_profile_info_endpoint"]
    headers = build_headers(config, driver)
    params = { 
        "username": user_name
    }

    try:    
        response = requests.get(web_profile_info_endpoint, params=params, headers=headers)

        if response.status_code == 200 and response.json()["status"] == "ok":
            user = response.json()["data"]["user"]

        else:
            raise Exception("status code != 200 or response.json.status != ok")
        
    except Exception as e:
        raise Exception()
    
    return user


def scrap_followers(config, driver, user_name, user_id):

    # open followers page
    driver.get(f"https://www.instagram.com/{user_name}/followers/")

    followers_endpoint = config["instagram"]["followers_endpoint"].replace("{user_id}", user_id)
    headers = build_headers(config, driver)

    # get followers
    max_id = 0
    followers = []

    while True:

        params = {
            "count": 100,
            "max_id": max_id
        }

        response = requests.get(followers_endpoint, params=params, headers=headers)

        if response.status_code == 200 and response.json()["status"] == "ok":

            data = response.json()

            followers.extend(data["users"])

            if "next_max_id" in data:
                max_id = data["next_max_id"]
            else:
                break

    return followers


def scrap_following(config, driver, user_name, user_id):

    # open following page
    driver.get(f"https://www.instagram.com/{user_name}/following/")

    following_endpoint = config["instagram"]["following_endpoint"].replace("{user_id}", user_id)
    headers = build_headers(config, driver)

    # get following
    max_id = 0
    following = []

    while True:

        params = {
            "count": 100,
            "max_id": max_id
        }

        response = requests.get(following_endpoint, params=params, headers=headers)

        if response.status_code == 200 and response.json()["status"] == "ok":

            data = response.json()

            following.extend(data["users"])

            if "next_max_id" in data:
                max_id = data["next_max_id"]
            else:
                break

    return following


def scrap_hashtag_following(config, driver, user_name, user_id):

    # open hashtag following page
    driver.get(f"https://www.instagram.com/{user_name}/hashtag_following/")
    hashtag_following_endpoint = config["instagram"]["graphql_query_endpoint"]
    headers = build_headers(config, driver)
    params = {
        "query_hash": config["instagram"]["query_hashes"]["hashtag_following"],
        "variables": "{" + f'"id": "{user_id}"' + "}"
    }

    try:
        response = requests.get(hashtag_following_endpoint, params=params, headers=headers)

        if response.status_code == 200 and response.json()["status"] == "ok":
            hashtag_following = response.json()["data"]["user"]["edge_following_hashtag"]["edges"]

        else:
            raise Exception("status code != 200 or response.json.status != ok")

    except Exception as e:
        raise Exception()
    

    
    hashtag_following_refined = []
    for elem in hashtag_following:
        hashtag_following_refined.append(elem["node"])

    return hashtag_following_refined


def scrap_posts(config, driver, user_name, user_id):

    # open posts page
    driver.get(f"https://www.instagram.com/{user_name}/")
    posts_endpoint = config["instagram"]["feed_endpoint"].replace("{user_id}", user_id)
    headers = build_headers(config, driver)
    params = {
        "count": 20,
    }

    posts = []
    more_available = False

    response = requests.get(posts_endpoint, params=params, headers=headers)

    if response.status_code == 200 and response.json()["status"] == "ok":
        data = response.json()
        posts.extend(data["items"])
        more_available = data["more_available"]

    while more_available:

        params = {
            "count": 20,
            "max_id": data["next_max_id"]
        }

        response = requests.get(posts_endpoint, params=params, headers=headers)

        if response.status_code == 200 and response.json()["status"] == "ok":
            data = response.json()
            posts.extend(data["items"])
            more_available = data["more_available"]
        
        else:
            more_available = False

    return posts


def scrap_reels(config, driver, user_name, user_id):

    # open reels page
    driver.get(f"https://www.instagram.com/{user_name}/reels/")
    reels_endpoint = config["instagram"]["clips_endpoint"]
    headers = build_headers(config, driver)

    payload = {
        "target_user_id": user_id,
        "page_size": 25,
        "include_feed_video": True
    }

    reels = []
    more_available = False

    response = requests.post(reels_endpoint, data=payload, headers=headers)

    if response.status_code == 200 and response.json()["status"] == "ok":
        data = response.json()
        reels.extend(data["items"])
        more_available = data["paging_info"]["more_available"]

    while more_available:

        payload = {
            "target_user_id": user_id,
            "page_size": 25,
            "include_feed_video": True,
            "max_id": data["paging_info"]["max_id"]
        }

        response = requests.post(reels_endpoint, data=payload, headers=headers)

        if response.status_code == 200 and response.json()["status"] == "ok":
            data = response.json()
            reels.extend(data["items"])
            more_available = data["paging_info"]["more_available"]
        
        else:
            more_available = False

    for i in range(len(reels)):
        reels[i] = reels[i]["media"]

    return reels


def scroll_down(driver):
    driver.execute_script("window.scroll({ top: document.body.scrollHeight, left: 0, behavior: 'smooth' });")


# images
def download_media_type_1(post, output_directory):
    media_id = post["pk"]
    media_height = post["original_height"]
    media_width = post["original_width"]
    media_url = post["image_versions2"]["candidates"][0]["url"]
    output_path = Path(output_directory, f"{media_id}.jpg")

    # skip if media already exists
    if output_path.exists():
        print(f"skipping, media already exists [ {output_path} ]")
        return

    for media in post["image_versions2"]["candidates"]:
        if media["height"] == media_height and media["width"] == media_width:
            media_url = media["url"]
            break

    download_binary(media_url, output_path)


    # print("media_id:", media_id)
    # print("media_height:", media_height)
    # print("media_width", media_width)
    # print("media_url", media_url)


# videos 
def download_media_type_2(post, output_directory):
    media_id = post["pk"]
    media_height = post["original_height"]
    media_width = post["original_width"]
    media_url = post["video_versions"][0]["url"]
    output_path = Path(output_directory, f"{media_id}.mp4")

    # skip if media already exists
    if output_path.exists():
        print(f"skipping, media already exists [ {output_path} ]")
        return

    for media in post["video_versions"]:
        if media["height"] == media_height and media["width"] == media_width:
            media_url = media["url"]
            break

    download_binary(media_url, output_path)


    # print("media_id:", media_id)
    # print("media_height:", media_height)
    # print("media_width", media_width)
    # print("media_url", media_url)


# carrousel
def download_media_type_8(post, output_directory):
    carousel_id = post["pk"]
    carousel_media_count = post["carousel_media_count"]
    carousel_media = post["carousel_media"]

    # print("carousel_id:", carousel_id)
    # print("carousel_media_count:", carousel_media_count)

    for media in carousel_media:
        carousel_folder_path = Path(output_directory, f"{carousel_id}")
    
        # create carousel_folder_path if not exists already
        if not carousel_folder_path.exists():
            carousel_folder_path.mkdir(parents=True)
        
        if media["media_type"] == 1:
            download_media_type_1(media, carousel_folder_path)

        elif media["media_type"] == 2:
            download_media_type_2(media, carousel_folder_path)

        else:
            print("some other media type found:", media["media_type"])
