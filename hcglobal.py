import sys
from datetime import datetime

LIB_DIR = f'{sys.path[0]}/lib'
MISC_DIR = f'{sys.path[0]}/misc'
UPDATED_APP_JSON = 'product/UpdatedApp.json'
PRODUCT_PRIVILEGE_PERMISSION_XML = 'product/etc/permissions/privapp-permissions-product.xml'
PRIVILEGE_PERMISSIONS = {
    'android.permission.WRITE_VERIFICATION_STATE_E2EE_CONTACT_KEYS',
    'deviceintegration.permission.MANAGE_CROSS_DEVICE',
    'android.permission.SATELLITE_COMMUNICATION',
    'android.permission.WRITE_OBB',
    'android.permission.LOCATION_BYPASS',
    'android.permission.ACCESS_IMS_CALL_SERVICE',
    'android.permission.EXEMPT_FROM_AUDIO_RECORD_RESTRICTIONS',
    'android.permission.ACCESS_UCE_PRESENCE_SERVICE',
    'android.permission.ACCESS_UCE_OPTIONS_SERVICE',
    'android.permission.SYSTEM_CAMERA',
    'android.permission.CAMERA_PRIVACY_ALLOWLIST',
    'android.permission.SEND_RESPOND_VIA_MESSAGE',
    'android.permission.SEND_SMS_NO_CONFIRMATION',
    'android.permission.CARRIER_FILTER_SMS',
    'android.permission.RECEIVE_EMERGENCY_BROADCAST',
    'android.permission.RECEIVE_BLUETOOTH_MAP',
    'android.permission.BIND_DIRECTORY_SEARCH',
    'android.permission.MODIFY_CELL_BROADCASTS',
    'com.android.voicemail.permission.WRITE_VOICEMAIL',
    'com.android.voicemail.permission.READ_VOICEMAIL',
    'android.permission.INSTALL_LOCATION_PROVIDER',
    'android.permission.INSTALL_LOCATION_TIME_ZONE_PROVIDER_SERVICE',
    'android.permission.HDMI_CEC',
    'android.permission.LOCATION_HARDWARE',
    'android.permission.ACCESS_CONTEXT_HUB',
    'android.permission.CONTROL_AUTOMOTIVE_GNSS',
    'android.permission.MANAGE_WIFI_NETWORK_SELECTION',
    'android.permission.MANAGE_WIFI_INTERFACES',
    'android.permission.READ_WIFI_CREDENTIAL',
    'android.permission.TETHER_PRIVILEGED',
    'android.permission.RECEIVE_WIFI_CREDENTIAL_CHANGE',
    'android.permission.OVERRIDE_WIFI_CONFIG',
    'android.permission.SCORE_NETWORKS',
    'android.permission.RESTART_WIFI_SUBSYSTEM',
    'android.permission.NETWORK_CARRIER_PROVISIONING',
    'android.permission.ACCESS_LOWPAN_STATE',
    'android.permission.CHANGE_LOWPAN_STATE',
    'android.permission.READ_LOWPAN_CREDENTIAL',
    'android.permission.MANAGE_LOWPAN_INTERFACES',
    'android.permission.THREAD_NETWORK_PRIVILEGED',
    'android.permission.WIFI_SET_DEVICE_MOBILITY_STATE',
    'android.permission.WIFI_UPDATE_USABILITY_STATS_SCORE',
    'android.permission.BLUETOOTH_PRIVILEGED',
    'android.permission.NFC_SET_CONTROLLER_ALWAYS_ON',
    'android.permission.SECURE_ELEMENT_PRIVILEGED_OPERATION',
    'android.permission.CONNECTIVITY_INTERNAL',
    'android.permission.CONNECTIVITY_USE_RESTRICTED_NETWORKS',
    'android.permission.NETWORK_SIGNAL_STRENGTH_WAKEUP',
    'android.permission.PACKET_KEEPALIVE_OFFLOAD',
    'android.permission.RECEIVE_DATA_ACTIVITY_CHANGE',
    'android.permission.LOOP_RADIO',
    'android.permission.NFC_HANDOVER_STATUS',
    'android.permission.UWB_PRIVILEGED',
    'android.permission.ACCESS_VIBRATOR_STATE',
    'android.permission.TURN_SCREEN_ON',
    'android.permission.MANAGE_FACTORY_RESET_PROTECTION',
    'android.permission.MANAGE_USB',
    'android.permission.MANAGE_DEBUGGING',
    'android.permission.ACCESS_MTP',
    'android.permission.INSTALL_DYNAMIC_SYSTEM',
    'android.permission.ACCESS_BROADCAST_RADIO',
    'android.permission.ACCESS_FM_RADIO',
    'android.permission.TV_INPUT_HARDWARE',
    'android.permission.CAPTURE_TV_INPUT',
    'android.permission.DVB_DEVICE',
    'android.permission.MANAGE_CARRIER_OEM_UNLOCK_STATE',
    'android.permission.MANAGE_USER_OEM_UNLOCK_STATE',
    'android.permission.READ_OEM_UNLOCK_STATE',
    'android.permission.CONFIGURE_FACTORY_RESET_PROTECTION',
    'android.permission.NOTIFY_PENDING_SYSTEM_UPDATE',
    'android.permission.CAMERA_DISABLE_TRANSMIT_LED',
    'android.permission.CAMERA_SEND_SYSTEM_EVENTS',
    'android.permission.MODIFY_PHONE_STATE',
    'android.permission.READ_PRECISE_PHONE_STATE',
    'android.permission.READ_PRIVILEGED_PHONE_STATE',
    'android.permission.REGISTER_SIM_SUBSCRIPTION',
    'android.permission.REGISTER_CALL_PROVIDER',
    'android.permission.REGISTER_CONNECTION_MANAGER',
    'android.permission.BIND_INCALL_SERVICE',
    'android.permission.NETWORK_SCAN',
    'android.permission.BIND_VISUAL_VOICEMAIL_SERVICE',
    'android.permission.BIND_SCREENING_SERVICE',
    'android.permission.BIND_CALL_REDIRECTION_SERVICE',
    'android.permission.BIND_CONNECTION_SERVICE',
    'android.permission.BIND_TELECOM_CONNECTION_SERVICE',
    'android.permission.CONTROL_INCALL_EXPERIENCE',
    'android.permission.RECEIVE_STK_COMMANDS',
    'android.permission.SEND_EMBMS_INTENTS',
    'android.permission.BIND_IMS_SERVICE',
    'android.permission.BIND_SATELLITE_SERVICE',
    'android.permission.WRITE_EMBEDDED_SUBSCRIPTIONS',
    'android.permission.WRITE_MEDIA_STORAGE',
    'android.permission.ALLOCATE_AGGRESSIVE',
    'android.permission.USE_RESERVED_DISK',
    'android.permission.REAL_GET_TASKS',
    'android.permission.START_TASKS_FROM_RECENTS',
    'android.permission.INTERACT_ACROSS_USERS',
    'android.permission.ACCESS_HIDDEN_PROFILES_FULL',
    'android.permission.MANAGE_USERS',
    'android.permission.QUERY_USERS',
    'android.permission.ACCESS_BLOBS_ACROSS_USERS',
    'android.permission.ACTIVITY_EMBEDDING',
    'android.permission.START_ACTIVITIES_FROM_BACKGROUND',
    'android.permission.START_FOREGROUND_SERVICES_FROM_BACKGROUND',
    'android.permission.BROADCAST_OPTION_INTERACTIVE',
    'android.permission.KILL_ALL_BACKGROUND_PROCESSES',
    'android.permission.GET_PROCESS_STATE_AND_OOM_SCORE',
    'android.permission.SET_DISPLAY_OFFSET',
    'android.permission.REQUEST_COMPANION_PROFILE_APP_STREAMING',
    'android.permission.REQUEST_COMPANION_PROFILE_NEARBY_DEVICE_STREAMING',
    'android.permission.REQUEST_COMPANION_PROFILE_COMPUTER',
    'android.permission.REQUEST_COMPANION_SELF_MANAGED',
    'android.permission.COMPANION_APPROVE_WIFI_CONNECTIONS',
    'android.permission.READ_WALLPAPER_INTERNAL',
    'android.permission.SET_TIME',
    'android.permission.SET_TIME_ZONE',
    'android.permission.SUGGEST_EXTERNAL_TIME',
    'android.permission.MANAGE_TIME_AND_ZONE_DETECTION',
    'android.permission.CHANGE_CONFIGURATION',
    'android.permission.WRITE_GSERVICES',
    'android.permission.FORCE_STOP_PACKAGES',
    'android.permission.RETRIEVE_WINDOW_CONTENT',
    'android.permission.SET_ANIMATION_SCALE',
    'android.permission.MOUNT_UNMOUNT_FILESYSTEMS',
    'android.permission.MOUNT_FORMAT_FILESYSTEMS',
    'android.permission.WRITE_APN_SETTINGS',
    'android.permission.CLEAR_APP_CACHE',
    'android.permission.ALLOW_ANY_CODEC_FOR_PLAYBACK',
    'android.permission.MANAGE_CA_CERTIFICATES',
    'android.permission.RECOVERY',
    'android.permission.READ_SYSTEM_UPDATE_INFO',
    'android.permission.UPDATE_CONFIG',
    'android.permission.QUERY_TIME_ZONE_RULES',
    'android.permission.UPDATE_TIME_ZONE_RULES',
    'android.permission.CHANGE_OVERLAY_PACKAGES',
    'android.permission.UPDATE_FONTS',
    'android.permission.LIST_ENABLED_CREDENTIAL_PROVIDERS',
    'android.permission.PROVIDE_DEFAULT_ENABLED_CREDENTIAL_SERVICE',
    'android.permission.PROVIDE_REMOTE_CREDENTIALS',
    'android.permission.WRITE_SECURE_SETTINGS',
    'android.permission.DUMP',
    'android.permission.CONTROL_UI_TRACING',
    'android.permission.READ_LOGS',
    'android.permission.SET_DEBUG_APP',
    'android.permission.READ_DROPBOX_DATA',
    'android.permission.SET_PROCESS_LIMIT',
    'android.permission.SET_ALWAYS_FINISH',
    'android.permission.SIGNAL_PERSISTENT_PROCESSES',
    'android.permission.REQUEST_INCIDENT_REPORT_APPROVAL',
    'android.permission.GET_ACCOUNTS_PRIVILEGED',
    'android.permission.STATUS_BAR',
    'android.permission.UPDATE_DEVICE_STATS',
    'android.permission.GET_APP_OPS_STATS',
    'android.permission.UPDATE_APP_OPS_STATS',
    'android.permission.SHUTDOWN',
    'android.permission.STOP_APP_SWITCHES',
    'android.permission.BIND_WALLPAPER',
    'android.permission.MANAGE_UI_TRANSLATION',
    'android.permission.MANAGE_VOICE_KEYPHRASES',
    'android.permission.KEYPHRASE_ENROLLMENT_APPLICATION',
    'android.permission.BIND_TV_AD_SERVICE',
    'android.permission.BIND_TV_INPUT',
    'android.permission.BIND_TV_INTERACTIVE_APP',
    'android.permission.BIND_TV_REMOTE_SERVICE',
    'android.permission.TV_VIRTUAL_REMOTE_CONTROLLER',
    'android.permission.CHANGE_HDMI_CEC_ACTIVE_SOURCE',
    'android.permission.MODIFY_PARENTAL_CONTROLS',
    'android.permission.READ_CONTENT_RATING_SYSTEMS',
    'android.permission.NOTIFY_TV_INPUTS',
    'android.permission.TUNER_RESOURCE_ACCESS',
    'android.permission.MEDIA_RESOURCE_OVERRIDE_PID',
    'android.permission.REGISTER_MEDIA_RESOURCE_OBSERVER',
    'android.permission.RESET_PASSWORD',
    'android.permission.LOCK_DEVICE',
    'android.permission.SCHEDULE_PRIORITIZED_ALARM',
    'android.permission.SCHEDULE_EXACT_ALARM',
    'android.permission.INSTALL_PACKAGES',
    'android.permission.INSTALL_SELF_UPDATES',
    'android.permission.INSTALL_PACKAGE_UPDATES',
    'com.android.permission.INSTALL_EXISTING_PACKAGES',
    'com.android.permission.USE_INSTALLER_V2',
    'android.permission.DELETE_CACHE_FILES',
    'android.permission.DELETE_PACKAGES',
    'android.permission.MOVE_PACKAGE',
    'android.permission.CHANGE_COMPONENT_ENABLED_STATE',
    'android.permission.LAUNCH_PERMISSION_SETTINGS',
    'android.permission.OBSERVE_GRANT_REVOKE_PERMISSIONS',
    'android.permission.REQUEST_OBSERVE_DEVICE_UUID_PRESENCE',
    'android.permission.CONTROL_DEVICE_LIGHTS',
    'android.permission.CONTROL_DISPLAY_SATURATION',
    'android.permission.CONTROL_DISPLAY_COLOR_TRANSFORMS',
    'android.permission.BRIGHTNESS_SLIDER_USAGE',
    'android.permission.ACCESS_AMBIENT_LIGHT_STATS',
    'android.permission.CONFIGURE_DISPLAY_BRIGHTNESS',
    'android.permission.CONTROL_VPN',
    'android.permission.CAPTURE_TUNER_AUDIO_INPUT',
    'android.permission.CAPTURE_AUDIO_OUTPUT',
    'android.permission.CAPTURE_MEDIA_OUTPUT',
    'android.permission.CAPTURE_VOICE_COMMUNICATION_OUTPUT',
    'android.permission.CAPTURE_AUDIO_HOTWORD',
    'android.permission.ACCESS_ULTRASOUND',
    'android.permission.SOUNDTRIGGER_DELEGATE_IDENTITY',
    'android.permission.MODIFY_AUDIO_ROUTING',
    'android.permission.MODIFY_AUDIO_SETTINGS_PRIVILEGED',
    'android.permission.CALL_AUDIO_INTERCEPTION',
    'android.permission.MODIFY_DEFAULT_AUDIO_EFFECTS',
    'android.permission.DISABLE_SYSTEM_SOUND_EFFECTS',
    'android.permission.REMOTE_DISPLAY_PROVIDER',
    'android.permission.MEDIA_CONTENT_CONTROL',
    'android.permission.SET_VOLUME_KEY_LONG_PRESS_LISTENER',
    'android.permission.SET_MEDIA_KEY_LISTENER',
    'android.permission.REBOOT',
    'android.permission.POWER_SAVER',
    'android.permission.BATTERY_PREDICTION',
    'android.permission.USER_ACTIVITY',
    'android.permission.MANAGE_LOW_POWER_STANDBY',
    'android.permission.SET_LOW_POWER_STANDBY_PORTS',
    'android.permission.BROADCAST_CLOSE_SYSTEM_DIALOGS',
    'android.permission.BROADCAST_NETWORK_PRIVILEGED',
    'android.permission.MASTER_CLEAR',
    'android.permission.CALL_PRIVILEGED',
    'android.permission.PERFORM_CDMA_PROVISIONING',
    'android.permission.PERFORM_SIM_ACTIVATION',
    'android.permission.CONTROL_LOCATION_UPDATES',
    'android.permission.ACCESS_CHECKIN_PROPERTIES',
    'android.permission.PACKAGE_USAGE_STATS',
    'android.permission.ACCESS_BROADCAST_RESPONSE_STATS',
    'android.permission.LOADER_USAGE_STATS',
    'android.permission.OBSERVE_APP_USAGE',
    'android.permission.CHANGE_APP_IDLE_STATE',
    'android.permission.CHANGE_APP_LAUNCH_TIME_ESTIMATE',
    'android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST',
    'android.permission.BATTERY_STATS',
    'android.permission.REGISTER_STATS_PULL_ATOM',
    'android.permission.BACKUP',
    'android.permission.RECOVER_KEYSTORE',
    'android.permission.BIND_REMOTEVIEWS',
    'android.permission.BIND_APPWIDGET',
    'android.permission.BIND_KEYGUARD_APPWIDGET',
    'android.permission.MODIFY_APPWIDGET_BIND_PERMISSIONS',
    'android.permission.GLOBAL_SEARCH',
    'android.permission.READ_SEARCH_INDEXABLES',
    'android.permission.WRITE_SETTINGS_HOMEPAGE_DATA',
    'android.permission.SET_WALLPAPER_COMPONENT',
    'android.permission.SET_WALLPAPER_DIM_AMOUNT',
    'android.permission.READ_DREAM_STATE',
    'android.permission.WRITE_DREAM_STATE',
    'android.permission.ACCESS_CACHE_FILESYSTEM',
    'android.permission.CRYPT_KEEPER',
    'android.permission.READ_NETWORK_USAGE_HISTORY',
    'android.permission.MODIFY_NETWORK_ACCOUNTING',
    'android.permission.MANAGE_SUBSCRIPTION_PLANS',
    'android.permission.PACKAGE_VERIFICATION_AGENT',
    'android.permission.MANAGE_ROLLBACKS',
    'android.permission.INTENT_FILTER_VERIFICATION_AGENT',
    'android.permission.SERIAL_PORT',
    'android.permission.UPDATE_LOCK',
    'android.permission.REQUEST_NOTIFICATION_ASSISTANT_SERVICE',
    'android.permission.ACCESS_NOTIFICATIONS',
    'android.permission.CHECK_REMOTE_LOCKSCREEN',
    'android.permission.MANAGE_FINGERPRINT',
    'android.permission.MANAGE_FACE',
    'android.permission.SET_BIOMETRIC_DIALOG_ADVANCED',
    'android.permission.CONTROL_KEYGUARD_SECURE_NOTIFICATIONS',
    'android.permission.MANAGE_WEAK_ESCROW_TOKEN',
    'android.permission.PROVIDE_TRUST_AGENT',
    'android.permission.SHOW_KEYGUARD_MESSAGE',
    'android.permission.LAUNCH_TRUST_AGENT_SETTINGS',
    'android.permission.PROVIDE_RESOLVER_RANKER_SERVICE',
    'android.permission.INVOKE_CARRIER_SETUP',
    'android.permission.ACCESS_NETWORK_CONDITIONS',
    'android.permission.ACCESS_DRM_CERTIFICATES',
    'android.permission.REMOVE_DRM_CERTIFICATES',
    'android.permission.BIND_CARRIER_MESSAGING_SERVICE',
    'android.permission.BIND_CARRIER_SERVICES',
    'android.permission.LOCAL_MAC_ADDRESS',
    'android.permission.DISPATCH_NFC_MESSAGE',
    'android.permission.MODIFY_DAY_NIGHT_MODE',
    'android.permission.ENTER_CAR_MODE_PRIORITIZED',
    'android.permission.HANDLE_CAR_MODE_CHANGES',
    'android.permission.SEND_CATEGORY_CAR_NOTIFICATIONS',
    'android.permission.RECEIVE_MEDIA_RESOURCE_USAGE',
    'android.permission.MANAGE_SOUND_TRIGGER',
    'android.permission.SOUND_TRIGGER_RUN_IN_BATTERY_SAVER',
    'android.permission.DISPATCH_PROVISIONING_MESSAGE',
    'android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME',
    'android.permission.NOTIFICATION_DURING_SETUP',
    'android.permission.MANAGE_CLOUDSEARCH',
    'android.permission.MANAGE_MUSIC_RECOGNITION',
    'android.permission.ACCESS_SMARTSPACE',
    'android.permission.ACCESS_CONTEXTUAL_SEARCH',
    'android.permission.MANAGE_WALLPAPER_EFFECTS_GENERATION',
    'android.permission.READ_RUNTIME_PROFILES',
    'android.permission.MODIFY_QUIET_MODE',
    'android.permission.CONTROL_REMOTE_APP_TRANSITION_ANIMATIONS',
    'android.permission.WATCH_APPOPS',
    'android.permission.MONITOR_DEFAULT_SMS_PACKAGE',
    'android.permission.BIND_EXPLICIT_HEALTH_CHECK_SERVICE',
    'android.permission.RECEIVE_SANDBOX_TRIGGER_AUDIO',
    'android.permission.SEND_DEVICE_CUSTOMIZATION_READY',
    'android.permission.SUBSTITUTE_SHARE_TARGET_APP_NAME_AND_ICON',
    'android.permission.LOG_COMPAT_CHANGE',
    'android.permission.READ_COMPAT_CHANGE_CONFIG',
    'android.permission.OVERRIDE_COMPAT_CHANGE_CONFIG',
    'android.permission.OVERRIDE_COMPAT_CHANGE_CONFIG_ON_RELEASE_BUILD',
    'android.permission.ALLOW_SLIPPERY_TOUCHES',
    'android.permission.ACCESS_TV_TUNER',
    'android.permission.ACCESS_TV_DESCRAMBLER',
    'android.permission.ACCESS_TV_SHARED_FILTER',
    'android.permission.MANAGE_GAME_MODE',
    'android.permission.ACCESS_FPS_COUNTER',
    'android.permission.MANAGE_GAME_ACTIVITY',
    'android.permission.SIGNAL_REBOOT_READINESS',
    'android.permission.SHOW_CUSTOMIZED_RESOLVER',
    'android.permission.RENOUNCE_PERMISSIONS',
    'android.permission.ACCESS_TUNED_INFO',
    'android.permission.READ_SAFETY_CENTER_STATUS',
    'android.permission.ACCESS_AMBIENT_CONTEXT_EVENT',
    'android.permission.SET_UNRESTRICTED_KEEP_CLEAR_AREAS',
    'android.permission.SET_UNRESTRICTED_GESTURE_EXCLUSION',
    'android.permission.TIS_EXTENSION_INTERFACE',
    'android.permission.WRITE_SECURITY_LOG',
    'android.permission.MANAGE_WEARABLE_SENSING_SERVICE',
    'android.permission.USE_ON_DEVICE_INTELLIGENCE',
    'android.permission.BIND_ON_DEVICE_INTELLIGENCE_SERVICE',
    'android.permission.QUERY_CLONED_APPS',
    'android.permission.GET_BINDING_UID_IMPORTANCE',
    'android.permission.PREPARE_FACTORY_RESET',
    'android.permission.OVERRIDE_SYSTEM_KEY_BEHAVIOR_IN_FOCUSED_WINDOW',
    'android.permission.READ_SYSTEM_GRAMMATICAL_GENDER',
    'android.permission.EMERGENCY_INSTALL_PACKAGES',
    'android.permission.SETUP_FSVERITY'
}


def log(string: str):
    now = datetime.now().strftime('[%m-%d %H:%M:%S]')
    print(f'{now} {string}')
