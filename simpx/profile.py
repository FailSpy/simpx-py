import asyncio
import json
import os
from typing import Dict, Optional, Any, List, Union, Tuple
from dataclasses import dataclass, field, asdict

from .client import ChatClient
from .command import Profile as SimpleXProfile
from .qr import print_qr_to_terminal

@dataclass
class BotProfile:
    """
    Represents a SimpleX bot profile with configuration options.
    This class abstracts the SimpleX profile management from the bot logic.
    """
    # Basic profile information
    display_name: str
    full_name: str
    image: Optional[str] = None
    
    # Bot configuration
    description: str = "A SimpleX bot built with SimpleXBot framework"
    auto_accept_contacts: bool = True
    welcome_message: Optional[str] = None
    auto_accept_message: Optional[str] = None
    command_prefix: str = "!"
    
    # Server configuration
    server_url: str = "ws://localhost:5225"
    
    # Storage
    config_file: Optional[str] = None
    
    # Runtime attributes (not saved to config)
    profile_id: Optional[int] = field(default=None)  # Now included in serialization
    user_id: Optional[int] = field(default=None, repr=False)
    contact_id: Optional[int] = field(default=None, repr=False)
    address: Optional[str] = field(default=None, repr=False)
    
    @property
    def simplex_profile(self) -> SimpleXProfile:
        """Convert to SimpleX profile format."""
        return {
            "displayName": self.display_name,
            "fullName": self.full_name,
            "image": self.image
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a dictionary for serialization."""
        # Include profile_id in the serialized data but exclude other runtime attributes
        data = asdict(self)
        data.pop("user_id")
        data.pop("contact_id")
        data.pop("address")
        
        # Always include profile_id in serialized data, even if None
        # This allows users to add a profile_id to the JSON file
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotProfile':
        """Create a profile from a dictionary."""
        # Filter out keys that are not part of the dataclass
        valid_fields = [f.name for f in fields(cls)]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def save(self, config_file: Optional[str] = None) -> None:
        """Save the profile to a JSON file."""
        file_path = config_file or self.config_file
        if not file_path:
            raise ValueError("Config file path not specified")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        # Update config_file if it was provided
        if config_file:
            self.config_file = config_file
    
    @classmethod
    def load(cls, config_file: str) -> 'BotProfile':
        """Load a profile from a JSON file."""
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        profile = cls.from_dict(data)
        profile.config_file = config_file
        return profile


class ProfileManager:
    """
    Manages SimpleX bot profiles and their interaction with the SimpleX client.
    Supports multiple bot profiles and users on the same daemon.
    """
    
    def __init__(self):
        self.client: Optional[ChatClient] = None
        self.current_profile: Optional[BotProfile] = None
        self.profiles: Dict[str, BotProfile] = {}
        self.users_map: Dict[int, int] = {}  # Maps profile_id to user_id
    
    async def initialize(self, 
                         profile: Optional[BotProfile] = None, 
                         server_url: Optional[str] = None) -> ChatClient:
        """
        Initialize the profile manager with a client connection.
        
        Args:
            profile: The bot profile to use
            server_url: Override the server URL from the profile
            
        Returns:
            The initialized ChatClient
        """
        # Use server URL from arguments or profile or default
        server = server_url
        if not server and profile:
            server = profile.server_url
        if not server and self.current_profile:
            server = self.current_profile.server_url
        if not server:
            server = "ws://localhost:5225"
        
        # Initialize client
        self.client = await ChatClient.create(server)
        
        # Get list of existing users/profiles
        existing_profiles = await self._get_existing_profiles()
        
        # If no profile provided, check if we can use current profile
        if not profile and not self.current_profile:
            # Try to use the profile from the server if there is an active user
            existing_user = await self.client.api_get_active_user()
            if existing_user:
                # Create a profile from the existing user
                profile_id = existing_user["profile"].get("profileId")
                self.current_profile = BotProfile(
                    display_name=existing_user["profile"]["displayName"],
                    full_name=existing_user["profile"]["fullName"],
                    image=existing_user["profile"].get("image"),
                    server_url=server
                )
                self.current_profile.profile_id = profile_id
                self.current_profile.user_id = existing_user["userId"]
                self.current_profile.contact_id = existing_user["userContactId"]
                print(f"Using existing profile: {self.current_profile.display_name} (ID: {profile_id})")
            else:
                raise ValueError("No profile provided and no existing profile found on server")
        elif profile:
            self.current_profile = profile
        
        # Set up the profile with the SimpleX server
        await self._setup_profile(existing_profiles)
        
        # Save updated profile with profile_id if it was loaded from a file
        # This ensures the profile_id gets saved back to the JSON
        if self.current_profile and self.current_profile.config_file:
            self.current_profile.save()
            print(f"Updated profile file with profile ID: {self.current_profile.profile_id}")
        
        return self.client
    
    async def _get_existing_profiles(self) -> Dict[int, Tuple[str, str, int]]:
        """
        Get a mapping of existing profile IDs to (display_name, full_name, user_id) tuples.
        
        Returns:
            Dictionary mapping profile IDs to profile info tuples
        """
        try:
            # Try to get list of users
            response = await self.client.send_chat_command({"type": "listUsers"})
            if response["type"] == "usersList":
                profiles = {}
                for user_info in response.get("users", []):
                    user = user_info.get("user", {})
                    profile = user.get("profile", {})
                    profile_id = profile.get("profileId")
                    if profile_id is not None:
                        display_name = profile.get("displayName", "")
                        full_name = profile.get("fullName", "")
                        user_id = user.get("userId")
                        profiles[profile_id] = (display_name, full_name, user_id)
                        # Update the users map
                        if user_id is not None:
                            self.users_map[profile_id] = user_id
                return profiles
        except Exception as e:
            print(f"Error getting existing profiles: {e}")
        
        return {}
    
    async def _setup_profile(self, existing_profiles: Dict[int, Tuple[str, str, int]]) -> None:
        """
        Set up the bot profile with the SimpleX server.
        
        Args:
            existing_profiles: Dictionary of existing profile IDs to profile info
        """
        if not self.client or not self.current_profile:
            raise ValueError("Client or profile not initialized")
        
        # Check if we're trying to use a specific profile ID
        target_profile_id = self.current_profile.profile_id
        
        if target_profile_id is not None:
            # Case 1: Specific profile ID requested
            if target_profile_id in existing_profiles:
                # Profile exists, try to activate it and update if needed
                await self._activate_existing_profile(target_profile_id, existing_profiles)
            else:
                # Profile ID provided but not found
                raise ValueError(
                    f"Profile ID {target_profile_id} not found. Profile IDs cannot be set on creation, "
                    f"they must reference existing profiles. Available profile IDs: {list(existing_profiles.keys())}"
                )
        else:
            # Case 2: No specific profile ID requested
            # Try to find a profile with matching display_name
            matching_profile_id = None
            for profile_id, (display_name, _, _) in existing_profiles.items():
                if display_name == self.current_profile.display_name:
                    matching_profile_id = profile_id
                    break
            
            if matching_profile_id is not None:
                # Use existing profile with matching name, but update it with current settings
                print(f"Found existing profile with matching name, ID: {matching_profile_id}")
                self.current_profile.profile_id = matching_profile_id
                await self._activate_existing_profile(matching_profile_id, existing_profiles)
            else:
                # Create a new profile
                await self._create_new_profile()
        
        # Set up connection address
        await self._setup_address()
        
        # Configure auto-accept if enabled
        if self.current_profile.auto_accept_contacts:
            auto_reply = None
            if self.current_profile.auto_accept_message:
                auto_reply = {"type": "text", "text": self.current_profile.auto_accept_message}
            
            await self.client.enable_address_auto_accept(
                accept_incognito=True,
                auto_reply=auto_reply
            )
        
        print(f"Profile active: {self.current_profile.display_name} (ID: {self.current_profile.profile_id})")
        if self.current_profile.address:
            print(f"Bot address: {self.current_profile.address}")
            print_qr_to_terminal(self.current_profile.address)
    
    async def _activate_existing_profile(self, 
                                        profile_id: int, 
                                        existing_profiles: Dict[int, Tuple[str, str, int]]) -> None:
        """
        Activate an existing profile and update if needed.
        
        Args:
            profile_id: The ID of the profile to activate
            existing_profiles: Dictionary of existing profile IDs to profile info
        """
        display_name, full_name, user_id = existing_profiles[profile_id]
        
        # Store the profile ID
        self.current_profile.profile_id = profile_id
        
        # Get current active user
        active_user = await self.client.api_get_active_user()
        
        # Check if the target profile is already active
        if active_user and active_user.get("profile", {}).get("profileId") == profile_id:
            # Profile already active, just update its info
            self.current_profile.user_id = active_user["userId"]
            self.current_profile.contact_id = active_user["userContactId"]
            
            # Check if profile needs updating
            update_needed = (
                self.current_profile.display_name != display_name or
                self.current_profile.full_name != full_name or
                self.current_profile.image != active_user["profile"].get("image")
            )
            
            if update_needed:
                # Update existing profile
                await self.client.api_update_profile(
                    active_user["userId"],
                    self.current_profile.simplex_profile
                )
                print(f"Updated profile: {self.current_profile.display_name} (ID: {profile_id})")
        else:
            # Need to switch users
            # First, stop the chat if it's running
            try:
                await self.client.api_stop_chat()
            except Exception as e:
                print(f"Warning: Error stopping chat (this is expected if chat wasn't running): {e}")
            
            # Then, switch users by creating an "activeUser" with the existing profile ID
            # We need to first get the actual user ID from the users map
            if user_id is None:
                raise ValueError(f"User ID not found for profile ID {profile_id}")
            
            # Construct a request to set the active user
            # Note: This is currently using a direct command since there isn't an API method for this
            cmd = f"/_use {user_id}"
            r = await self.client.send_chat_cmd_str(cmd)
            
            if r["type"] == "activeUser":
                self.current_profile.user_id = r["user"]["userId"]
                self.current_profile.contact_id = r["user"]["userContactId"]
                
                # Update the profile if needed
                update_needed = (
                    self.current_profile.display_name != r["user"]["profile"]["displayName"] or
                    self.current_profile.full_name != r["user"]["profile"]["fullName"] or
                    self.current_profile.image != r["user"]["profile"].get("image")
                )
                
                if update_needed:
                    await self.client.api_update_profile(
                        self.current_profile.user_id,
                        self.current_profile.simplex_profile
                    )
                    print(f"Updated profile: {self.current_profile.display_name} (ID: {profile_id})")
            else:
                raise ValueError(f"Failed to set active user for profile ID {profile_id}: {r}")
            
            # Restart the chat
            await self.client.api_start_chat()
    
    async def _create_new_profile(self) -> None:
        """Create a new profile on the SimpleX server."""
        # Create a new user profile
        user = await self.client.api_create_active_user(
            self.current_profile.simplex_profile,
            same_servers=True,
            past_timestamp=False
        )
        print(f"Created new profile: {self.current_profile.display_name}")
        
        # Store user information
        self.current_profile.user_id = user["userId"]
        self.current_profile.contact_id = user["userContactId"]
        
        # Get the profile ID from the response
        self.current_profile.profile_id = user["profile"].get("profileId")
        
        # Update the users map
        if self.current_profile.profile_id is not None:
            self.users_map[self.current_profile.profile_id] = self.current_profile.user_id
    
    async def _setup_address(self) -> None:
        """Set up the SimpleX address for the bot."""
        if not self.client:
            raise ValueError("Client not initialized")
        
        # Get or create the bot's address
        address = await self.client.api_get_user_address()
        if not address:
            address = await self.client.api_create_user_address()
        
        self.current_profile.address = address
    
    def add_profile(self, profile: BotProfile, name: str) -> None:
        """
        Add a profile to the manager.
        
        Args:
            profile: The profile to add
            name: A name to identify the profile
        """
        self.profiles[name] = profile
        
        # Set as current if none is set
        if not self.current_profile:
            self.current_profile = profile
    
    async def switch_profile(self, name: str) -> BotProfile:
        """
        Switch to a different profile.
        
        Args:
            name: The name of the profile to switch to
            
        Returns:
            The activated profile
        """
        if name not in self.profiles:
            raise ValueError(f"Profile '{name}' not found")
        
        # Save the previous profile's information if it exists
        previous_profile = self.current_profile
        if previous_profile and previous_profile.config_file:
            previous_profile.save()
        
        # Set the new profile
        self.current_profile = self.profiles[name]
        
        # If client is initialized, switch to the new profile
        if self.client:
            # Get existing profiles first
            existing_profiles = await self._get_existing_profiles()
            
            # Set up the new profile
            await self._setup_profile(existing_profiles)
            
            # Save the updated profile with profile_id if it was loaded from a file
            if self.current_profile.config_file:
                self.current_profile.save()
        
        return self.current_profile
    
    async def list_available_profiles(self) -> Dict[int, Tuple[str, str]]:
        """
        Get a list of available profiles on the server.
        
        Returns:
            Dictionary mapping profile IDs to (display_name, full_name) tuples
        """
        if not self.client:
            raise ValueError("Client not initialized")
        
        existing_profiles = await self._get_existing_profiles()
        return {pid: (name, fullname) for pid, (name, fullname, _) in existing_profiles.items()}
    
    @classmethod
    async def load_profiles(cls, profiles_dir: str) -> 'ProfileManager':
        """
        Load all profiles from a directory.
        
        Args:
            profiles_dir: Directory containing profile JSON files
            
        Returns:
            A ProfileManager with all loaded profiles
        """
        manager = cls()
        
        if not os.path.isdir(profiles_dir):
            os.makedirs(profiles_dir, exist_ok=True)
            return manager
        
        for filename in os.listdir(profiles_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(profiles_dir, filename)
                try:
                    profile = BotProfile.load(file_path)
                    name = filename.rsplit('.', 1)[0]  # Remove .json extension
                    manager.add_profile(profile, name)
                except Exception as e:
                    print(f"Error loading profile {filename}: {e}")
        
        return manager


# Field function for dataclass
def fields(dataclass_type):
    return dataclass_type.__dataclass_fields__.values()
