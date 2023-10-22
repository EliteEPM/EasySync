"""
Run this script as permanently alive to login to Anaplan and constantly check for 
new integration requests. If request is detected, use the anaplan library to upload, monitor
and close out the request

Visit https://github.com/EliteEPM/EasySync for a full How-To guide
"""

from dotenv import set_key
from anaplan import AnaplanAuth, oauth_device_firstrun

# This module saves basic, cert or oauth refresh token in an env file
# Avoid the hassle of hardcoding credentials into the main run file


def basic_authentication():
    """Simple function to load an env file with username and password, also ensures it's a valid login credential"""

    username = input("Enter your username: ")
    password = input("Enter your password: ")
    print(
        f"Basic authentication with username '{username}' and password '{password}'")
    confirmation = input("Is this information correct? (yes/no): ")

    if confirmation.lower() == "yes":
        print("Attempting authentication...")
        try:
            AnaplanAuth('basic', f'{username}:{password}').get_token()
            print('Successfully validated with Anaplan')
            set_key('creds.env', 'un', username)
            set_key('creds.env', 'pw', password)
            print('Credentials saved in local file!')
        except:
            print('Invalid, please try again')
    else:
        basic_authentication()


def certificate_authentication():
    """Simple function to load an env file with public and private files, also ensures it's a valid login credential"""

    public_cert_file = input(
        "Enter the name of your public certificate file: ")
    private_key_file = input("Enter the name of your private key file: ")
    print(
        "Certificate authentication with " +
        f"public certificate file '{public_cert_file}' and private key file '{private_key_file}'")
    confirmation = input(
        "Is this information correct? Also confirm if the files are in this folder (yes/no): ")

    if confirmation.lower() == "yes":
        print("Attempting authentication...")
        try:
            AnaplanAuth('certificate', public_cert_file,
                        private_key_file).get_token()
            print('Successfully validated with Anaplan')
            set_key('creds.env', "pub_cert", public_cert_file)
            set_key('creds.env', "priv_key", private_key_file)
            print('Credentials saved in local file!')
        except:
            print('Invalid, please try again')
    else:
        certificate_authentication()


def oauth_authentication():
    """Simple function to load an env file with oauth refresh token, also ensures it's a valid login credential"""

    client_id = input("Enter your client ID: ")
    print(
        f"OAuth authentication with client ID '{client_id}'")
    confirmation = input("Is this information correct? (yes/no): ")

    if confirmation.lower() == "yes":
        print("Attempting authentication...")
        try:
            oauth_device_firstrun(client_id, 'creds.env')
            AnaplanAuth('oauth_refresh', 'creds.env').get_token()
            print('Credentials saved in local file!')
        except:
            print('Invalid, please try again')
    else:
        oauth_authentication()


def main():
    """Trigger a user run"""
    print("Choose an authentication method:")
    print("1. Basic Authentication")
    print("2. Certificate Authentication")
    print("3. OAuth Device Code Authentication")

    choice = input("Enter your choice (1/2/3): ")

    if choice == "1":
        basic_authentication()
    elif choice == "2":
        certificate_authentication()
    elif choice == "3":
        oauth_authentication()
    else:
        print("Invalid choice. Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()
