import json
from aws_mfa_creds.helper import helper
from aws_mfa_creds.mfa_creds import *


def main():
    """Console script for aws_mfa_creds."""
    options = helper()
    aws_profile_arn = get_aws_profile_arn(options.config_file)
    if options.refresh:
        auto_refresh_credentials(aws_profile_arn)
        sys.exit(0)

    selected_aws_profile, role_arn = choose_profile_option(aws_profile_arn)
    session_name, credentials = get_credentials_for_role(selected_aws_profile, role_arn)

    if options.output == 'write':
        write_credentials(session_name, credentials)
    elif options.output == 'json':
        print(json.dumps({'AWS_ACCESS_KEY_ID': credentials['AccessKeyId'],
                          'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
                          'AWS_SESSION_TOKEN': credentials['SessionToken']}))
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
