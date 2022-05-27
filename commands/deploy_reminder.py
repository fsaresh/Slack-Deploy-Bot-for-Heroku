from datetime import datetime, timedelta
from dateutil.parser import parse
from enum import Enum
from helpers.command_helpers import parse_argument, HUMAN_TIMESTAMP_FORMAT, SlackHerokuDeployError
from slack_bolt import Say
from slack_sdk import WebClient
from typing import Dict
import logging

LOG = logging.getLogger(__name__)
MAX_REMINDER_MINUTES = 3 * 24 * 60  # 3 days


class DeployReminderError(SlackHerokuDeployError):
    pass


class DeployVerbs(Enum):
    AT = 'at'
    IN = 'in'


class ScheduledTime:
    def __init__(self, scheduled_time: datetime):
        self.scheduled_time = scheduled_time.replace(second=0, microsecond=0)

    @property
    def minutes_til_deploy(self) -> int:
        time_diff = self.scheduled_time - datetime.now().replace(second=0, microsecond=0)
        return int(time_diff.seconds / 60)

    @property
    def human_timestamp(self) -> str:
        return self.scheduled_time.strftime(HUMAN_TIMESTAMP_FORMAT)


class DeployReminder:
    def __init__(self, say: Say, command: Dict, web_client: WebClient):
        self.say = say
        self.command = command
        self.command_text = self.command['text']
        self.web_client = web_client

    def schedule_reminder(self):
        """ Schedule a reminder for the specified number of minutes_to_add (first argument) from now,
        notifying anyone/any team tagged (optional second parameter)
        """
        if self.use_legacy_minutes_to_add():
            verb = DeployVerbs.IN
            time_specified = parse_argument(self.command_text, arg_index=0)
            initial_recipient = parse_argument(self.command_text, arg_index=1)
        else:
            verb = DeployVerbs(parse_argument(self.command_text, arg_index=0).lower())
            time_specified = parse_argument(self.command_text, arg_index=1)
            initial_recipient = parse_argument(self.command_text, arg_index=2)

        schedule = self.get_schedule_based_on_verb(verb=verb, time_specified=time_specified)

        preamble = ''
        if initial_recipient:
            preamble = f'{initial_recipient}: '
        # TODO: Make timezone aware/compatible instead of hard-coding to Pacific time
        command_issuer = f"<@{self.command['user_id']}>"
        self.say(f"{preamble}Deployment reminder scheduled by {command_issuer} "
                 f"in {schedule.minutes_til_deploy} minute(s) "
                 f"at {schedule.human_timestamp} Pacific")

        result = self.web_client.chat_scheduleMessage(
            channel=self.command['channel_id'],
            text=f"<@{self.command['user_id']}> TIME TO DEPLOY",
            post_at=schedule.scheduled_time.strftime('%s')
        )
        LOG.info(result)

    def get_schedule_based_on_verb(self, verb, time_specified):
        if verb is DeployVerbs.IN:
            schedule = get_scheduled_time_in_minutes(raw_minutes_to_add=time_specified)
        elif verb is DeployVerbs.AT:
            schedule = get_scheduled_time_at_timestamp(timestamp=time_specified)
        else:
            raise DeployReminderError(f"Unable to schedule deploy, invalid verb provided")
        if not schedule:
            raise DeployReminderError(f'Unable to schedule message for command text: {self.command_text}')
        return schedule

    def use_legacy_minutes_to_add(self) -> bool:
        try:
            int(parse_argument(self.command_text, arg_index=0))
            return True
        except ValueError:
            return False


def get_scheduled_time_at_timestamp(timestamp) -> ScheduledTime:
    parsed_time = parse(timestamp)
    if parsed_time < datetime.now():
        raise DeployReminderError(get_reminder_in_past_message())

    scheduled_time = ScheduledTime(parsed_time)
    if scheduled_time.minutes_til_deploy > MAX_REMINDER_MINUTES:
        raise DeployReminderError(get_reminder_too_far_ahead_message())

    return scheduled_time


def get_scheduled_time_in_minutes(raw_minutes_to_add: str) -> ScheduledTime:
    minutes_to_add = int(raw_minutes_to_add)
    if minutes_to_add < 1:
        raise DeployReminderError(get_reminder_in_past_message())
    elif minutes_to_add > MAX_REMINDER_MINUTES:
        raise DeployReminderError(get_reminder_too_far_ahead_message())

    scheduled_time = datetime.now() + timedelta(minutes=minutes_to_add)
    return ScheduledTime(scheduled_time)


def get_reminder_in_past_message() -> str:
    return f'Cannot set reminders in the past'


def get_reminder_too_far_ahead_message() -> str:
    return f'Cannot set reminders for over {MAX_REMINDER_MINUTES} minutes ' \
           f'({int(MAX_REMINDER_MINUTES / 60)} hours) from now'


def get_deploy_reminder_help_message(command: Dict, exception: Exception) -> str:
    return f"Unable to schedule deployment reminder with parameters: `{command['text']}`, example usages:\n"\
           f"`/deploy-reminder in 30 @task-automation-devs`\n"\
           f"`/deploy-reminder`at 12:34\n`"\
           f"Error: {exception}"
