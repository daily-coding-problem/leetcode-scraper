from typing import Dict, Optional

class User:
    def __init__(self, data: Dict[str, any]):
        """
        Initializes a User instance with data from a dictionary.

        :param data: Dictionary containing user data.
        """
        self.user_id: Optional[int] = data.get("userId")
        self.is_signed_in: Optional[bool] = data.get("isSignedIn")
        self.is_mock_user: Optional[bool] = data.get("isMockUser")
        self.is_premium: Optional[bool] = data.get("isPremium")
        self.is_verified: Optional[bool] = data.get("isVerified")
        self.username: Optional[str] = data.get("username")
        self.real_name: Optional[str] = data.get("realName")
        self.avatar: Optional[str] = data.get("avatar")
        self.is_admin: Optional[bool] = data.get("isAdmin")
        self.is_superuser: Optional[bool] = data.get("isSuperuser")
        self.permissions: Optional[list] = data.get("permissions", [])
        self.is_translator: Optional[bool] = data.get("isTranslator")
        self.active_session_id: Optional[str] = data.get("activeSessionId")
        self.checked_in_today: Optional[bool] = data.get("checkedInToday")
        self.completed_feature_guides: Optional[list] = data.get("completedFeatureGuides", [])
        self.notification_status = data.get("notificationStatus", {})

    def __repr__(self):
        """
        Returns a string representation of the User object.

        :return: String representation.
        """
        return (
            f"User(username={self.username}, real_name={self.real_name}, "
            f"is_signed_in={self.is_signed_in}, is_premium={self.is_premium})"
        )

    def to_dict(self) -> Dict[str, any]:
        """
        Converts the User object to a dictionary.

        :return: Dictionary representation of the User object.
        """
        return {
            "userId": self.user_id,
            "isSignedIn": self.is_signed_in,
            "isMockUser": self.is_mock_user,
            "isPremium": self.is_premium,
            "isVerified": self.is_verified,
            "username": self.username,
            "realName": self.real_name,
            "avatar": self.avatar,
            "isAdmin": self.is_admin,
            "isSuperuser": self.is_superuser,
            "permissions": self.permissions,
            "isTranslator": self.is_translator,
            "activeSessionId": self.active_session_id,
            "checkedInToday": self.checked_in_today,
            "completedFeatureGuides": self.completed_feature_guides,
            "notificationStatus": self.notification_status,
        }
