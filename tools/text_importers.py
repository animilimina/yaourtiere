import yaml


def read_text(path: str) -> str:
    with open(path, 'r') as file:
        output = file.read().rstrip()
    return output


def read_yaml(path: str) -> dict:
    with open(path, 'r') as yaml_stream:
        output = yaml.safe_load(yaml_stream)
    return output
