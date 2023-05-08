class Url:
    
    def __init__(self, *args) -> None:

        args = list(args)

        for i in range(len(args) - 1, 0, -1):
            args[i - 1] = args[i - 1].rstrip("/") + "/" + args[i].lstrip("/")

        self.url = args[0] if args else ""

    def __str__(self) -> str:
        return self.url