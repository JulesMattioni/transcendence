class ReaderStorage:

    @staticmethod
    def read_bytes(filepath: str) -> bytes:
        with open(filepath, "rb") as f:
            return f.read()
