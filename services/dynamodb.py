import boto3
from boto3.dynamodb.conditions import Key
from config import config


class DynamodbManager:
    def __init__(self):
        self.__session = boto3.Session(
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region_name
        )
        self._table = self.__session.resource('dynamodb').Table(config.dynamodb_table)


class DynamodbItem(DynamodbManager):
    def __init__(self, item_type: str, item_id: int, get: bool = True):
        DynamodbManager.__init__(self)
        self.__item_key = {
            "item_type": item_type,
            "item_id": item_id
        }
        if get:
            self._item = self.__get_item()

    def __get_item(self) -> dict:
        response = self._table.get_item(Key=self.__item_key)
        if "Item" in response.keys():
            output = response["Item"]
        else:
            output = self.__item_key
            self._table.put_item(Item=self.__item_key)
        return output

    def _update_item(self) -> None:
        self._table.put_item(Item=self._item)
        return

    def increase_counter(self, counter: str):
        self._table.update_item(Key=self.__item_key,
                                AttributeUpdates={
                                    counter: {
                                        "Value": 1,
                                        "Action": "ADD"
                                    }
                                })


class DynamodbExtractor(DynamodbManager):
    def __init__(self, item_type: str, item_id_min: int = None, item_id_max: int = None):
        DynamodbManager.__init__(self)
        self.__item_type = item_type
        self.__item_id_min = item_id_min
        self.__item_id_max = item_id_max if item_id_max else self.__item_id_min
        self.extraction = self.__extract_items()

    def __extract_items(self):
        if self.__item_id_min:
            response = self._table.query(KeyConditionExpression=
                                         Key('item_type').eq(self.__item_type) &
                                         Key('item_id').between(self.__item_id_min, self.__item_id_max)
                                         )
        else:
            response = self._table.query(KeyConditionExpression=Key('item_type').eq(self.__item_type))
        return response['Items']
