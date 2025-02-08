import click

@click.command()
@click.option('--name', default='World', help='The name to greet.')
def main(name):
    """Simple command that greets NAME for a total of COUNT times."""
    click.echo(f'Hello, {name}!')

if __name__ == '__main__':
    main()
