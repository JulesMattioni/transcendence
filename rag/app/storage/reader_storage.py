class ReaderStorage:
    """
    Read-only access to the uploads volume shared with the core service.

    core writes the binaries; rag only reads them back during ingestion,
    so this layer never creates or deletes files.
    """

    @staticmethod
    def read_bytes(filepath: str) -> bytes:
        """
        Read a stored binary from disk in full.

        Args:
            filepath: Path of the binary on the shared uploads volume.

        Returns:
            The file's raw bytes.

        Raises:
            FileNotFoundError: If no file exists at filepath.
        """

        with open(filepath, "rb") as f:
            return f.read()
