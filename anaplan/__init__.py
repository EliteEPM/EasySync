"""
Anaplan Integration Python Library

This Library uses a combination of transactional and bulk APIs to provide a seamless
integration experience into Anaplan Models. Intended as an alternative to Anaplan Connect

Github repo: https://github.com/EliteEPM/EasySync
Also visit: https://github.com/EliteEPM/AnaplanAPILive

Author: Anirudh Nayak
License: MIT
"""

from anaplan.authentication import AnaplanAuth
from anaplan.dictionary import AnaplanModel
from anaplan.oauth_firstrun import oauth_device_firstrun
