from pathlib import Path

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from common.myutllib import Url

from instagram.user import User

from common.utils import read_json
from common.utils import save_json
from common.utils import create_directory_structure

from instagram.utils import download_media_type_1
from instagram.utils import download_media_type_2
from instagram.utils import download_media_type_8

import requests

class Instagram:

    def __init__(self) -> None:
        
        self.config = read_json(Path("resources", "config.json"))
        
        self.user = None
        self.driver = None

        create_directory_structure([
            Path(self.config["browser"]["firefox"]["log_path"]).parent
        ])

        self.__open()

    def __open(self) -> None:

        options = Options()
        service = Service(log_path=self.config["browser"]["firefox"]["log_path"])

        arguments = self.config["browser"]["firefox"]["arguments"] + [
            "--url",
            self.config["instagram"]["url"]
        ]

        for argument in arguments:
            options.add_argument(argument)

        self.driver = Firefox(options=options, service=service)
        self.driver.maximize_window()

    def close(self):
        self.driver and self.driver.quit()

    def __build_request_headers(self):

        csrftoken = ""
        user_agent = self.driver.execute_script("return navigator.userAgent;")
        cookies_string = ""

        for cookie in self.driver.get_cookies():
            cookies_string += cookie["name"] + "=" + cookie["value"] + "; "

            if cookie["name"] == "csrftoken":
                csrftoken = cookie["value"]

        headers = self.config["headers"]
        headers["user-agent"] = user_agent
        headers["referer"] = self.driver.execute_script("return location.href")
        headers["cookie"] = cookies_string
        headers["x-ig-app-id"] = self.config["instagram"]["app_id"]
        headers["x-csrftoken"] = csrftoken
        headers["x-ig-www-claim"] = self.driver.execute_script("return window.sessionStorage.getItem(\"www-claim-v2\");")

        return headers

    def scrap_web_profile_info(self, user: User) -> User:

        # open profile page
        self.driver.get(str(Url(self.config["instagram"]["url"], user.username)))

        # get web profile info
        web_profile_info_endpoint = self.config["instagram"]["web_profile_info_endpoint"]
        params = { "username": user.username }
        headers = self.__build_request_headers()

        try:
            response = requests.get(web_profile_info_endpoint, params=params, headers=headers)

            if response.status_code == 200 and response.json()["status"] == "ok":
                data = response.json()["data"]

            else:
                raise Exception("status code != 200 or response.json.status != ok")

        except Exception as e:
            self.config["application"]["print_errs"] and print(e)
            raise Exception()
        
        user.user = data["user"]

        return user

    def scrap_posts_info(self, user: User) -> User:

        # open posts page
        self.driver.get(str(Url(self.config["instagram"]["url"], user.username)))

        posts_endpoint = self.config["instagram"]["feed_endpoint"].replace("{user_id}", user.id)
        params = { "count": 20 }
        headers = self.__build_request_headers()

        posts = []
        more_available = False

        try:
            response = requests.get(posts_endpoint, params=params, headers=headers)

            if response.status_code == 200 and response.json()["status"] == "ok":
                data = response.json()
                posts.extend(data["items"])
                more_available = data["more_available"]

            else:
                raise Exception("status code != 200 or response.json.status != ok")
            
        except Exception as e:
            self.config["application"]["print_errs"] and print(e)
            raise Exception()

        while more_available:

            params = {
                "count": 20,
                "max_id": data["next_max_id"]
            }

            try:
                response = requests.get(posts_endpoint, params=params, headers=headers)

                if response.status_code == 200 and response.json()["status"] == "ok":
                    data = response.json()
                    posts.extend(data["items"])
                    more_available = data["more_available"]

                else:
                    raise Exception("status code != 200 or response.json.status != ok")
                
            except Exception as e:
                raise Exception()

        user.posts = posts

        return user

    def scrap_reels_info(self, user: User) -> User:

        # open reels page
        self.driver.get(f"https://www.instagram.com/{user.username}/reels/")

        reels_endpoint = self.config["instagram"]["clips_endpoint"]
        headers = self.__build_request_headers()

        payload = {
            "target_user_id": user.id,
            "page_size": 25,
            "include_feed_video": True
        }

        reels = []
        more_available = False

        try:
            response = requests.post(reels_endpoint, data=payload, headers=headers)

            if response.status_code == 200 and response.json()["status"] == "ok":
                data = response.json()
                reels.extend(data["items"])
                more_available = data["paging_info"]["more_available"]
            
            else:
                raise Exception("status code != 200 or response.json.status != ok")
                
        except Exception as e:
            raise Exception()


        while more_available:

            payload = {
                "target_user_id": user.id,
                "page_size": 25,
                "include_feed_video": True,
                "max_id": data["paging_info"]["max_id"]
            }

            try:
                response = requests.post(reels_endpoint, data=payload, headers=headers)

                if response.status_code == 200 and response.json()["status"] == "ok":
                    data = response.json()
                    reels.extend(data["items"])
                    more_available = data["paging_info"]["more_available"]
                
                else:
                    raise Exception("status code != 200 or response.json.status != ok")
            
            except Exception as e:
                raise Exception()

        for i in range(len(reels)):
            reels[i] = reels[i]["media"]

        user.reels = reels

        return user

    def scrap_followers_info(self, user: User) -> User:

        # open followers page
        self.driver.get(f"https://www.instagram.com/{user.username}/followers/")

        followers_endpoint = self.config["instagram"]["followers_endpoint"].replace("{user_id}", user.id)
        params = { "count": 100 }
        headers = self.__build_request_headers()

        # get followers
        data = None
        followers = []

        try:
            response = requests.get(followers_endpoint, params=params, headers=headers)

            if response.status_code == 200 and response.json()["status"] == "ok":
                data = response.json()
                followers.extend(data["users"])

            else:
                raise Exception("status code != 200 or response.json.status != ok")
            
        except Exception as e:
            raise Exception()


        while data and "next_max_id" in data:

            params = { 
                "count": 100,
                "max_id": data["next_max_id"] 
            }

            try:
                response = requests.get(followers_endpoint, params=params, headers=headers)

                if response.status_code == 200 and response.json()["status"] == "ok":
                    data = response.json()
                    followers.extend(data["users"])

                else:
                    raise Exception("status code != 200 or response.json.status != ok")
                
            except Exception as e:
                raise Exception()

        user.followers = followers

        return user

    def scrap_following_info(self, user: User) -> User:

        # open following page
        self.driver.get(f"https://www.instagram.com/{user.username}/following/")

        following_endpoint = self.config["instagram"]["following_endpoint"].replace("{user_id}", user.id)
        params = { "count": 100 }
        headers = self.__build_request_headers()

        # get following
        data = None
        following = []

        try:
            response = requests.get(following_endpoint, params=params, headers=headers)

            if response.status_code == 200 and response.json()["status"] == "ok":
                data = response.json()
                following.extend(data["users"])

            else:
                raise Exception("status code != 200 or response.json.status != ok")
            
        except Exception as e:
            raise Exception()


        while data and "next_max_id" in data:

            params = { 
                "count": 100,
                "max_id": data["next_max_id"] 
            }

            try:
                response = requests.get(following_endpoint, params=params, headers=headers)

                if response.status_code == 200 and response.json()["status"] == "ok":
                    data = response.json()
                    following.extend(data["users"])
                    
                else:
                    raise Exception("status code != 200 or response.json.status != ok")
                
            except Exception as e:
                raise Exception()

        user.following = following

        return user


    def scrap_hashtag_following_info(self, user: User) -> User:

        # open hashtag following page
        self.driver.get(f"https://www.instagram.com/{user.username}/hashtag_following/")

        hashtag_following_endpoint = self.config["instagram"]["graphql_query_endpoint"]
        headers = self.__build_request_headers()
        params = {
            "query_hash": self.config["instagram"]["query_hashes"]["hashtag_following"],
            "variables": "{" + f'"id": "{user.id}"' + "}"
        }

        try:
            response = requests.get(hashtag_following_endpoint, params=params, headers=headers)

            if response.status_code == 200 and response.json()["status"] == "ok":
                hashtag_following = response.json()["data"]["user"]["edge_following_hashtag"]["edges"]

            else:
                raise Exception("status code != 200 or response.json.status != ok")

        except Exception as e:
            raise Exception()
        
        for i in range(len(hashtag_following)):
            hashtag_following[i] = hashtag_following[i]["node"]

        user.hashtag_following = hashtag_following
        
        return user



    # media_type = 1 => image
    # media_type = 2 => video
    # media_type = 8 => carousal
    # media_type = None => all
    def download_posts(self, user: User, media_type=None) -> None:

        posts_not_downloaded = []

        for post in user.posts:
            # log unknown media_type
            post["media_type"] not in (1, 2, 8) and print(f"unknown media_type: {post['media_type']}")

            if post["media_type"] == 1 and media_type in (None, post["media_type"]):

                try:
                    download_media_type_1(post, user.posts_images_directory)

                except Exception as e:
                    posts_not_downloaded.append({
                        "pk": post["pk"],
                        "code": post["code"],
                        "reason": "error"
                    })
                    self.config["application"]["print_errs"] and print(e)

            elif post["media_type"] == 2 and media_type in (None, post["media_type"]):

                try:
                    download_media_type_2(post, user.posts_videos_directory)

                except Exception as e:
                    posts_not_downloaded.append({
                        "pk": post["pk"],
                        "code": post["code"],
                        "reason": "error"
                    })
                    self.config["application"]["print_errs"] and print(e)

            elif post["media_type"] == 8 and media_type in (None, post["media_type"]):

                try:
                    download_media_type_8(post, user.posts_carousels_directory)

                except Exception as e:
                    posts_not_downloaded.append({
                        "pk": post["pk"],
                        "code": post["code"],
                        "reason": "error"
                    })
                    self.config["application"]["print_errs"] and print(e)

        save_json(posts_not_downloaded, Path(user.data_directory, "posts_not_downloaded.json"))

    def download_reels(self, user: User) -> None:

        reels_not_downloaded = []

        for reel in user.reels:
            # log unknown media_type
            reel["media_type"] not in (1, 2, 8) and print(f"unknown media_type: {reel['media_type']}")

            if reel["media_type"] == 2:
                if Path(user.posts_videos_directory, f"{reel['pk']}.mp4").exists():
                    reels_not_downloaded.append({
                        "pk": reel["pk"],
                        "code": reel["code"],
                        "reason": "common"
                    })
                    continue

                try:
                    download_media_type_2(reel, user.reels_directory)

                except Exception as e:
                    reels_not_downloaded.append({
                        "pk": reel["pk"],
                        "code": reel["code"],
                        "reason": "error"
                    })
                    self.config["application"]["print_errs"] and print(e)

        save_json(reels_not_downloaded, Path(user.data_directory, "reels_not_downloaded.json"))
