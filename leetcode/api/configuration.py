from typing import Dict


class Configuration:
    def __init__(self):
        self.auth: Dict[str, str] = {}

    def get(self, key: str) -> str:
        """
        Get the value of the configuration key.

        :param key: The key to get the value for.
        :return: The value of the key.
        """
        return self.auth.get(key, "")

    def set(self, key: str, value: str):
        """
        Set the value of the configuration key.

        :param key: The key to set the value for.
        :param value: The value to set.
        """
        self.auth[key] = value
