#!/usr/bin/python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import smtplib
import ssl
from typing import Any, Dict, List, Optional

from click.core import Context

try:
    import jinja2
except ModuleNotFoundError:
    exit("Jinja2 is a required dependency for this script")
try:
    import click
except ModuleNotFoundError:
    exit("Click is a required dependency for this script")


SMTP_PORT = 587
SMTP_SERVER = "mail-relay.apache.org"
PROJECT_NAME = "Superset"
PROJECT_MODULE = "superset"
PROJECT_DESCRIPTION = "Apache Superset is a modern, enterprise-ready business intelligence web application"


def string_comma_to_list(message: str) -> List[str]:
    if not message:
        return []
    return [element.strip() for element in message.split(",")]


def send_email(
    smtp_server: str,
    smpt_port: int,
    username: str,
    password: str,
    sender_email: str,
    receiver_email: str,
    message: str,
) -> None:
    """
    Send a simple text email (SMTP)
    """
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, smpt_port) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.sendmail(sender_email, receiver_email, message)


def render_template(template_file: str, **kwargs: Any) -> str:
    """
    Simple render template based on named parameters

    :param template_file: The template file location
    :kwargs: Named parameters to use when rendering the template
    :return: Rendered template
    """
    template = jinja2.Template(open(template_file).read())
    return template.render(kwargs)


def inter_send_email(
    username: str, password: str, sender_email: str, receiver_email: str, message: str
) -> None:
    print("--------------------------")
    print("SMTP Message")
    print("--------------------------")
    print(message)
    print("--------------------------")
    confirm = input("Is the Email message ok? (yes/no): ")
    if confirm not in ("Yes", "yes", "y"):
        exit("Exit by user request")

    try:
        send_email(
            SMTP_SERVER,
            SMTP_PORT,
            username,
            password,
            sender_email,
            receiver_email,
            message,
        )
        print("Email sent successfully")
    except smtplib.SMTPAuthenticationError:
        exit("SMTP User authentication error, Email not sent!")
    except Exception as e:
        exit(f"SMTP exception {e}")


class BaseParameters(object):
    def __init__(
        self,
        email: str,
        username: str,
        password: str,
        version: str,
        version_rc: str,
    ) -> None:
        self.email = email
        self.username = username
        self.password = password
        self.version = version
        self.version_rc = version_rc
        self.template_arguments: Dict[str, Any] = {}

    def __repr__(self) -> str:
        return f"Apache Credentials: {self.email}/{self.username}/{self.version}/{self.version_rc}"


@click.group()
@click.pass_context
@click.option(
    "--apache_email",
    prompt="Apache Email",
    help="Your Apache email this will be used for SMTP From",
)
@click.option(
    "--apache_username", prompt="Apache username", help="Your LDAP Apache username"
)
@click.option(
    "--apache_password",
    prompt="Apache password",
    hide_input=True,
    help="Your LDAP Apache password",
)
@click.option("--version", envvar="SUPERSET_VERSION")
@click.option("--version_rc", envvar="SUPERSET_VERSION_RC")
def cli(
    ctx: Context,
    apache_email: str,
    apache_username: str,
    apache_password: str,
    version: str,
    version_rc: str,
) -> None:
    """Welcome to releasing send email CLI interface!"""
    base_parameters = BaseParameters(
        apache_email, apache_username, apache_password, version, version_rc
    )
    base_parameters.template_arguments["project_name"] = PROJECT_NAME
    base_parameters.template_arguments["project_module"] = PROJECT_MODULE
    base_parameters.template_arguments["project_description"] = PROJECT_DESCRIPTION
    base_parameters.template_arguments["version"] = base_parameters.version
    base_parameters.template_arguments["version_rc"] = base_parameters.version_rc
    base_parameters.template_arguments["sender_email"] = base_parameters.email
    ctx.obj = base_parameters


@cli.command("vote_pmc")
@click.option(
    "--receiver_email",
    default="dev@superset.apache.org",
    type=str,
    prompt="The receiver email (To:)",
)
@click.pass_obj
def vote_pmc(base_parameters: BaseParameters, receiver_email: str) -> None:
    template_file = "email_templates/vote_pmc.j2"
    base_parameters.template_arguments["receiver_email"] = receiver_email
    message = render_template(template_file, **base_parameters.template_arguments)
    inter_send_email(
        base_parameters.username,
        base_parameters.password,
        base_parameters.template_arguments["sender_email"],
        base_parameters.template_arguments["receiver_email"],
        message,
    )


@cli.command("result_pmc")
@click.option(
    "--receiver_email",
    default="dev@superset.apache.org",
    type=str,
    prompt="The receiver email (To:)",
)
@click.option(
    "--vote_bindings",
    default="",
    type=str,
    prompt="A List of people with +1 binding vote (ex: Max,Grace,Krist)",
)
@click.option(
    "--vote_nonbindings",
    default="",
    type=str,
    prompt="A List of people with +1 non binding vote (ex: Ville)",
)
@click.option(
    "--vote_negatives",
    default="",
    type=str,
    prompt="A List of people with -1 vote (ex: John)",
)
@click.option(
    "--vote_thread",
    default="",
    type=str,
    prompt="Permalink to the vote thread "
    "(see https://lists.apache.org/list.html?dev@superset.apache.org)",
)
@click.pass_obj
def result_pmc(
    base_parameters: BaseParameters,
    receiver_email: str,
    vote_bindings: str,
    vote_nonbindings: str,
    vote_negatives: str,
    vote_thread: str,
) -> None:
    template_file = "email_templates/result_pmc.j2"
    base_parameters.template_arguments["receiver_email"] = receiver_email
    base_parameters.template_arguments["vote_bindings"] = string_comma_to_list(
        vote_bindings
    )
    base_parameters.template_arguments["vote_nonbindings"] = string_comma_to_list(
        vote_nonbindings
    )
    base_parameters.template_arguments["vote_negatives"] = string_comma_to_list(
        vote_negatives
    )
    base_parameters.template_arguments["vote_thread"] = vote_thread
    message = render_template(template_file, **base_parameters.template_arguments)
    inter_send_email(
        base_parameters.username,
        base_parameters.password,
        base_parameters.template_arguments["sender_email"],
        base_parameters.template_arguments["receiver_email"],
        message,
    )


@cli.command("announce")
@click.option(
    "--receiver_email",
    default="dev@superset.apache.org",
    type=str,
    prompt="The receiver email (To:)",
)
@click.pass_obj
def announce(base_parameters: BaseParameters, receiver_email: str) -> None:
    template_file = "email_templates/announce.j2"
    base_parameters.template_arguments["receiver_email"] = receiver_email
    message = render_template(template_file, **base_parameters.template_arguments)
    inter_send_email(
        base_parameters.username,
        base_parameters.password,
        base_parameters.template_arguments["sender_email"],
        base_parameters.template_arguments["receiver_email"],
        message,
    )


cli()
