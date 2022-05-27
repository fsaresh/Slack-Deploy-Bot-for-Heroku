import datetime
from typing import Optional, Union
from unittest import TestCase
from unittest.mock import MagicMock

from slack_bolt import Say
from slack_sdk import WebClient

from commands.deploy_reminder import DeployReminder, DeployReminderError, DeployVerbs, MAX_REMINDER_MINUTES
from helpers.command_helpers import HUMAN_TIMESTAMP_FORMAT

mock_say = MagicMock(Say)
mock_client = MagicMock(WebClient)

BUFFER_TIME = 5


def generate_command_text(verb: DeployVerbs, time: Union[int, str], recipient: Optional[str] = None):
    return {
        'text': f'{verb.value} {time} {recipient}',
        'user_id': None,
        'channel_id': None,
    }


def generate_timestamp(minutes_from_now: int):
    timestamp = datetime.datetime.now() + datetime.timedelta(minutes=minutes_from_now)
    return timestamp.strftime(HUMAN_TIMESTAMP_FORMAT)

# @patch.object(DeployReminder, 'get_scheduled_time_in_minutes')
# @patch.object(DeployReminder, 'get_scheduled_time_at_timestamp')


class TestDeployReminder(TestCase):
    def setUp(self) -> None:
        mock_say.reset_mock()
        mock_client.reset_mock()

    def test_invalid_verb(self):
        command = {'text': 'invalid 30'}
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        with self.assertRaises(ValueError):
            deploy_reminder.schedule_reminder()

    def test_no_verb_legacy_minutes_to_add(self):
        command = {'text': '30', 'channel_id': None, 'user_id': None}
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        deploy_reminder.schedule_reminder()
        mock_client.chat_scheduleMessage.assert_called_once()

    def test_in_verb_negative_time(self):
        command = generate_command_text(DeployVerbs.IN, -BUFFER_TIME)
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        with self.assertRaises(DeployReminderError):
            deploy_reminder.schedule_reminder()

    def test_in_verb_beyond_max_time(self):
        command = generate_command_text(DeployVerbs.IN, MAX_REMINDER_MINUTES+BUFFER_TIME)
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        with self.assertRaises(DeployReminderError):
            deploy_reminder.schedule_reminder()

    def test_in_verb_valid_time(self):
        command = generate_command_text(DeployVerbs.IN, BUFFER_TIME)
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        deploy_reminder.schedule_reminder()
        mock_client.chat_scheduleMessage.assert_called_once()

    def test_at_verb_negative_time(self):
        command = generate_command_text(DeployVerbs.AT, generate_timestamp(-BUFFER_TIME))
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        with self.assertRaises(DeployReminderError):
            deploy_reminder.schedule_reminder()

    def test_at_verb_beyond_max_time(self):
        command = generate_command_text(DeployVerbs.AT, generate_timestamp(MAX_REMINDER_MINUTES+BUFFER_TIME))
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        deploy_reminder.schedule_reminder()
        mock_client.chat_scheduleMessage.assert_called_once()

    def test_at_verb_valid_time(self):
        command = generate_command_text(DeployVerbs.AT, generate_timestamp(BUFFER_TIME))
        deploy_reminder = DeployReminder(say=mock_say, command=command, web_client=mock_client)
        deploy_reminder.schedule_reminder()
        mock_client.chat_scheduleMessage.assert_called_once()
