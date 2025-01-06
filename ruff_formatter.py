# Built-in imports
from subprocess import run


def main() -> None:
    run(['ruff', 'format'])


if __name__ == '__main__':
    main()
