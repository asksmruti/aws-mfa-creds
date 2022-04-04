import os
import sys
import boto3
import logging
import configparser
from botocore.exceptions import ClientError

# Setting up logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s'
                    )
logger = logging.getLogger('aws-mfa')


def get_aws_profile_arn(aws_config_file_path) -> dict:
    """
    :Description: To extract the profile name and corresponding role_arn
    from aws config file and return a dict
    :param aws_config_file_path: Path to the aws config file
    :return: A dict of profile's name and role_arn
    """
    profile_role_arn_dict = {}
    filename = os.path.expanduser(aws_config_file_path)

    if not os.path.exists(filename):
        logger.error(f"ERROR: {aws_config_file_path} file does not exist.")
        sys.exit(1)
    else:
        config = configparser.ConfigParser()
        config.read(filename)
        aws_profiles: list[str] = config.sections()

        if len(aws_profiles) == 0:
            logger.error(f"ERROR: {aws_config_file_path} file is empty.")
            sys.exit(1)

        for profile in aws_profiles:
            try:
                # profile_role_arn_dict[profile.split()[-1]] = config.get(profile, "role_arn")
                profile_role_arn_dict[profile.split()[-1]] = config.get(profile, "role_arn")
            except configparser.NoOptionError:
                pass

    return profile_role_arn_dict


def choose_profile_option(profile_role_arn_dict: dict):
    """
    Description: To provide choice to user to select the profile from aws config
    and return a profile and corresponding arn
    :param profile_role_arn_dict: A dictionary of profile and role_arns
    :return: profile_name and role_arn
    """
    aws_profiles_list = []
    if profile_role_arn_dict:
        print("\nPlease choose from the following profile(s) : \n")
    else:
        logger.error("Config file has no role_arn")
        sys.exit(1)
    for k, v in profile_role_arn_dict.items():
        print(f"{list(profile_role_arn_dict).index(k) + 1})  {k}")
        aws_profiles_list.append(k)

    i = input("\n Enter profile id: ")

    if 0 < int(i) <= len(profile_role_arn_dict):
        profile_name = aws_profiles_list[int(i) - 1]
        role_arn = profile_role_arn_dict[profile_name]
    else:
        logger.error("Please select correct profile id")
        sys.exit(1)

    return profile_name.split()[-1], role_arn


def refresh_credentials(session_name, role_arn):
    """
    Description: Refresh aws credentials
    :param session_name: Temporary AWS session name
    :param role_arn: ARN of aws role
    :return: AWS temporary credentials
    """
    try:
        session = boto3.Session(profile_name=session_name)
        sts = session.client('sts')
        response = sts.assume_role(RoleArn=role_arn,
                                   RoleSessionName=session_name,
                                   DurationSeconds=3600
                                   )
        return session_name, response['Credentials']
    except:
        logger.debug("Existing credentials expired")
        return session_name, {}


def get_credentials_for_role(selected_aws_profile, role_arn):
    """
    Description: Generate sts credentials for corresponding role
    :param selected_aws_profile: aws_profile name
    :param role_arn: role_arn
    :return: temporary session name and credentials object
    """
    boto3.set_stream_logger('botocore', logging.CRITICAL)
    session_name = f"temp_{selected_aws_profile}"
    session_name, credentials = refresh_credentials(session_name, role_arn)

    # To generate the new credentials
    if not credentials:
        try:
            session = boto3.Session(profile_name=selected_aws_profile)
            sts = session.client('sts')
            response = sts.assume_role(RoleArn=role_arn,
                                       RoleSessionName=session_name,
                                       DurationSeconds=3600
                                       )
            return session_name, response['Credentials']
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            sys.exit(1)
    else:
        return session_name, credentials


def write_credentials(profile, credentials):
    """
    :param profile: Temporary session profile name
    :param credentials: sts crdential object
    :return: Write temporary credentials into ~/.aws/credentials file
    """
    filename = os.path.expanduser('~/.aws/credentials')
    dirname = os.path.dirname(filename)

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    config = configparser.ConfigParser()
    config.read(filename)
    if not config.has_section(profile):
        config.add_section(profile)
    config.set(profile, 'aws_access_key_id', credentials['AccessKeyId'])
    config.set(profile, 'aws_secret_access_key', credentials['SecretAccessKey'])
    config.set(profile, 'aws_session_token', credentials['SessionToken'])
    try:
        with open(filename, 'w') as fp:
            config.write(fp)
        logger.info(f"Set your profile to {profile}, export AWS_PROFILE={profile} \n")
    except IOError:
        logger.error(f"Unable to write into {filename}")


def auto_refresh_credentials(profile_role_dict):
    """
    :param profile_role_dict: dictionary of profile name and role ARN
    :return: Automatically refresh credentials and write to AWS credentials file
    """
    for profile, role_arn in profile_role_dict.items():
        session_name, credentials = refresh_credentials(f"temp_{profile}", role_arn)
        if session_name and credentials:
            write_credentials(session_name, credentials)
