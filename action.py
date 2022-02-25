#!/usr/bin/env python3

from configargparse import ArgParser
import dataclasses
from dataclasses import dataclass
from typing import Optional
from towndex_cli.main import main as cli


class Action:
    @dataclass(frozen=True)
    class Inputs:
        input: str
        output: str
        cache: str = ""
        configuration: str = ""
        debug: str = ""

        @classmethod
        def from_args(cls):
            argument_parser = ArgParser()
            for field in dataclasses.fields(cls):
                argument_parser.add_argument(
                    "--" + field.name.replace("_", "-"),
                    env_var="INPUT_" + field.name.upper(),
                    required=field.default == dataclasses.MISSING,
                )
                field.default
            args = argument_parser.parse_args()
            kwds = {
                key: value
                for key, value in vars(args).items()
                if isinstance(value, str) and value.strip()
            }
            return cls(**kwds)

        def __post_init__(self):
            for field in dataclasses.fields(self):
                if field.name in (
                    "cache",
                    "configuration",
                    "debug",
                ):
                    continue
                value = getattr(self, field.name)
                if not value.strip():
                    raise ValueError("empty/blank " + field.name)

    @classmethod
    def main(cls, inputs: Optional[Inputs] = None):
        if inputs is None:
            inputs = cls.Inputs.from_args()

        cli_args = ["gui"]
        if inputs.cache:
            cli_args.extend(("--cache", inputs.cache))
        if inputs.configuration:
            cli_args.extend(("--configuration", inputs.configuration))
        if inputs.debug:
            cli_args.append("--debug")
        cli_args.extend(("--input", inputs.input))
        cli_args.extend(("--output", inputs.output))

        cli(cli_args)


if __name__ == "__main__":
    Action.main()
