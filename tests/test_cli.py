"""Unit tests for the CLI entry point, argument parsing, and logging configuration."""

import logging

from laptop_remote.cli import build_parser
from laptop_remote.core.logger import LOGGER_NAME, configure_logging  # type: ignore


class TestCliArguments:
    def test_default_arguments(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.pin is None
        assert args.name is None
        assert args.port == 5000
        assert args.ssl is False
        assert args.tray is False
        assert args.verbose is False
        assert args.quiet is False

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-v"])
        assert args.verbose is True
        assert args.quiet is False

    def test_quiet_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--quiet"])
        assert args.quiet is True
        assert args.verbose is False

    def test_custom_port_and_name(self):
        parser = build_parser()
        args = parser.parse_args(["--port", "8080", "-n", "DeskTop"])
        assert args.port == 8080
        assert args.name == "DeskTop"


class TestConfigureLogging:
    def test_configure_logging_verbose(self):
        configure_logging(verbose=True, quiet=False)
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.DEBUG

    def test_configure_logging_quiet(self):
        configure_logging(verbose=False, quiet=True)
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.WARNING

    def test_configure_logging_default(self):
        configure_logging(verbose=False, quiet=False)
        root_logger = logging.getLogger(LOGGER_NAME)
        assert root_logger.level == logging.INFO
