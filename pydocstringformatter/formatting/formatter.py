import re
import tokenize

from pydocstringformatter.formatting.base import StringFormatter


class BeginningQuotesFormatter(StringFormatter):
    """Fix the position of the opening quotes."""

    name = "beginning-quotes"

    def _treat_string(self, tokeninfo: tokenize.TokenInfo, _: int) -> str:
        new_string = tokeninfo.string
        if new_string[3] == "\n":
            new_string = re.sub(r"\n *", "", new_string, 1)
        return new_string


class CapitalizeFirstLetterFormatter(StringFormatter):
    """Capitalize the first letter of the docstring if appropriate."""

    name = "capitalize-first-letter"
    first_letter_re = re.compile(r"""['"]{3}\s*(\w)""")

    def _treat_string(self, tokeninfo: tokenize.TokenInfo, _: int) -> str:
        new_string = None
        if match := self.first_letter_re.match(tokeninfo.string):
            first_letter = match.end() - 1
            new_string = (
                tokeninfo.string[:first_letter]
                + tokeninfo.string[first_letter].upper()
                + tokeninfo.string[first_letter + 1 :]
            )
        return new_string or tokeninfo.string


class ClosingQuotesFormatter(StringFormatter):
    """Fix the position of the closing quotes."""

    name = "closing-quotes"

    def _treat_string(self, tokeninfo: tokenize.TokenInfo, _: int) -> str:
        """Fix the position of end quotes for multi-line docstrings."""
        new_string = tokeninfo.string
        if "\n" not in new_string:
            # Not a multiline docstring, nothing to do
            return new_string
        good_end = f"{(tokeninfo.start[1]) * ' '}{(new_string[0]) * 3}"
        split_string = new_string.split("\n")

        # Add new line with only quotes
        if not new_string.endswith("\n" + good_end):
            new_string = new_string[:-3] + "\n" + good_end
        # Remove line with only quotes for potential single line string
        elif len(split_string) == 2 and split_string[-1] == good_end:
            new_string = "\n".join(split_string[:-1]) + tokeninfo.string[0] * 3
        return new_string


class FinalPeriodFormatter(StringFormatter):
    """Add a period to the end of single line docstrings and summaries."""

    name = "final-period"

    def _treat_string(self, tokeninfo: tokenize.TokenInfo, _: int) -> str:
        """Add a period to the end of single-line docstrings and summaries."""
        # Handle single line docstrings
        if not tokeninfo.string.count("\n"):
            if tokeninfo.string[-4] != ".":
                return tokeninfo.string[:-3] + "." + tokeninfo.string[-3:]
        # Handle multi-line docstrings
        else:
            lines = tokeninfo.string.splitlines()
            # If second line is one recurring character we're dealing with a rst title
            if (stripped := lines[1].lstrip()) and stripped.count(stripped[0]) == len(
                stripped
            ):
                return tokeninfo.string
            # If second line is empty we're dealing with a summary
            if lines[1] == "":
                if lines[0][-1] != ".":
                    return lines[0] + ".\n" + "\n".join(lines[1:])
            # TODO(#26): Handle multi-line docstrings that do not have a summary
            # This is obviously dependent on whether 'pydocstringformatter' will
            # start enforcing summaries :)
        return tokeninfo.string


class SplitSummaryAndDocstringFormatter(StringFormatter):
    """Split the summary and body of a docstring based on a period in between them.

    This formatter is currently optional as its considered somwehat opinionated
    and might require major refactoring for existing projects.
    """

    name = "split-summary-body"
    optional = True

    def _treat_string(self, tokeninfo: tokenize.TokenInfo, indent_length: int) -> str:
        """Split a summary and body if there is a period after the summary."""
        if index := tokeninfo.string.find("."):
            if (
                index not in (-1, len(tokeninfo.string) - 4)
                and "\n" not in tokeninfo.string[:index]  # Skip multi-line summaries
            ):
                # Handle summary with part of docstring body on same line
                if tokeninfo.string[index + 1] == " ":
                    return (
                        tokeninfo.string[:index]
                        + f".\n\n{' ' * indent_length}"
                        + tokeninfo.string[index + 2 :]
                    )

                # Handle summary with part of docstring body on same line
                if (
                    tokeninfo.string[index + 1] == "\n"
                    and tokeninfo.string[index + 2] != "\n"
                ):
                    return (
                        tokeninfo.string[:index]
                        + ".\n\n"
                        + tokeninfo.string[index + 2 :]
                    )
        return tokeninfo.string


class StripWhitespacesFormatter(StringFormatter):
    """Strip 1) docstring start, 2) docstring end and 3) end of line."""

    name = "strip-whitespaces"

    def _treat_string(self, tokeninfo: tokenize.TokenInfo, indent_length: int) -> str:
        """Strip whitespaces."""
        quotes, lines = tokeninfo.string[:3], tokeninfo.string[3:-3].split("\n")
        for index, line in enumerate(lines):
            if index == 0:  # pylint: disable=compare-to-zero
                lines[index] = line.lstrip().rstrip()
            elif index == len(lines) - 1:
                # Remove whitespaces if last line is completely empty
                if len(line) > indent_length and line.count(" ") == len(line):
                    lines[index] = ""
            else:
                lines[index] = line.rstrip()

        return quotes + "\n".join(lines) + quotes
