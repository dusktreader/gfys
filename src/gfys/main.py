import re
import subprocess
import sys
from typing import Annotated

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


def should_print_line(line: str | None):
    if line is None:
        return False

    if '(cached)' not in line and '[no tests to run]' in line:
        return False

    if '[no test files]' in line:
        return False

    if 'testing: warning: no tests to run' in line:
        return False

    if re.match(r'===\s+(RUN|PAUSE|CONT)\s+', line):
        return False

    if line.strip() == 'PASS':
        return False

    if line.strip() == 'FAIL':
        return False

    return True


def print_line(line: str):
    line = line.rstrip()
    line = re.sub(r'^---\s+(PASS|FAIL):', r'\1:', line)

    if re.match(r'(PASS|FAIL):\s+\w+', line):
        line = re.sub(r'\s+\(\d+\.\d+s\)\s*$', '', line)

    if line.startswith("ok"):
        line = line.replace("ok", "[green]ok[/green]", 1)

    if 'PASS' in line:
        line = line.replace('PASS', '[green]PASS[/green]')

    if 'FAIL' in line:
        line = line.replace('FAIL', '[red]FAIL[/red]')

    console.print(line, markup=True, highlight=False)


def filter_output(lines: list[str]):
    for line in lines:
        if should_print_line(line):
            print_line(line)


@app.command()
def main(
    packages: Annotated[str, typer.Argument(help="Package pattern to test (default: ./...)")] = "./...",
    run: Annotated[str | None, typer.Option(help="Run only tests matching pattern")] = None,
    verbose: Annotated[bool, typer.Option("-v", "--verbose", help="Verbose output")] = False,
    cache: Annotated[bool, typer.Option(help="Use cache if available")] = False,
    tags: Annotated[list[str] | None, typer.Option(help="Use tags")] = None,
):
    """
    Run go test with filtered and colorized output.
    """
    cmd = ["go", "test"]

    if verbose:
        cmd.append("-v")

    if not cache:
        cmd.append("-count=1")

    if run:
        cmd.extend(["-run", run])

    if tags:
        cmd.extend(["-tags", " ".join(tags)])

    cmd.append(packages)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        output_lines = result.stdout.splitlines(keepends=True)
        filter_output(output_lines)

        if result.stderr:
            console.print(result.stderr, style="red")

        sys.exit(result.returncode)

    except KeyboardInterrupt:
        console.print("\nTest interrupted", style="yellow")
        sys.exit(130)

    except Exception as e:
        console.print(f"Error running tests: {e}", style="red", markup=False)
        sys.exit(1)


if __name__ == '__main__':
    app()
