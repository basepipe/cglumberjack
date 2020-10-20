import click
import wget
import os

@click.command()
def main():
    url_ = "https://www.uberware.net/get/Windows/Smedge2020.0.msi"
    filename = wget.download(url_, os.path.join(os.path.expanduser("~"), "Downloads"))
    print(filename)


if __name__ == "__main__":
    main()