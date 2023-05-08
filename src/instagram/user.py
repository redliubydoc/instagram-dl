from pathlib import Path

from common.utils import read_json
from common.utils import save_json
from common.utils import create_directory_structure


class User: 

    def __init__(
        self,
        user=None,
        posts=None,
        reels=None,
        following=None,
        followers=None,
        hashtag_following=None
    ) -> None:

        self.config = read_json(Path("resources", "config.json"))
        
        self.user = user
        self.posts = posts
        self.reels = reels
        self.following = following
        self.followers = followers
        self.hashtag_following = hashtag_following

        self.directories = {
            "data": Path(Path.home(), "Desktop", self.config["application"]["name"], self.username, "data"),
            "reels": Path(Path.home(), "Desktop", self.config["application"]["name"], self.username, "reels"),
            "posts.images": Path(Path.home(), "Desktop", self.config["application"]["name"], self.username, "posts", "images"),
            "posts.videos": Path(Path.home(), "Desktop", self.config["application"]["name"], self.username, "posts", "videos"),
            "posts.carousels": Path(Path.home(), "Desktop", self.config["application"]["name"], self.username, "posts", "carousels")
        }

        create_directory_structure(self.directories.values())

    @property
    def data_directory(self) -> Path:
        return Path(self.directories["data"])

    @property
    def reels_directory(self) -> Path:
        return Path(self.directories["reels"])

    @property
    def posts_images_directory(self) -> Path:
        return Path(self.directories["posts.images"])

    @property
    def posts_videos_directory(self) -> Path:
        return Path(self.directories["posts.videos"])

    @property
    def posts_carousels_directory(self) -> Path:
        return Path(self.directories["posts.carousels"])

    @property
    def username(self):
        return self.user["username"] if "username" in self.user.keys() else None

    @property
    def id(self):
        return self.user["id"] if "id" in self.user.keys() else None

    @property
    def is_accessible(self):

        # user is public or I am following the user
        _return = self.user["followed_by_viewer"] or self.user["is_private"]
        return _return

    @property
    def followers_count(self):
        return self.user["edge_followed_by"]["count"] if "edge_followed_by" in self.user.keys() else None

    @property
    def following_count(self):
        return self.user["edge_follow"]["count"] if "edge_follow" in self.user.keys() else None

    @property
    def posts_count(self):
        return self.user["edge_owner_to_timeline_media"]["count"] if "edge_owner_to_timeline_media" in self.user.keys() else None
