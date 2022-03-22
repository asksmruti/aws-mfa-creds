import argparse


def helper():
    """
    :return: Arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", required=False,
                        dest="output", help="Output format write or json, default='write'", metavar="STRING",
                        default="write", choices=['json', 'write'])
    parser.add_argument("--config-file", "-t", required=False,
                        dest="config_file", help="AWS config file path, default='~/.aws/config'", metavar="STRING",
                        default="~/.aws/config")
    parser.add_argument("--refresh", "-r", required=False, help="Refresh AWS token before expired for aws profile", default=False, type=bool)

    options = parser.parse_args()
    return options