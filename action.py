#!/usr/bin/env python3

import subprocess
import sys
from configargparse import ArgParser
import dataclasses
from dataclasses import dataclass
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from towndex_etl.cli.cli import cli
from towndex_etl.cli.input_format import InputFormat
from towndex_etl.cli.output_format import OutputFormat
from towndex_etl.extractors.extractor import Extractor


class Action:
    @dataclass(frozen=True)
    class Inputs:
        input: str
        output: str
        configuration: str = ""
        debug: str = ""
        dev: bool = False

        @classmethod
        def from_args(cls):
            argument_parser = ArgParser()
            argument_parser.add_argument(
                "-c", is_config_file=True, help="path to a file to read arguments from"
            )
            for field in dataclasses.fields(cls):
                if field.name == "dev":
                    continue
                argument_parser.add_argument(
                    "--" + field.name.replace("_", "-"),
                    env_var="INPUT_" + field.name.upper(),
                    required=field.default == dataclasses.MISSING,
                )
                field.default
            # The dev argument can only be supplied manually from the command line.
            argument_parser.add_argument("--dev", action="store_true")
            args = argument_parser.parse_args()
            kwds = {
                key: value
                for key, value in vars(args).items()
                if isinstance(value, str) and value.strip()
            }
            if args.dev:
                kwds["dev"] = True
            for ignore_key in ("c",):
                kwds.pop(ignore_key, None)
            return cls(**kwds)

        def __post_init__(self):
            for field in dataclasses.fields(self):
                if field.name in (
                    "configuration",
                    "debug",
                    "dev",
                ):
                    continue
                value = getattr(self, field.name)
                if not value.strip():
                    raise ValueError("empty/blank " + field.name)

    def __init__(self, *, inputs: Inputs, temp_directory_path: Path):
        self.__inputs = inputs
        if self.__inputs.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__logger.debug("inputs: %s", self.__inputs)
        self.__temp_directory_path = temp_directory_path

    @classmethod
    def main(cls, inputs: Optional[Inputs] = None):
        if inputs is None:
            inputs = cls.Inputs.from_args()
        with TemporaryDirectory() as temp_dir:
            cls(inputs=inputs, temp_directory_path=Path(temp_dir)).__main()

    def __build_gui(
        self,
        *,
        configuration_file_path: Optional[Path],
        gui_directory_path: Path,
        input_directory_path: Path,
        output_directory_path: Path
    ):
        data_file_path = self.__temp_directory_path / "data.json"

        cli(
            input=str(input_directory_path.resolve()),
            input_format=InputFormat.JSON_DIRECTORY,
            output=data_file_path,
            output_format=OutputFormat.JSON_FILE,
        )

        subprocess_env = os.environ.copy()
        if configuration_file_path is not None:
            subprocess_env["CONFIGURATION_FILE_PATH"] = str(
                configuration_file_path.resolve()
            )
        subprocess_env["DATA_FILE_PATH"] = str(data_file_path.resolve())
        subprocess_env["EDITOR"] = ""
        subprocess_env["OUTPUT_DIRECTORY_PATH"] = str(output_directory_path.resolve())
        self.__logger.info("subprocess environment variables: %s", subprocess_env)

        args = ["yarn", "build"]

        shell = sys.platform == "win32"
        if shell and sys.platform != "win32":
            args = " ".join(args)

        self.__logger.info("running %s", args)
        try:
            subprocess.run(
                args,
                check=True,
                cwd=str(gui_directory_path),
                env=subprocess_env,
                shell=shell,
            )
            self.__logger.info("completed %s", args)
        except subprocess.TimeoutExpired:
            self.__logger.warning("timed out on %s", args)

        self.__logger.info("built GUI to %s", output_directory_path)

    def __main(self):
        gui_directory_path = None
        for check_gui_directory_path in (
            Path(__file__).parent.parent / "gui",
            Path("/towndex/gui"),
        ):
            if check_gui_directory_path.is_dir():
                gui_directory_path = check_gui_directory_path
                break

        if gui_directory_path is None:
            raise RuntimeError("unable to locate towndex gui directory")

        self.__build_gui(
            configuration_file_path=Path(self.__inputs.configuration)
            if self.__inputs.configuration
            else None,
            gui_directory_path=gui_directory_path,
            input_directory_path=Path(self.__inputs.input),
            output_directory_path=Path(self.__inputs.output),
        )


if __name__ == "__main__":
    Action.main()
